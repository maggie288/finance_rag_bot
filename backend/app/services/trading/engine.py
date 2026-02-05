from __future__ import annotations

import logging
from typing import Optional, List
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.trading import TradingSimulation, Trade
from app.models.user import User
from app.services.market_data.aggregator import market_data
from app.services.llm.provider import llm_provider
from app.schemas.market import KlinePoint

logger = logging.getLogger(__name__)


class TradingEngine:
    """Core trading simulation engine"""

    def __init__(self):
        self.commission_rate = Decimal("0.001")  # 0.1% commission per trade

    def _add_log(self, simulation: TradingSimulation, level: str, message: str):
        """Add a log entry to the simulation"""
        if simulation.execution_logs is None:
            simulation.execution_logs = {"logs": []}

        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
        }
        simulation.execution_logs["logs"].append(log_entry)
        logger.info(f"[Simulation {simulation.id}] {level.upper()}: {message}")

    def get_initial_balance(self, market: str) -> tuple[Decimal, str]:
        """Get initial balance based on market"""
        if market == "cn":
            return Decimal("50000"), "CNY"
        else:
            return Decimal("50000"), "USD"

    async def create_simulation(
        self,
        db: AsyncSession,
        user: User,
        symbol: str,
        market: str,
        agent_name: str,
        config: Optional[dict] = None,
    ) -> TradingSimulation:
        """Create a new trading simulation"""
        initial_balance, currency = self.get_initial_balance(market)

        # Simulation period: Feb 2026 - Apr 2026
        start_date = datetime(2026, 2, 1, tzinfo=timezone.utc)
        end_date = datetime(2026, 4, 30, 23, 59, 59, tzinfo=timezone.utc)

        # Map agent name to LLM model
        model_mapping = {
            "deepseek": "deepseek",
            "minimax": "minimax",
            "claude": "claude",
            "openai": "openai",
        }
        llm_model = model_mapping.get(agent_name, "deepseek")

        simulation = TradingSimulation(
            user_id=user.id,
            symbol=symbol,
            market=market,
            agent_name=agent_name,
            llm_model=llm_model,
            initial_balance=initial_balance,
            current_balance=initial_balance,
            currency=currency,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            current_shares=Decimal("0"),
            config=config or {},
        )

        db.add(simulation)
        await db.flush()
        return simulation

    async def run_simulation(
        self, db: AsyncSession, simulation: TradingSimulation
    ) -> TradingSimulation:
        """Run the simulation from start to end date"""
        try:
            simulation.status = "running"
            self._add_log(simulation, "info", f"🚀 开始AI交易模拟 - {simulation.agent_name.upper()} Agent")
            self._add_log(simulation, "info", f"📈 交易标的: {simulation.symbol} ({simulation.market.upper()})")
            self._add_log(simulation, "info", f"💰 初始资金: {simulation.initial_balance} {simulation.currency}")
            await db.flush()

            # Fetch historical data for the simulation period
            # We need 60 trading days (Feb-Apr ~= 60 days)
            self._add_log(simulation, "info", "📊 正在获取历史市场数据...")
            klines = await market_data.get_kline(
                symbol=simulation.symbol,
                market=simulation.market,
                interval="1day",
                outputsize=100,
                db=db,
            )

            if not klines or len(klines) < 20:
                self._add_log(simulation, "error", "❌ 历史数据不足，无法进行模拟")
                raise ValueError("Insufficient historical data for simulation")

            self._add_log(simulation, "info", f"✅ 成功获取 {len(klines)} 条历史数据")

            # Filter klines within simulation period
            sim_klines = []
            # Ensure simulation dates are timezone-aware
            sim_start = simulation.start_date
            sim_end = simulation.end_date
            if sim_start.tzinfo is None:
                sim_start = sim_start.replace(tzinfo=timezone.utc)
            if sim_end.tzinfo is None:
                sim_end = sim_end.replace(tzinfo=timezone.utc)

            for k in klines:
                try:
                    # Handle various datetime formats
                    k_dt_str = k.datetime.replace("Z", "+00:00")
                    k_dt = datetime.fromisoformat(k_dt_str)
                    # Ensure kline datetime is also timezone-aware
                    if k_dt.tzinfo is None:
                        k_dt = k_dt.replace(tzinfo=timezone.utc)
                    if sim_start <= k_dt <= sim_end:
                        sim_klines.append(k)
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse kline datetime: {k.datetime}, error: {e}")
                    continue

            if len(sim_klines) < 10:
                # If no data in Feb-Apr 2026 (future), use last 60 days for simulation
                sim_klines = klines[-60:] if len(klines) >= 60 else klines
                self._add_log(simulation, "info", f"⚠️ 使用最近 {len(sim_klines)} 天的历史数据进行回测")

            logger.info(f"Running simulation for {simulation.symbol} with {len(sim_klines)} trading days")
            self._add_log(simulation, "info", f"🔄 开始回测，共 {len(sim_klines)} 个交易日")
            self._add_log(simulation, "info", "=" * 50)

            # Run trading logic for each day
            for idx, kline in enumerate(sim_klines):
                # Check if simulation was stopped or paused
                await db.refresh(simulation)
                if simulation.status == "stopped":
                    self._add_log(simulation, "warning", "⏹️ 模拟已被用户手动停止")
                    break
                if simulation.status == "paused":
                    self._add_log(simulation, "warning", "⏸️ 模拟已被用户暂停，等待恢复...")
                    break

                # Provide market context (recent price history)
                lookback = sim_klines[max(0, idx-20):idx+1]

                trade_date_str = kline.datetime[:10]
                self._add_log(simulation, "info", f"📅 第 {idx+1}/{len(sim_klines)} 天 ({trade_date_str})")
                self._add_log(simulation, "info", f"   💹 当前价格: ${kline.close:.2f} | 开盘: ${kline.open:.2f} | 最高: ${kline.high:.2f} | 最低: ${kline.low:.2f}")

                # Calculate current portfolio value
                position_value = simulation.current_shares * Decimal(str(kline.close))
                total_value = simulation.current_balance + position_value
                self._add_log(
                    simulation,
                    "info",
                    f"   📊 持仓: {simulation.current_shares:.2f} 股 (${position_value:.2f}) | 现金: ${simulation.current_balance:.2f} | 总资产: ${total_value:.2f}"
                )

                self._add_log(simulation, "info", f"   🤖 AI正在分析市场并做出决策...")

                decision = await self._make_trading_decision(
                    simulation=simulation,
                    current_kline=kline,
                    price_history=lookback,
                    db=db,
                )

                if decision:
                    self._add_log(
                        simulation,
                        "info",
                        f"   💡 AI决策: {decision['action'].upper()} {decision['quantity']:.2f} 股 (信心度: {float(decision['confidence'])*100:.1f}%)"
                    )
                    self._add_log(simulation, "info", f"   📝 决策理由: {decision['reasoning'][:100]}...")

                    await self._execute_trade(
                        simulation=simulation,
                        decision=decision,
                        current_price=kline.close,
                        trade_date=datetime.fromisoformat(kline.datetime.replace("Z", "+00:00")),
                        market_data=kline,
                        db=db,
                    )
                else:
                    self._add_log(simulation, "info", f"   ⏸️ AI决策: HOLD - 暂不交易")

                self._add_log(simulation, "info", "-" * 50)

            # Calculate final metrics
            self._add_log(simulation, "info", "📊 计算最终性能指标...")
            await self._calculate_metrics(simulation, db)

            self._add_log(simulation, "success", "🎉 模拟完成！")
            self._add_log(simulation, "info", f"📈 总交易次数: {simulation.total_trades}")
            self._add_log(simulation, "info", f"💰 总盈亏: ${simulation.total_profit_loss:.2f}")
            roi = (simulation.total_profit_loss / simulation.initial_balance * 100) if simulation.initial_balance > 0 else 0
            self._add_log(simulation, "info", f"📊 投资回报率: {roi:+.2f}%")

            simulation.status = "completed"
            simulation.summary = self._generate_summary(simulation)

        except Exception as e:
            logger.error(f"Simulation failed: {e}")
            self._add_log(simulation, "error", f"❌ 模拟失败: {str(e)}")
            simulation.status = "failed"
            simulation.error_message = str(e)

        await db.flush()
        return simulation

    async def _make_trading_decision(
        self,
        simulation: TradingSimulation,
        current_kline: KlinePoint,
        price_history: List[KlinePoint],
        db: AsyncSession,
    ) -> Optional[dict]:
        """Use LLM to make trading decision"""
        # Build context for LLM
        recent_prices = [f"Date: {k.datetime[:10]}, O:{k.open:.2f}, H:{k.high:.2f}, L:{k.low:.2f}, C:{k.close:.2f}, V:{k.volume or 0}"
                         for k in price_history[-10:]]

        current_price = current_kline.close
        position_value = simulation.current_shares * Decimal(str(current_price))
        total_value = simulation.current_balance + position_value

        prompt = f"""You are an AI trading agent managing a stock portfolio.

**Current Portfolio Status:**
- Symbol: {simulation.symbol}
- Cash Balance: {simulation.current_balance:.2f} {simulation.currency}
- Current Shares: {simulation.current_shares:.6f}
- Current Price: {current_price:.2f}
- Position Value: {position_value:.2f}
- Total Portfolio Value: {total_value:.2f}

**Recent Price History (last 10 days):**
{chr(10).join(recent_prices)}

**Today's Price:**
- Date: {current_kline.datetime[:10]}
- Open: {current_kline.open:.2f}
- High: {current_kline.high:.2f}
- Low: {current_kline.low:.2f}
- Close: {current_kline.close:.2f}
- Volume: {current_kline.volume or 0}

**Trading Rules:**
- Maximum position size: {simulation.config.get('max_position_size', 0.5) * 100}% of portfolio
- You can BUY, SELL, or HOLD
- Consider technical indicators, trend, volume
- Provide clear reasoning for your decision

**Please respond in EXACTLY this JSON format:**
{{
  "action": "buy" or "sell" or "hold",
  "quantity_shares": <number of shares to trade, 0 if hold>,
  "confidence": <0.0 to 1.0>,
  "reasoning": "<detailed explanation of your decision>"
}}

Decision:"""

        try:
            response = await llm_provider.chat(
                model_key=simulation.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            # Parse LLM response
            import json
            content = response["content"].strip()

            # Try to extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            decision = json.loads(content)

            # Update simulation metrics
            simulation.total_tokens_used += response.get("tokens_used", 0)
            simulation.total_llm_cost += Decimal(str(response.get("cost_usd", 0)))

            # Validate decision
            action = decision.get("action", "hold").lower()
            if action not in ["buy", "sell", "hold"]:
                action = "hold"

            if action == "hold":
                return None

            return {
                "action": action,
                "quantity": Decimal(str(decision.get("quantity_shares", 0))),
                "confidence": Decimal(str(decision.get("confidence", 0.5))),
                "reasoning": decision.get("reasoning", "No reasoning provided"),
                "tokens_used": response.get("tokens_used", 0),
                "llm_cost": Decimal(str(response.get("cost_usd", 0))),
            }

        except Exception as e:
            logger.error(f"LLM decision failed: {e}")
            return None

    async def _execute_trade(
        self,
        simulation: TradingSimulation,
        decision: dict,
        current_price: float,
        trade_date: datetime,
        market_data: KlinePoint,
        db: AsyncSession,
    ):
        """Execute a trade and update simulation state"""
        action = decision["action"]
        quantity = decision["quantity"]
        price = Decimal(str(current_price))

        if quantity <= 0:
            return

        # Validate trade
        if action == "buy":
            cost = quantity * price
            commission = cost * self.commission_rate
            total_cost = cost + commission

            if total_cost > simulation.current_balance:
                # Can't afford, reduce quantity
                quantity = (simulation.current_balance * Decimal("0.99")) / (price * (Decimal("1") + self.commission_rate))
                cost = quantity * price
                commission = cost * self.commission_rate
                total_cost = cost + commission

            if quantity <= 0:
                return

            shares_before = simulation.current_shares
            cash_before = simulation.current_balance

            simulation.current_shares += quantity
            simulation.current_balance -= total_cost

            # Update average cost
            if shares_before > 0:
                total_cost_basis = shares_before * (simulation.average_cost or price) + cost
                simulation.average_cost = total_cost_basis / simulation.current_shares
            else:
                simulation.average_cost = price

            self._add_log(
                simulation,
                "success",
                f"   ✅ 买入成功: {quantity:.2f} 股 @ ${price:.2f} | 手续费: ${commission:.2f} | 总成本: ${total_cost:.2f}"
            )
            self._add_log(
                simulation,
                "info",
                f"   📊 交易后: 持仓 {simulation.current_shares:.2f} 股 | 现金余额: ${simulation.current_balance:.2f}"
            )

            trade = Trade(
                simulation_id=simulation.id,
                trade_date=trade_date,
                action="buy",
                symbol=simulation.symbol,
                quantity=quantity,
                price=price,
                total_amount=total_cost,
                commission=commission,
                shares_before=shares_before,
                shares_after=simulation.current_shares,
                cash_before=cash_before,
                cash_after=simulation.current_balance,
                realized_pnl=None,
                llm_reasoning=decision["reasoning"],
                confidence_score=decision["confidence"],
                market_data={
                    "price": float(price),
                    "open": market_data.open,
                    "high": market_data.high,
                    "low": market_data.low,
                    "close": market_data.close,
                    "volume": market_data.volume,
                },
                tokens_used=decision["tokens_used"],
                llm_cost=decision["llm_cost"],
            )

        elif action == "sell":
            if quantity > simulation.current_shares:
                quantity = simulation.current_shares

            if quantity <= 0:
                return

            proceeds = quantity * price
            commission = proceeds * self.commission_rate
            net_proceeds = proceeds - commission

            shares_before = simulation.current_shares
            cash_before = simulation.current_balance

            # Calculate realized P&L
            cost_basis = quantity * (simulation.average_cost or price)
            realized_pnl = net_proceeds - cost_basis

            simulation.current_shares -= quantity
            simulation.current_balance += net_proceeds

            # Track wins/losses
            if realized_pnl > 0:
                simulation.winning_trades += 1
            elif realized_pnl < 0:
                simulation.losing_trades += 1

            profit_emoji = "📈" if realized_pnl > 0 else "📉" if realized_pnl < 0 else "➖"
            self._add_log(
                simulation,
                "success" if realized_pnl > 0 else "warning" if realized_pnl < 0 else "info",
                f"   ✅ 卖出成功: {quantity:.2f} 股 @ ${price:.2f} | 手续费: ${commission:.2f} | 净收益: ${net_proceeds:.2f}"
            )
            self._add_log(
                simulation,
                "success" if realized_pnl > 0 else "warning",
                f"   {profit_emoji} 已实现盈亏: ${realized_pnl:+.2f} | 成本: ${cost_basis:.2f}"
            )
            self._add_log(
                simulation,
                "info",
                f"   📊 交易后: 持仓 {simulation.current_shares:.2f} 股 | 现金余额: ${simulation.current_balance:.2f}"
            )

            trade = Trade(
                simulation_id=simulation.id,
                trade_date=trade_date,
                action="sell",
                symbol=simulation.symbol,
                quantity=quantity,
                price=price,
                total_amount=net_proceeds,
                commission=commission,
                shares_before=shares_before,
                shares_after=simulation.current_shares,
                cash_before=cash_before,
                cash_after=simulation.current_balance,
                realized_pnl=realized_pnl,
                llm_reasoning=decision["reasoning"],
                confidence_score=decision["confidence"],
                market_data={
                    "price": float(price),
                    "open": market_data.open,
                    "high": market_data.high,
                    "low": market_data.low,
                    "close": market_data.close,
                    "volume": market_data.volume,
                },
                tokens_used=decision["tokens_used"],
                llm_cost=decision["llm_cost"],
            )

        simulation.total_trades += 1
        db.add(trade)
        await db.flush()

    async def _calculate_metrics(self, simulation: TradingSimulation, db: AsyncSession):
        """Calculate performance metrics"""
        # Get all trades
        result = await db.execute(
            select(Trade).where(Trade.simulation_id == simulation.id).order_by(Trade.trade_date)
        )
        trades = result.scalars().all()

        if not trades:
            return

        # Calculate total P&L (realized + unrealized)
        realized_pnl = sum(t.realized_pnl or Decimal("0") for t in trades)

        # Get final price for unrealized P&L
        if simulation.current_shares > 0 and trades:
            last_price = trades[-1].price
            unrealized_pnl = simulation.current_shares * last_price - simulation.current_shares * (simulation.average_cost or last_price)
        else:
            unrealized_pnl = Decimal("0")

        simulation.total_profit_loss = realized_pnl + unrealized_pnl

        # Calculate max drawdown and portfolio value trajectory
        portfolio_values = []
        returns = []
        for i, trade in enumerate(trades):
            total_value = trade.cash_after + trade.shares_after * trade.price
            portfolio_values.append(total_value)

            # Calculate daily returns for Sharpe ratio
            if i > 0:
                prev_value = portfolio_values[i-1]
                if prev_value > 0:
                    daily_return = float((total_value - prev_value) / prev_value)
                    returns.append(daily_return)

        if portfolio_values:
            peak = portfolio_values[0]
            max_dd = Decimal("0")
            for value in portfolio_values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak if peak > 0 else Decimal("0")
                if dd > max_dd:
                    max_dd = dd
            simulation.max_drawdown = max_dd

        # Calculate Sharpe Ratio (annualized, assuming 252 trading days)
        if len(returns) > 1:
            import statistics
            avg_return = statistics.mean(returns)
            std_return = statistics.stdev(returns)
            if std_return > 0:
                # Annualized Sharpe Ratio (assuming risk-free rate = 0)
                sharpe = (avg_return / std_return) * (252 ** 0.5)
                simulation.sharpe_ratio = Decimal(str(round(sharpe, 4)))
            else:
                simulation.sharpe_ratio = Decimal("0")

    def _generate_summary(self, simulation: TradingSimulation) -> str:
        """Generate simulation summary"""
        win_rate = (simulation.winning_trades / simulation.total_trades * 100) if simulation.total_trades > 0 else 0
        roi = (simulation.total_profit_loss / simulation.initial_balance * 100) if simulation.initial_balance > 0 else 0

        # Calculate final portfolio value
        final_value = simulation.current_balance + (simulation.current_shares * (simulation.average_cost or Decimal("0")))

        summary = f"""📊 Trading Simulation Summary

**Performance Metrics:**
- Total Trades: {simulation.total_trades}
- Winning Trades: {simulation.winning_trades} ✅
- Losing Trades: {simulation.losing_trades} ❌
- Win Rate: {win_rate:.1f}%

**Financial Results:**
- Initial Balance: {simulation.initial_balance:.2f} {simulation.currency}
- Final Portfolio Value: {final_value:.2f} {simulation.currency}
- Total P&L: {simulation.total_profit_loss:.2f} {simulation.currency} ({'+' if roi >= 0 else ''}{roi:.2f}%)
- ROI: {roi:.2f}%

**Risk Metrics:**
- Max Drawdown: {(simulation.max_drawdown or Decimal("0")) * 100:.2f}%
- Sharpe Ratio: {simulation.sharpe_ratio or Decimal("0"):.4f}

**Position Details:**
- Final Cash: {simulation.current_balance:.2f} {simulation.currency}
- Final Shares: {simulation.current_shares:.6f}
- Average Cost: {simulation.average_cost or 0:.2f} {simulation.currency}

**AI Agent Stats:**
- Agent: {simulation.agent_name.upper()}
- Total Tokens: {simulation.total_tokens_used:,}
- LLM Cost: ${simulation.total_llm_cost:.4f}
"""
        return summary


trading_engine = TradingEngine()
