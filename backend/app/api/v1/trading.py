from __future__ import annotations

from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.dependencies import get_current_user, get_db
from app.models.user import User
from app.models.trading import TradingSimulation, Trade
from app.schemas.trading import (
    SimulationStartRequest,
    SimulationResponse,
    SimulationDetailResponse,
    SimulationListResponse,
    TradeResponse,
    AgentInfo,
)
from app.services.trading.engine import trading_engine
from app.core.credits import deduct_credits, get_credit_cost
from app.workers.trading_tasks import run_trading_simulation

router = APIRouter(prefix="/trading", tags=["trading"])


@router.get("/agents", response_model=list[AgentInfo])
async def list_agents():
    """List available AI trading agents"""
    agents = [
        AgentInfo(
            name="deepseek",
            display_name="DeepSeek",
            description="High-performance reasoning model with strong analytical capabilities",
            model_name="deepseek/deepseek-chat",
            available=True,
        ),
        AgentInfo(
            name="minimax",
            display_name="MiniMax",
            description="Chinese LLM optimized for financial analysis",
            model_name="minimax/abab6.5-chat",
            available=True,
        ),
        AgentInfo(
            name="claude",
            display_name="Claude 3.5 Sonnet",
            description="Anthropic's advanced model with excellent reasoning",
            model_name="claude-3-5-sonnet-20241022",
            available=True,
        ),
        AgentInfo(
            name="openai",
            display_name="GPT-4o",
            description="OpenAI's flagship model for complex tasks",
            model_name="gpt-4o",
            available=True,
        ),
    ]
    return agents


@router.post("/simulations", response_model=SimulationResponse)
async def create_simulation(
    req: SimulationStartRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new AI trading simulation (pending status, needs manual start)"""
    # Deduct credits
    cost = await get_credit_cost("trading_simulation")
    transaction = await deduct_credits(
        db,
        user.id,
        cost,
        description=f"AI Trading Simulation: {req.symbol}",
        reference_type="trading_simulation",
    )
    if not transaction:
        raise HTTPException(status_code=402, detail="Insufficient credits")

    # Create simulation (status: pending, won't auto-start)
    simulation = await trading_engine.create_simulation(
        db=db,
        user=user,
        symbol=req.symbol,
        market=req.market,
        agent_name=req.agent_name,
        config=req.config.model_dump() if req.config else None,
    )
    await db.commit()

    # Note: Simulation is created in "pending" status
    # User needs to call POST /simulations/{id}/start to begin execution

    return SimulationResponse.model_validate(simulation)


@router.post("/simulations/{simulation_id}/start", response_model=SimulationResponse)
async def start_simulation(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a pending simulation - AI Agent will begin analyzing and trading"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Only start pending simulations
    if simulation.status != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start simulation with status: {simulation.status}. Only pending simulations can be started."
        )

    # Trigger Celery task to run simulation
    run_trading_simulation.delay(str(simulation.id))

    return SimulationResponse.model_validate(simulation)


@router.get("/simulations", response_model=SimulationListResponse)
async def list_simulations(
    symbol: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's trading simulations"""
    query = select(TradingSimulation).where(TradingSimulation.user_id == user.id)

    if symbol:
        query = query.where(TradingSimulation.symbol == symbol)
    if status:
        query = query.where(TradingSimulation.status == status)

    query = query.order_by(desc(TradingSimulation.created_at))

    all_result = await db.execute(query)
    all_items = all_result.scalars().all()
    total = len(all_items)

    # Paginate
    offset = (page - 1) * page_size
    items = all_items[offset:offset + page_size]

    return SimulationListResponse(
        total=total,
        items=[SimulationResponse.model_validate(item) for item in items],
    )


@router.get("/simulations/{simulation_id}", response_model=SimulationDetailResponse)
async def get_simulation(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get simulation details with trades"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Get trades
    trades_result = await db.execute(
        select(Trade)
        .where(Trade.simulation_id == simulation_id)
        .order_by(Trade.trade_date)
    )
    trades = trades_result.scalars().all()

    response = SimulationDetailResponse.model_validate(simulation)
    response.trades = [TradeResponse.model_validate(t) for t in trades]
    return response


@router.delete("/simulations/{simulation_id}")
async def delete_simulation(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a simulation"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    await db.delete(simulation)
    await db.commit()
    return {"message": "Simulation deleted"}


@router.get("/simulations/{simulation_id}/trades", response_model=list[TradeResponse])
async def get_simulation_trades(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all trades for a simulation"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    # Verify ownership
    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Get trades
    trades_result = await db.execute(
        select(Trade)
        .where(Trade.simulation_id == sim_uuid)
        .order_by(Trade.trade_date)
    )
    trades = trades_result.scalars().all()

    return [TradeResponse.model_validate(t) for t in trades]


@router.post("/simulations/{simulation_id}/pause", response_model=SimulationResponse)
async def pause_simulation(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pause a running simulation (can be resumed later)"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Only pause running simulations
    if simulation.status != "running":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot pause simulation with status: {simulation.status}. Only running simulations can be paused."
        )

    # Update status to paused
    simulation.status = "paused"
    await db.commit()

    return SimulationResponse.model_validate(simulation)


@router.post("/simulations/{simulation_id}/resume", response_model=SimulationResponse)
async def resume_simulation(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a paused simulation"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Only resume paused simulations
    if simulation.status != "paused":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume simulation with status: {simulation.status}. Only paused simulations can be resumed."
        )

    # Change status back to pending and trigger Celery task
    simulation.status = "pending"
    await db.commit()

    # Resume via Celery task
    run_trading_simulation.delay(str(simulation.id))

    return SimulationResponse.model_validate(simulation)


@router.post("/simulations/{simulation_id}/stop", response_model=SimulationResponse)
async def stop_simulation(
    simulation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop a simulation permanently (cannot be resumed)"""
    try:
        sim_uuid = uuid.UUID(simulation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid simulation ID format")

    result = await db.execute(
        select(TradingSimulation).where(
            TradingSimulation.id == sim_uuid,
            TradingSimulation.user_id == user.id,
        )
    )
    simulation = result.scalar_one_or_none()
    if not simulation:
        raise HTTPException(status_code=404, detail="Simulation not found")

    # Can stop pending, running, or paused simulations
    if simulation.status not in ["pending", "running", "paused"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop simulation with status: {simulation.status}"
        )

    # Update status to stopped
    simulation.status = "stopped"
    simulation.summary = "Simulation was manually stopped by user"
    await db.commit()

    return SimulationResponse.model_validate(simulation)
