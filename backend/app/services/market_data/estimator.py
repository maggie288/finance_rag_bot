"""
基于股票行情数据估算基本面指标的服务
当无法获取真实的基本面数据时，通过技术分析和统计方法提供估算值
"""

from __future__ import annotations

import logging
from typing import Optional, List
from statistics import mean, stdev
from app.schemas.market import FundamentalData, KlinePoint, StockQuote

logger = logging.getLogger(__name__)


class MarketDataEstimator:
    """
    基于行情数据估算基本面指标的工具类

    注意：这些估算值仅供参考，不能替代真实的财务数据
    """

    @staticmethod
    def estimate_from_market_data(
        symbol: str,
        market: str,
        quote: Optional[StockQuote] = None,
        kline_data: Optional[List[KlinePoint]] = None,
    ) -> Optional[FundamentalData]:
        """
        基于行情数据估算基本面指标

        Args:
            symbol: 股票代码
            market: 市场
            quote: 实时行情数据
            kline_data: K线历史数据（建议至少100个交易日）

        Returns:
            估算的基本面数据（带有 is_estimated 标记）
        """
        if not quote and not kline_data:
            logger.warning(f"[Estimator] No market data available for {symbol}")
            return None

        logger.info(f"[Estimator] Estimating fundamentals from market data for {symbol}")

        estimated_data = FundamentalData(
            symbol=symbol,
            market=market,
        )

        # 如果有 K线数据，进行更详细的估算
        if kline_data and len(kline_data) >= 20:
            try:
                estimated_data = MarketDataEstimator._estimate_from_kline(
                    symbol, market, kline_data, quote
                )
            except Exception as e:
                logger.error(f"[Estimator] Failed to estimate from kline: {e}")

        # 如果有实时行情，补充一些简单估算
        if quote:
            try:
                MarketDataEstimator._supplement_from_quote(estimated_data, quote)
            except Exception as e:
                logger.error(f"[Estimator] Failed to supplement from quote: {e}")

        # 标记为估算值
        estimated_data.is_estimated = True
        estimated_data.estimation_note = "基于股票行情数据估算，仅供参考"

        return estimated_data

    @staticmethod
    def _estimate_from_kline(
        symbol: str,
        market: str,
        kline_data: List[KlinePoint],
        quote: Optional[StockQuote] = None,
    ) -> FundamentalData:
        """基于K线数据估算指标"""

        # 按时间排序（确保从旧到新）
        sorted_data = sorted(kline_data, key=lambda x: x.datetime)

        # 获取最新价格
        latest_close = sorted_data[-1].close

        # 计算波动率（年化）
        if len(sorted_data) >= 30:
            recent_closes = [k.close for k in sorted_data[-30:]]
            returns = [(recent_closes[i] / recent_closes[i-1] - 1)
                      for i in range(1, len(recent_closes))]
            volatility = stdev(returns) * (252 ** 0.5) if len(returns) > 1 else 0
        else:
            volatility = 0

        # 计算趋势强度（收益率）
        if len(sorted_data) >= 60:
            price_60d_ago = sorted_data[-60].close
            return_60d = (latest_close / price_60d_ago - 1) * 100
        else:
            return_60d = 0

        # 计算移动平均线
        ma20 = mean([k.close for k in sorted_data[-20:]]) if len(sorted_data) >= 20 else latest_close
        ma60 = mean([k.close for k in sorted_data[-60:]]) if len(sorted_data) >= 60 else latest_close

        # 计算成交量趋势
        if len(sorted_data) >= 20:
            recent_volumes = [k.volume for k in sorted_data[-20:] if k.volume]
            avg_volume = mean(recent_volumes) if recent_volumes else 0
        else:
            avg_volume = 0

        # 估算市值（使用最新价格和平均成交量）
        estimated_market_cap = None
        if avg_volume > 0:
            estimated_shares = avg_volume * 50
            estimated_market_cap = latest_close * estimated_shares

        # 估算PE比率（基于价格趋势和波动率）
        estimated_pe = None
        if volatility > 0:
            growth_factor = 1 + (return_60d / 100) if return_60d > 0 else 1
            volatility_factor = 1 + volatility
            estimated_pe = 15 * growth_factor * volatility_factor
            estimated_pe = max(5, min(estimated_pe, 100))

        # 估算PB比率
        estimated_pb = None
        if estimated_pe:
            estimated_pb = estimated_pe * 0.1
            estimated_pb = max(0.5, min(estimated_pb, 20))

        # 估算ROE
        estimated_roe = None
        if return_60d != 0:
            estimated_roe = abs(return_60d) * 2
            estimated_roe = max(0, min(estimated_roe, 50))

        # 估算收入增长率
        estimated_revenue_growth = return_60d if return_60d > 0 else None

        # 估算股息率
        estimated_dividend_yield = None
        if volatility > 0:
            estimated_dividend_yield = max(0, 5 - volatility * 10)
            estimated_dividend_yield = min(estimated_dividend_yield, 10)

        return FundamentalData(
            symbol=symbol,
            market=market,
            pe_ratio=estimated_pe,
            pb_ratio=estimated_pb,
            roe=estimated_roe,
            market_cap=estimated_market_cap,
            revenue_growth=estimated_revenue_growth,
            dividend_yield=estimated_dividend_yield,
            price_ma20=ma20,
            price_ma60=ma60,
            volatility=volatility * 100,
            return_60d=return_60d,
        )

    @staticmethod
    def _supplement_from_quote(data: FundamentalData, quote: StockQuote) -> None:
        """从实时行情补充估算数据"""
        if not data.market_cap and quote.volume and quote.volume > 0:
            estimated_shares = quote.volume * 50
            data.market_cap = quote.price * estimated_shares
