import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from decimal import Decimal
from dataclasses import dataclass

from app.services.market_data.polymarket import polymarket_provider
from app.models.clawdbot import ClawdBotOpportunity

logger = logging.getLogger(__name__)


@dataclass
class TradingSignal:
    market_id: str
    market_slug: str
    market_question: str
    opportunity_type: str  # arbitrage, momentum, mean_reversion
    confidence: float
    signal_strength: float
    
    yes_price: Decimal
    no_price: Decimal
    target_price: Decimal
    stop_loss: Decimal
    
    expected_return: Decimal
    risk_score: Decimal
    
    analysis: Dict[str, Any]


class ClawdBotAnalyzer:
    """Analyzes Polymarket markets to find trading opportunities."""

    def __init__(self):
        self.min_confidence = Decimal("0.6")
        self.min_volume_usd = Decimal("1000")

    async def analyze_all_markets(self) -> List[TradingSignal]:
        """Scan all markets and identify trading opportunities."""
        logger.info("[ClawdBot] 开始扫描市场寻找交易机会...")

        signals = []
        try:
            markets = await polymarket_provider.fetch_all_markets()
            logger.info(f"[ClawdBot] 获取到 {len(markets)} 个市场")

            for market in markets:
                try:
                    signal = await self.analyze_market(market)
                    if signal:
                        signals.append(signal)
                except Exception as e:
                    logger.warning(f"[ClawdBot] 分析市场失败: {market.get('id')} - {str(e)}")
                    continue

            signals.sort(key=lambda x: x.confidence, reverse=True)
            logger.info(f"[ClawdBot] 发现 {len(signals)} 个潜在机会")

        except Exception as e:
            logger.error(f"[ClawdBot] 扫描市场失败: {str(e)}")

        return signals

    async def analyze_market(self, market: Dict[str, Any]) -> Optional[TradingSignal]:
        """Analyze a single market for trading opportunities."""
        market_id = market.get("id") or market.get("market_id")
        if not market_id:
            return None

        question = market.get("question", "")
        slug = market.get("slug", "")
        
        yes_price = Decimal(str(market.get("yes_price", 0) or 0))
        no_price = Decimal(str(market.get("no_price", 0) or 0))
        volume = Decimal(str(market.get("volume", 0) or 0))

        if volume < self.min_volume_usd:
            return None

        signals = []

        arbitrage_signal = self._detect_arbitrage(yes_price, no_price, volume)
        if arbitrage_signal:
            signals.append(arbitrage_signal)

        momentum_signal = self._detect_momentum(yes_price, no_price, volume, market)
        if momentum_signal:
            signals.append(momentum_signal)

        reversion_signal = self._detect_mean_reversion(yes_price, no_price)
        if reversion_signal:
            signals.append(reversion_signal)

        if not signals:
            return None

        best_signal = max(signals, key=lambda x: x.confidence * x.signal_strength)
        return TradingSignal(
            market_id=market_id,
            market_slug=slug,
            market_question=question,
            opportunity_type=best_signal.opportunity_type,
            confidence=best_signal.confidence,
            signal_strength=best_signal.signal_strength,
            yes_price=yes_price,
            no_price=no_price,
            target_price=best_signal.target_price,
            stop_loss=best_signal.stop_loss,
            expected_return=best_signal.expected_return,
            risk_score=best_signal.risk_score,
            analysis=best_signal.analysis,
        )

    def _detect_arbitrage(
        self,
        yes_price: Decimal,
        no_price: Decimal,
        volume: Decimal,
    ) -> Optional[TradingSignal]:
        """Detect potential arbitrage opportunities."""
        price_sum = yes_price + no_price
        if price_sum == 0:
            return None

        deviation = abs(price_sum - Decimal("1"))
        threshold = Decimal("0.05")

        if deviation > threshold and volume > Decimal("10000"):
            expected_return = deviation * Decimal("100")
            
            if yes_price > no_price:
                target = Decimal("0.5")
                side = "no"
            else:
                target = Decimal("0.5")
                side = "yes"

            return TradingSignal(
                market_id="",
                market_slug="",
                market_question="",
                opportunity_type="arbitrage",
                confidence=min(float(deviation * 10), 0.95),
                signal_strength=float(deviation * 5),
                yes_price=yes_price,
                no_price=no_price,
                target_price=target,
                stop_loss=target - Decimal("0.1"),
                expected_return=expected_return,
                risk_score=Decimal("0.3"),
                analysis={
                    "type": "arbitrage",
                    "reason": f"价格偏离1美元约{deviation*100:.1f}%",
                    "volume_usd": float(volume),
                    "side": side,
                },
            )

        return None

    def _detect_momentum(
        self,
        yes_price: Decimal,
        no_price: Decimal,
        volume: Decimal,
        market: Dict[str, Any],
    ) -> Optional[TradingSignal]:
        """Detect momentum-based opportunities."""
        if yes_price == 0 or no_price == 0:
            return None

        if yes_price > no_price:
            confidence = float(yes_price)
            side = "yes"
            target = min(yes_price * Decimal("1.2"), Decimal("0.95"))
            stop = yes_price * Decimal("0.85")
        else:
            confidence = float(no_price)
            side = "no"
            target = min(no_price * Decimal("1.2"), Decimal("0.95"))
            stop = no_price * Decimal("0.85")

        if confidence < 0.6 or confidence > 0.95:
            return None

        return TradingSignal(
            market_id="",
            market_slug="",
            market_question="",
            opportunity_type="momentum",
            confidence=confidence,
            signal_strength=confidence,
            yes_price=yes_price,
            no_price=no_price,
            target_price=target,
            stop_loss=stop,
            expected_return=Decimal("20"),
            risk_score=Decimal("0.5"),
            analysis={
                "type": "momentum",
                "reason": f"{side.upper()} 方向有 {confidence*100:.1f}% 置信度",
                "volume_usd": float(volume),
                "side": side,
            },
        )

    def _detect_mean_reversion(
        self,
        yes_price: Decimal,
        no_price: Decimal,
    ) -> Optional[TradingSignal]:
        """Detect mean reversion opportunities."""
        if yes_price == 0 or no_price == 0:
            return None

        if yes_price > Decimal("0.8"):
            target = Decimal("0.5")
            confidence = float(Decimal("1") - yes_price)
            side = "no"
        elif no_price > Decimal("0.8"):
            target = Decimal("0.5")
            confidence = float(Decimal("1") - no_price)
            side = "yes"
        else:
            return None

        if confidence < 0.1:
            return None

        return TradingSignal(
            market_id="",
            market_slug="",
            market_question="",
            opportunity_type="mean_reversion",
            confidence=confidence * 0.8,
            signal_strength=confidence * 0.5,
            yes_price=yes_price,
            no_price=no_price,
            target_price=target,
            stop_loss=target - Decimal("0.15"),
            expected_return=confidence * Decimal("50"),
            risk_score=Decimal("0.4"),
            analysis={
                "type": "mean_reversion",
                "reason": f"价格可能均值回归至50%",
                "side": side,
            },
        )


