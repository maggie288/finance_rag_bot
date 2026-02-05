from __future__ import annotations

from typing import Optional, List, Any
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, model_validator
import uuid


class TradingConfig(BaseModel):
    decision_frequency: str = Field(default="daily", description="daily, hourly")
    max_position_size: float = Field(default=0.5, ge=0.0, le=1.0, description="Max % of portfolio per trade")
    stop_loss_pct: Optional[float] = Field(default=0.1, ge=0.0, le=1.0)
    take_profit_pct: Optional[float] = Field(default=0.2, ge=0.0)
    risk_tolerance: str = Field(default="medium", description="low, medium, high")


class SimulationStartRequest(BaseModel):
    symbol: str = Field(..., description="Stock symbol")
    market: str = Field(..., description="Market: us, hk, cn, commodity")
    agent_name: str = Field(..., description="Agent name: deepseek, minimax, claude, openai")
    config: Optional[TradingConfig] = None


class TradeResponse(BaseModel):
    id: str
    trade_date: datetime
    action: str
    symbol: str
    quantity: Decimal
    price: Decimal
    total_amount: Decimal
    shares_after: Decimal
    cash_after: Decimal
    realized_pnl: Optional[Decimal] = None
    llm_reasoning: str
    confidence_score: Optional[Decimal] = None
    market_data: Optional[dict] = None

    class Config:
        from_attributes = True

    @model_validator(mode="wrap")
    @classmethod
    def convert_uuid_to_str(cls, data, handler):
        if hasattr(data, "__dict__"):
            data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
            if "id" in data_dict and isinstance(data_dict["id"], uuid.UUID):
                data_dict["id"] = str(data_dict["id"])
            return handler(data_dict)
        return handler(data)


class SimulationResponse(BaseModel):
    id: str
    symbol: str
    market: str
    agent_name: str
    llm_model: str
    initial_balance: Decimal
    current_balance: Decimal
    currency: str
    start_date: datetime
    end_date: datetime
    status: str
    current_shares: Decimal
    average_cost: Optional[Decimal] = None
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_profit_loss: Decimal
    max_drawdown: Optional[Decimal] = None
    sharpe_ratio: Optional[Decimal] = None
    config: Optional[dict] = None
    total_tokens_used: int
    total_llm_cost: Decimal
    summary: Optional[str] = None
    error_message: Optional[str] = None
    execution_logs: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @model_validator(mode="wrap")
    @classmethod
    def convert_uuid_to_str(cls, data, handler):
        if hasattr(data, "__dict__"):
            data_dict = {k: v for k, v in data.__dict__.items() if not k.startswith('_')}
            if "id" in data_dict and isinstance(data_dict["id"], uuid.UUID):
                data_dict["id"] = str(data_dict["id"])
            return handler(data_dict)
        return handler(data)


class SimulationDetailResponse(SimulationResponse):
    trades: List[TradeResponse] = []


class SimulationListResponse(BaseModel):
    total: int
    items: List[SimulationResponse]


class AgentInfo(BaseModel):
    name: str
    display_name: str
    description: str
    model_name: str
    available: bool
