from __future__ import annotations

from typing import Optional, List
from abc import ABC, abstractmethod
from app.schemas.market import StockQuote, KlinePoint, FundamentalData


class MarketDataProvider(ABC):
    @abstractmethod
    async def get_quote(self, symbol: str) -> StockQuote:
        pass

    @abstractmethod
    async def get_kline(
        self, symbol: str, interval: str = "1day", outputsize: int = 100
    ) -> List[KlinePoint]:
        pass

    @abstractmethod
    async def search(self, query: str) -> List[dict]:
        pass

    async def get_fundamentals(self, symbol: str) -> Optional[FundamentalData]:
        return None