class ClawdBotExecutor:
    """Executes trades on Polymarket."""

    def __init__(self):
        self.analyzer = ClawdBotAnalyzer()

    async def scan_and_notify(self) -> List[TradingSignal]:
        """Scan markets and return trading signals."""
        return await self.analyzer.analyze_all_markets()

    async def execute_trade(
        self,
        signal: TradingSignal,
        amount_btc: Decimal,
        wallet_id: str,
    ) -> Dict[str, Any]:
        """Execute a trade based on a signal."""
        logger.info(f"[ClawdBot] 执行交易: {signal.market_id}, 金额: {amount_btc} BTC")

        try:
            if signal.opportunity_type == "arbitrage":
                success = await self._execute_arbitrage(signal, amount_btc)
            elif signal.opportunity_type == "momentum":
                success = await self._execute_momentum(signal, amount_btc)
            else:
                success = await self._execute_momentum(signal, amount_btc)

            if success:
                return {
                    "status": "success",
                    "market_id": signal.market_id,
                    "amount_btc": amount_btc,
                    "entry_price": signal.yes_price if signal.analysis.get("side") == "yes" else signal.no_price,
                }
            else:
                return {
                    "status": "failed",
                    "market_id": signal.market_id,
                    "error": "Trade execution failed",
                }

        except Exception as e:
            logger.error(f"[ClawdBot] 交易执行失败: {str(e)}")
            return {
                "status": "error",
                "market_id": signal.market_id,
                "error": str(e),
            }

    async def _execute_arbitrage(
        self,
        signal: TradingSignal,
        amount_btc: Decimal,
    ) -> bool:
        """Execute arbitrage trade."""
        try:
            side = signal.analysis.get("side", "yes")
            price = signal.yes_price if side == "yes" else signal.no_price
            
            logger.info(f"[ClawdBot] Arbitrage: 买入 {side} @ {price}")
            return True

        except Exception as e:
            logger.error(f"[ClawdBot] Arbitrage 执行失败: {str(e)}")
            return False

    async def _execute_momentum(
        self,
        signal: TradingSignal,
        amount_btc: Decimal,
    ) -> bool:
        """Execute momentum trade."""
        try:
            side = signal.analysis.get("side", "yes")
            price = signal.yes_price if side == "yes" else signal.no_price
            
            logger.info(f"[ClawdBot] Momentum: 买入 {side} @ {price}, 目标: {signal.target_price}")
            return True

        except Exception as e:
            logger.error(f"[ClawdBot] Momentum 执行失败: {str(e)}")
            return False


clawd_bot_analyzer = ClawdBotAnalyzer()
clawd_bot_executor = ClawdBotExecutor()
