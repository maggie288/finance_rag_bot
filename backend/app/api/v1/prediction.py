from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.credits import deduct_credits, get_credit_cost
from app.dependencies import get_current_user
from app.models.user import User
from app.models.report import PredictionResult
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.market_data.aggregator import market_data
from app.services.analysis.markov import markov_predictor

router = APIRouter(prefix="/prediction", tags=["prediction"])


@router.post("/markov", response_model=PredictionResponse)
async def markov_prediction(
    req: PredictionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Validate prediction type
    if req.prediction_type not in ("3day", "1week", "1month"):
        raise HTTPException(status_code=400, detail="Invalid prediction type. Use: 3day, 1week, 1month")

    # Check and deduct credits
    cost = await get_credit_cost("markov_prediction")
    transaction = await deduct_credits(
        db, user.id, cost,
        description=f"Markov prediction for {req.symbol} ({req.prediction_type})",
        reference_type="prediction",
    )
    if not transaction:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Get historical prices for prediction
    try:
        outputsize = {"3day": 60, "1week": 120, "1month": 250}.get(req.prediction_type, 120)
        kline = await market_data.get_kline(
            req.symbol, req.market, interval="1day", outputsize=outputsize
        )
        if len(kline) < 30:
            raise HTTPException(status_code=400, detail="Not enough historical data for prediction (need 30+ days)")

        prices = [p.close for p in kline]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch price data: {str(e)}")

    # Run prediction
    result = markov_predictor.predict(prices, req.prediction_type)

    # Save to database
    prediction = PredictionResult(
        user_id=user.id,
        symbol=req.symbol,
        market=req.market,
        prediction_type=req.prediction_type,
        current_price=Decimal(str(result["current_price"])),
        states={"labels": result["state_labels"]},
        transition_matrix={"matrix": result["transition_matrix"]},
        predicted_states=result["predicted_state_probs"],
        predicted_range=result["predicted_range"],
        confidence=Decimal(str(round(result["confidence"], 4))),
        computation_log={"steps": result["computation_steps"]},
    )
    db.add(prediction)
    await db.flush()

    return PredictionResponse(
        id=prediction.id,
        symbol=req.symbol,
        market=req.market,
        prediction_type=req.prediction_type,
        current_price=result["current_price"],
        current_state=result["current_state"],
        state_labels=result["state_labels"],
        transition_matrix=result["transition_matrix"],
        predicted_state_probs=result["predicted_state_probs"],
        predicted_range=result["predicted_range"],
        confidence=result["confidence"],
        computation_steps=result["computation_steps"],
        created_at=prediction.created_at,
    )
