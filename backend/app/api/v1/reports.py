from __future__ import annotations

from typing import Optional
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.credits import deduct_credits, get_credit_cost
from app.dependencies import get_current_user
from app.models.user import User
from app.models.report import AnalysisReport, PredictionResult
from app.schemas.report import ReportRequest, ReportResponse
from app.schemas.prediction import PredictionResponse, PredictionPriceRange
from app.services.llm.provider import llm_provider
from app.services.llm.prompts import FUNDAMENTAL_ANALYSIS_PROMPT, SENTIMENT_ANALYSIS_PROMPT
from app.services.market_data.aggregator import market_data

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    req: ReportRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cost = await get_credit_cost("report_generation")
    transaction = await deduct_credits(
        db, user.id, cost,
        description=f"Report: {req.report_type} for {req.symbol or 'macro'}",
        reference_type="report_gen",
    )
    if not transaction:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    model_key = req.llm_model or user.preferred_llm

    # Build prompt based on report type
    if req.report_type == "fundamental" and req.symbol:
        fundamentals = await market_data.get_fundamentals(req.symbol, req.market)
        if not fundamentals:
            raise HTTPException(status_code=404, detail="No fundamental data available")
        prompt = FUNDAMENTAL_ANALYSIS_PROMPT.format(
            symbol=req.symbol, financial_data=fundamentals.model_dump_json()
        )
    elif req.report_type == "sentiment" and req.symbol:
        prompt = SENTIMENT_ANALYSIS_PROMPT.format(
            symbol=req.symbol, content=req.query or f"Latest news about {req.symbol}"
        )
    else:
        prompt = req.query or f"Generate a {req.report_type} analysis report"

    messages = [{"role": "user", "content": prompt}]
    result = await llm_provider.chat(model_key, messages, max_tokens=8192)

    report = AnalysisReport(
        user_id=user.id,
        report_type=req.report_type,
        title=f"{req.report_type.title()} Analysis: {req.symbol or 'Macro'}",
        symbol=req.symbol,
        market=req.market,
        content=result["content"],
        summary=result["content"][:200],
        llm_model=model_key,
        tokens_used=result["total_tokens"],
        credits_cost=cost,
        status="completed",
    )
    db.add(report)
    await db.flush()

    return ReportResponse.model_validate(report)


# Prediction Reports APIs
@router.get("/predictions/list")
async def list_prediction_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    symbol: Optional[str] = Query(None),
    prediction_type: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(PredictionResult).where(PredictionResult.user_id == user.id)
    if symbol:
        query = query.where(PredictionResult.symbol == symbol)
    if prediction_type:
        query = query.where(PredictionResult.prediction_type == prediction_type)
    query = query.order_by(desc(PredictionResult.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    predictions = result.scalars().all()

    return {
        "predictions": [_format_prediction_response(p) for p in predictions],
        "page": page,
        "page_size": page_size,
    }


@router.get("/predictions/{prediction_id}", response_model=PredictionResponse)
async def get_prediction_report(
    prediction_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PredictionResult).where(
            PredictionResult.id == prediction_id,
            PredictionResult.user_id == user.id,
        )
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction report not found")

    return _format_prediction_response(prediction)


def _format_prediction_response(p: PredictionResult) -> PredictionResponse:
    states = p.states or {}
    transition_matrix = p.transition_matrix or {}
    predicted_states = p.predicted_states or {}
    predicted_range = p.predicted_range or {}

    return PredictionResponse(
        id=p.id,
        symbol=p.symbol,
        market=p.market,
        prediction_type=p.prediction_type,
        current_price=float(p.current_price) if p.current_price else 0.0,
        current_state="",
        state_labels=states.get("labels", []),
        transition_matrix=transition_matrix.get("matrix", []),
        predicted_state_probs=predicted_states,
        predicted_range=PredictionPriceRange(
            low=predicted_range.get("low", 0.0),
            mid=predicted_range.get("mid", 0.0),
            high=predicted_range.get("high", 0.0),
        ),
        confidence=float(p.confidence) if p.confidence else 0.0,
        computation_steps=[],
        created_at=p.created_at,
    )


@router.get("/list")
async def list_reports(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    report_type: Optional[str] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(AnalysisReport).where(AnalysisReport.user_id == user.id)
    if report_type:
        query = query.where(AnalysisReport.report_type == report_type)
    query = query.order_by(AnalysisReport.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    reports = result.scalars().all()

    return {
        "reports": [ReportResponse.model_validate(r) for r in reports],
        "page": page,
        "page_size": page_size,
    }


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AnalysisReport).where(
            AnalysisReport.id == report_id,
            AnalysisReport.user_id == user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    return ReportResponse.model_validate(report)
