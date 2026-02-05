"""AI交易模拟Celery任务"""
from __future__ import annotations

import logging
import asyncio
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select

from app.workers.celery_app import celery_app
from app.config import settings
from app.services.trading.engine import trading_engine
from app.models.trading import TradingSimulation

logger = logging.getLogger(__name__)


def get_celery_db_session():
    """
    Create a dedicated async engine for Celery tasks.
    Each task gets its own engine to avoid connection conflicts.
    """
    engine = create_async_engine(
        settings.database_url,
        echo=False,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return engine, session_factory


@celery_app.task(bind=True, name="run_trading_simulation")
def run_trading_simulation(self, simulation_id: str):
    """
    运行AI交易模拟任务

    Args:
        simulation_id: 模拟ID (UUID string)

    Returns:
        {"success": bool, "status": str, "total_trades": int, "profit_loss": float, "error": str}
    """
    async def _async_run():
        logger.info(f"Starting trading simulation task: {simulation_id}")

        try:
            sim_uuid = uuid.UUID(simulation_id)
        except ValueError:
            logger.error(f"Invalid simulation ID format: {simulation_id}")
            return {
                "success": False,
                "status": "failed",
                "total_trades": 0,
                "profit_loss": 0,
                "error": "Invalid simulation ID format"
            }

        # Create dedicated engine for this task
        engine, SessionLocal = get_celery_db_session()

        try:
            async with SessionLocal() as db:
                # 获取模拟记录
                result = await db.execute(
                    select(TradingSimulation).where(TradingSimulation.id == sim_uuid)
                )
                simulation = result.scalar_one_or_none()

                if not simulation:
                    logger.error(f"Simulation not found: {simulation_id}")
                    return {
                        "success": False,
                        "status": "failed",
                        "total_trades": 0,
                        "profit_loss": 0,
                        "error": "Simulation not found"
                    }

                # 检查状态 - 只允许 pending 状态的模拟启动
                if simulation.status not in ["pending"]:
                    logger.warning(f"Simulation {simulation_id} is not in pending status: {simulation.status}")
                    # 如果是 paused/stopped/completed/failed 状态，不是错误，只是不执行
                    if simulation.status in ["paused", "stopped", "completed", "failed"]:
                        return {
                            "success": True,
                            "status": simulation.status,
                            "total_trades": simulation.total_trades,
                            "profit_loss": float(simulation.total_profit_loss),
                            "error": None
                        }
                    return {
                        "success": False,
                        "status": simulation.status,
                        "total_trades": simulation.total_trades,
                        "profit_loss": float(simulation.total_profit_loss),
                        "error": f"Simulation is not in pending status (current: {simulation.status})"
                    }

                # 运行模拟
                logger.info(f"Running simulation {simulation_id} for {simulation.symbol}")
                simulation = await trading_engine.run_simulation(db, simulation)
                await db.commit()

                logger.info(
                    f"Simulation {simulation_id} completed with status: {simulation.status}, "
                    f"trades: {simulation.total_trades}, P/L: {simulation.total_profit_loss}"
                )

                return {
                    "success": simulation.status == "completed",
                    "status": simulation.status,
                    "total_trades": simulation.total_trades,
                    "profit_loss": float(simulation.total_profit_loss),
                    "error": simulation.error_message
                }

        except Exception as e:
            logger.error(f"Trading simulation task failed for {simulation_id}: {e}", exc_info=True)

            # 尝试更新模拟状态为失败 (use same engine)
            try:
                async with SessionLocal() as db:
                    result = await db.execute(
                        select(TradingSimulation).where(TradingSimulation.id == sim_uuid)
                    )
                    simulation = result.scalar_one_or_none()
                    if simulation and simulation.status in ["pending", "running"]:
                        simulation.status = "failed"
                        simulation.error_message = str(e)
                        await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update simulation status: {update_error}")

            return {
                "success": False,
                "status": "failed",
                "total_trades": 0,
                "profit_loss": 0,
                "error": str(e)
            }

        finally:
            # Clean up: dispose the engine to close all connections
            await engine.dispose()

    # Run with a fresh event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_async_run())
    finally:
        loop.close()
