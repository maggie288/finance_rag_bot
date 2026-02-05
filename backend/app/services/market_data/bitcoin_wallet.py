import logging
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime, timezone
import httpx

logger = logging.getLogger(__name__)


class BitcoinWalletProvider:
    """Bitcoin wallet integration provider."""

    def __init__(self, rpc_user: str, rpc_password: str, rpc_host: str = "127.0.0.1", rpc_port: int = 8332):
        self.rpc_url = f"http://{rpc_host}:{rpc_port}"
        self.auth = (rpc_user, rpc_password)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _call_rpc(self, method: str, params: list = None) -> Dict[str, Any]:
        """Make RPC call to Bitcoin Core."""
        client = await self._get_client()

        payload = {
            "jsonrpc": "2.0",
            "id": "clawdbot",
            "method": method,
            "params": params or [],
        }

        try:
            resp = await client.post(
                self.rpc_url,
                json=payload,
                auth=self.auth,
                headers={"Content-Type": "application/json"},
            )
            resp.raise_for_status()
            result = resp.json()

            if result.get("error"):
                raise Exception(f"RPC Error: {result['error']}")

            return result.get("result", {})

        except Exception as e:
            logger.error(f"[Bitcoin] RPC call {method} failed: {str(e)}")
            raise

    async def get_balance(self, address: str) -> Dict[str, Any]:
        """Get balance for an address."""
        try:
            result = await self._call_rpc("getaddressbalance", [{"address": address}])
            
            return {
                "confirmed": Decimal(str(result.get("confirmed", 0))) / 100000000,
                "unconfirmed": Decimal(str(result.get("unconfirmed", 0))) / 100000000,
                "total": Decimal(str(result.get("balance", 0))) / 100000000,
            }

        except Exception as e:
            logger.error(f"[Bitcoin] 获取余额失败: {address} - {str(e)}")
            return {
                "confirmed": Decimal("0"),
                "unconfirmed": Decimal("0"),
                "total": Decimal("0"),
            }

    async def get_wallet_info(self) -> Dict[str, Any]:
        """Get wallet information."""
        try:
            result = await self._call_rpc("getwalletinfo")
            return {
                "balance": Decimal(str(result.get("balance", 0))),
                "unconfirmed_balance": Decimal(str(result.get("unconfirmed_balance", 0))),
                "immature_balance": Decimal(str(result.get("immature_balance", 0))),
                "tx_count": result.get("txcount", 0),
            }

        except Exception as e:
            logger.error(f"[Bitcoin] 获取钱包信息失败: {str(e)}")
            return {}

    async def send_to_address(
        self,
        address: str,
        amount_btc: Decimal,
        comment: str = "",
    ) -> Dict[str, Any]:
        """Send Bitcoin to an address."""
        try:
            result = await self._call_rpc("sendtoaddress", [
                address,
                float(amount_btc),
                comment,
            ])

            return {
                "txid": result,
                "address": address,
                "amount": amount_btc,
                "status": "pending",
            }

        except Exception as e:
            logger.error(f"[Bitcoin] 发送失败: {address} - {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
            }

    async def get_transaction(self, txid: str) -> Dict[str, Any]:
        """Get transaction details."""
        try:
            result = await self._call_rpc("gettransaction", [txid])
            return {
                "txid": txid,
                "amount": Decimal(str(result.get("amount", 0))),
                "confirmations": result.get("confirmations", 0),
                "time": result.get("time", 0),
                "blockindex": result.get("blockindex", 0),
            }

        except Exception as e:
            logger.error(f"[Bitcoin] 获取交易失败: {txid} - {str(e)}")
            return {}


class BitcoinPriceProvider:
    """Get Bitcoin price from exchanges."""

    async def get_btc_usd_price(self) -> Decimal:
        """Get current BTC/USD price."""
        try:
            client = httpx.AsyncClient(timeout=30.0)
            
            resp = await client.get("https://api.coingecko.com/api/v3/simple/price", params={
                "ids": "bitcoin",
                "vs_currencies": "usd",
            })
            resp.raise_for_status()
            data = resp.json()
            
            return Decimal(str(data.get("bitcoin", {}).get("usd", 0)))

        except Exception as e:
            logger.error(f"[Bitcoin] 获取价格失败: {str(e)}")
            return Decimal("0")

    async def get_btc_to_usd(self, amount_btc: Decimal) -> Decimal:
        """Convert BTC to USD."""
        price = await self.get_btc_usd_price()
        return amount_btc * price


class BitcoinWalletService:
    """Bitcoin wallet service for ClawdBot."""

    def __init__(self, rpc_user: str, rpc_password: str, rpc_host: str = "127.0.0.1", rpc_port: int = 8332):
        self.provider = BitcoinWalletProvider(rpc_user, rpc_password, rpc_host, rpc_port)
        self.price_provider = BitcoinPriceProvider()

    async def sync_wallet_balance(
        self,
        address: str,
    ) -> Dict[str, Any]:
        """Sync wallet balance from blockchain."""
        balance = await self.provider.get_balance(address)
        price = await self.price_provider.get_btc_usd_price()
        balance_usd = balance["total"] * price

        return {
            "address": address,
            "balance_btc": balance["total"],
            "balance_usd": balance_usd,
            "btc_price_usd": price,
            "last_sync": datetime.now(timezone.utc),
        }

    async def calculate_position_size(
        self,
        available_btc: Decimal,
        confidence: Decimal,
        risk_per_trade: Decimal = Decimal("0.02"),
    ) -> Decimal:
        """Calculate position size based on Kelly Criterion."""
        if confidence <= 0 or confidence >= 1:
            return Decimal("0")

        kelly = confidence - ((Decimal("1") - confidence) / (Decimal("1") / confidence))
        position_size = available_btc * kelly * risk_per_trade
        
        max_position = available_btc * Decimal("0.1")
        return min(position_size, max_position)

    async def estimate_trade_value(
        self,
        yes_price: Decimal,
        no_price: Decimal,
        amount_btc: Decimal,
    ) -> Dict[str, Any]:
        """Estimate trade value in shares."""
        price_usd = await self.price_provider.get_btc_usd_price()
        
        amount_usd = amount_btc * price_usd
        shares = amount_usd / yes_price if yes_price > 0 else Decimal("0")

        return {
            "amount_btc": amount_btc,
            "amount_usd": amount_usd,
            "shares": shares,
            "btc_price_usd": price_usd,
        }

    async def close(self):
        await self.provider.close()


bitcoin_wallet_service = None


def get_bitcoin_wallet_service(
    rpc_user: str = "bitcoin",
    rpc_password: str = "password",
    rpc_host: str = "127.0.0.1",
    rpc_port: int = 8332,
) -> BitcoinWalletService:
    """Get or create Bitcoin wallet service singleton."""
    global bitcoin_wallet_service
    if bitcoin_wallet_service is None:
        bitcoin_wallet_service = BitcoinWalletService(rpc_user, rpc_password, rpc_host, rpc_port)
    return bitcoin_wallet_service
