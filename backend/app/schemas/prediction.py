from __future__ import annotations

from typing import Optional, List, Dict
from uuid import UUID
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel


class PredictionRequest(BaseModel):
    symbol: str
    market: str
    prediction_type: str  # 3day | 1week | 1month


class PredictionPriceRange(BaseModel):
    low: float
    mid: float
    high: float


class ComputationStep(BaseModel):
    step: int
    title: str
    description: str
    data: Optional[dict] = None


class PredictionResponse(BaseModel):
    id: UUID
    symbol: str
    market: str
    prediction_type: str
    current_price: float
    current_state: str
    state_labels: List[str]
    transition_matrix: List[List[float]]
    predicted_state_probs: Dict[str, float]
    predicted_range: PredictionPriceRange
    confidence: float
    computation_steps: List[ComputationStep]
    created_at: datetime

    model_config = {"from_attributes": True}
