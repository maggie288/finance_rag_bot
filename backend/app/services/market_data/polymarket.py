import logging
import httpx
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal

logger = logging.getLogger(__name__)

POLYMARKET_API_BASE = "https://gamma-api.polymarket.com"


class PolymarketClient:
    def __init__(self):
        self.base_url = POLYMARKET_API_BASE
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def get_markets(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        active: bool = True,
    ) -> List[Dict[str, Any]]:
        """Fetch markets from Polymarket."""
        client = await self._get_client()
        
        params = {
            "limit": limit,
            "offset": offset,
            "active": str(active).lower(),
        }
        if category:
            params["category"] = category

        try:
            logger.debug(f"[Polymarket] 获取市场列表: {params}")
            resp = await client.get(f"{self.base_url}/markets", params=params)
            resp.raise_for_status()
            data = resp.json()
            
            markets = data.get("markets", []) if isinstance(data, dict) else data
            logger.info(f"[Polymarket] 获取到 {len(markets)} 个市场")
            return markets

        except httpx.HTTPStatusError as e:
            logger.error(f"[Polymarket] API错误: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"[Polymarket] 获取市场失败: {str(e)}")
            raise

    async def get_market_detail(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed market information."""
        client = await self._get_client()

        try:
            logger.debug(f"[Polymarket] 获取市场详情: {market_id}")
            resp = await client.get(f"{self.base_url}/markets/{market_id}")
            
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            
            data = resp.json()
            logger.info(f"[Polymarket] 获取市场详情成功: {market_id}")
            return data

        except Exception as e:
            logger.error(f"[Polymarket] 获取市场详情失败: {str(e)}")
            raise

    async def get_order_book(self, market_id: str) -> Dict[str, Any]:
        """Get order book for a market."""
        client = await self._get_client()

        try:
            resp = await client.get(f"{self.base_url}/markets/{market_id}/order-book")
            resp.raise_for_status()
            return resp.json()

        except Exception as e:
            logger.error(f"[Polymarket] 获取订单簿失败: {str(e)}")
            raise

    async def get_market_events(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trending or events markets."""
        client = await self._get_client()

        try:
            params = {}
            if category:
                params["category"] = category

            resp = await client.get(f"{self.base_url}/events", params=params)
            resp.raise_for_status()
            return resp.json().get("events", [])

        except Exception as e:
            logger.error(f"[Polymarket] 获取事件失败: {str(e)}")
            raise


class PolymarketProvider:
    """Polymarket data provider for ClawdBot."""

    def __init__(self):
        self.client = PolymarketClient()

    async def fetch_all_markets(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all active markets."""
        return await self.client.get_markets(category=category, limit=100)

    async def get_market_prices(self, market_id: str) -> Dict[str, Any]:
        """Get current yes/no prices for a market."""
        try:
            market = await self.client.get_market_detail(market_id)
            if not market:
                return {}

            return {
                "yes_price": Decimal(str(market.get("yes_price", 0))),
                "no_price": Decimal(str(market.get("no_price", 0))),
                "volume": Decimal(str(market.get("volume", 0))),
                "liquidity": Decimal(str(market.get("liquidity", 0))),
                "last_updated": datetime.now(timezone.utc),
            }
        except Exception as e:
            logger.error(f"[Polymarket] 获取价格失败: {market_id} - {str(e)}")
            return {}

    async def get_trending_markets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get trending markets by volume."""
        markets = await self.fetch_all_markets()
        
        sorted_markets = sorted(
            markets,
            key=lambda x: float(x.get("volume", 0) or 0),
            reverse=True
        )
        
        return sorted_markets[:limit]

    async def search_markets(self, query: str) -> List[Dict[str, Any]]:
        """Search markets by keyword."""
        markets = await self.fetch_all_markets()
        
        query_lower = query.lower()
        filtered = [
            m for m in markets
            if query_lower in m.get("question", "").lower()
            or query_lower in m.get("slug", "").lower()
        ]
        
        return filtered

    async def close(self):
        await self.client.close()


polymarket_provider = PolymarketProvider()
