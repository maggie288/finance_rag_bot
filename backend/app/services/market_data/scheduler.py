import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.services.market_data.aggregator import market_data
from app.services.market_data.repository import StockDataRepository

logger = logging.getLogger(__name__)

scheduler: Optional[AsyncIOScheduler] = None


async def refresh_all_quotes():
    async with AsyncSessionLocal() as db:
        repo = StockDataRepository(db)
        all_quotes = await repo.get_all_quotes()

        if not all_quotes:
            logger.info("[Scheduler] No quotes to refresh")
            return

        symbols = [
            {"symbol": q.symbol, "market": q.market}
            for q in all_quotes
        ]

        result = await market_data.batch_refresh_quotes(symbols, db)
        logger.info(
            f"[Scheduler] Refreshed {len(result)} quotes at {datetime.now(timezone.utc).isoformat()}"
        )


async def refresh_user_watchlists():
    from sqlalchemy import select
    from app.models.watchlist import Watchlist
    from sqlalchemy.orm import selectinload

    async with AsyncSessionLocal() as db:
        stmt = (
            select(Watchlist)
            .options(selectinload(Watchlist.user))
        )
        result = await db.execute(stmt)
        watchlists = result.scalars().all()

        watchlist_by_user = {}
        for w in watchlists:
            if w.user_id not in watchlist_by_user:
                watchlist_by_user[w.user_id] = []
            watchlist_by_user[w.user_id].append({
                "symbol": w.symbol,
                "market": w.market,
                "name": w.name,
            })

        for user_id, items in watchlist_by_user.items():
            try:
                result = await market_data.refresh_user_watchlist(items, db)
                logger.info(
                    f"[Scheduler] User {user_id}: "
                    f"success={result['success']}, failed={result['failed']}"
                )
            except Exception as e:
                logger.error(f"[Scheduler] Failed to refresh user {user_id}: {e}")


async def cleanup_old_klines():
    from app.services.market_data.repository import StockDataRepository

    async with AsyncSessionLocal() as db:
        repo = StockDataRepository(db)
        markets = ["us", "hk", "cn", "commodity"]
        intervals = ["1day", "1week", "1month"]

        for market in markets:
            for interval in intervals:
                try:
                    count = await repo.delete_klines(
                        symbol="*",  # This needs a different approach
                        market=market,
                        interval=interval,
                        keep_latest=500,
                    )
                    if count > 0:
                        logger.info(f"[Scheduler] Cleaned {count} old klines for {market}/{interval}")
                except Exception as e:
                    logger.error(f"[Scheduler] Failed to cleanup {market}/{interval}: {e}")


def start_scheduler():
    global scheduler
    if scheduler is not None:
        return scheduler

    scheduler = AsyncIOScheduler(timezone="UTC")

    scheduler.add_job(
        refresh_all_quotes,
        trigger=IntervalTrigger(minutes=5),
        id="refresh_all_quotes",
        name="Refresh all cached quotes every 5 minutes",
        replace_existing=True,
    )

    scheduler.add_job(
        refresh_user_watchlists,
        trigger=CronTrigger(hour="*", minute="2"),
        id="refresh_user_watchlists",
        name="Refresh user watchlists every hour",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("[Scheduler] Started market data scheduler")

    return scheduler


def stop_scheduler():
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("[Scheduler] Stopped market data scheduler")


async def trigger_manual_refresh(market: Optional[str] = None) -> dict:
    async with AsyncSessionLocal() as db:
        repo = StockDataRepository(db)
        all_quotes = await repo.get_all_quotes(market=market)

        if not all_quotes:
            return {"message": "No quotes found", "refreshed": 0}

        symbols = [
            {"symbol": q.symbol, "market": q.market}
            for q in all_quotes
        ]

        result = await market_data.batch_refresh_quotes(symbols, db)

        return {
            "message": f"Refreshed {len(result)} quotes",
            "refreshed": len(result),
            "market": market or "all",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
