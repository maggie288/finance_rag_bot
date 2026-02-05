from __future__ import annotations

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.clawdbot import (
    PolymarketMarket,
    ClawdBotOpportunity,
    ClawdBotWallet,
    ClawdBotTrade,
    ClawdBotConfig,
)
from app.services.market_data.polymarket import polymarket_provider
from app.services.market_data.clawdbot import clawd_bot_analyzer

router = APIRouter(prefix="/clawdbot", tags=["clawdbot"])


@router.get("/markets")
async def list_polymarket_markets(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
):
    """List Polymarket markets."""
    try:
        markets = await polymarket_provider.fetch_all_markets(category=category)
        return {
            "markets": markets[:limit],
            "count": len(markets),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch markets: {str(e)}")


@router.get("/markets/trending")
async def get_trending_markets(
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
):
    """Get trending Polymarket markets."""
    try:
        markets = await polymarket_provider.get_trending_markets(limit=limit)
        return {
            "markets": markets,
            "count": len(markets),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trending markets: {str(e)}")


@router.get("/opportunities")
async def list_opportunities(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List trading opportunities."""
    query = select(ClawdBotOpportunity).order_by(desc(ClawdBotOpportunity.created_at))
    
    if status:
        query = query.where(ClawdBotOpportunity.status == status)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    opportunities = result.scalars().all()

    return {
        "opportunities": [
            {
                "id": str(o.id),
                "market_id": o.market_id,
                "market_question": o.market_question,
                "opportunity_type": o.opportunity_type,
                "confidence": float(o.confidence) if o.confidence else 0,
                "signal_strength": float(o.signal_strength) if o.signal_strength else 0,
                "entry_price_yes": float(o.entry_price_yes) if o.entry_price_yes else 0,
                "entry_price_no": float(o.entry_price_no) if o.entry_price_no else 0,
                "target_price": float(o.target_price) if o.target_price else 0,
                "expected_return": float(o.expected_return) if o.expected_return else 0,
                "status": o.status,
                "created_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in opportunities
        ],
        "page": page,
        "page_size": page_size,
    }


@router.post("/scan")
async def scan_opportunities(
    user: User = Depends(get_current_user),
):
    """Scan markets for trading opportunities."""
    try:
        signals = await clawd_bot_analyzer.analyze_all_markets()
        
        return {
            "opportunities_found": len(signals),
            "signals": [
                {
                    "market_id": s.market_id,
                    "market_slug": s.market_slug,
                    "market_question": s.market_question,
                    "opportunity_type": s.opportunity_type,
                    "confidence": s.confidence,
                    "signal_strength": s.signal_strength,
                    "yes_price": float(s.yes_price),
                    "no_price": float(s.no_price),
                    "target_price": float(s.target_price),
                    "stop_loss": float(s.stop_loss),
                    "expected_return": float(s.expected_return),
                    "risk_score": float(s.risk_score),
                    "analysis": s.analysis,
                }
                for s in signals[:20]
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/trades")
async def list_trades(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's trades."""
    query = select(ClawdBotTrade).where(ClawdBotTrade.user_id == user.id)
    query = query.order_by(desc(ClawdBotTrade.opened_at))
    
    if status:
        query = query.where(ClawdBotTrade.status == status)
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    
    result = await db.execute(query)
    trades = result.scalars().all()

    total_pnl = sum([float(t.pnl) for t in trades if t.pnl])
    win_count = sum([1 for t in trades if t.pnl and float(t.pnl) > 0])
    loss_count = sum([1 for t in trades if t.pnl and float(t.pnl) <= 0])

    return {
        "trades": [
            {
                "id": str(t.id),
                "market_id": t.market_id,
                "market_slug": t.market_slug,
                "side": t.side,
                "amount_btc": float(t.amount_btc) if t.amount_btc else 0,
                "amount_usd": float(t.amount_usd) if t.amount_usd else 0,
                "entry_price": float(t.entry_price) if t.entry_price else 0,
                "pnl": float(t.pnl) if t.pnl else 0,
                "pnl_percent": float(t.pnl_percent) if t.pnl_percent else 0,
                "status": t.status,
                "opened_at": t.opened_at.isoformat() if t.opened_at else None,
            }
            for t in trades
        ],
        "page": page,
        "page_size": page_size,
        "summary": {
            "total_trades": len(trades),
            "total_pnl": total_pnl,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_count / len(trades) if trades else 0,
        },
    }


@router.post("/wallets")
async def add_wallet(
    wallet_type: str,
    wallet_name: str,
    address: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a Bitcoin wallet."""
    wallet = ClawdBotWallet(
        user_id=user.id,
        wallet_type=wallet_type,
        wallet_name=wallet_name,
        address=address,
    )
    db.add(wallet)
    await db.commit()
    await db.refresh(wallet)

    return {
        "id": str(wallet.id),
        "wallet_type": wallet.wallet_type,
        "wallet_name": wallet.wallet_name,
        "address": wallet.address,
    }


@router.get("/wallets")
async def list_wallets(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's wallets."""
    query = select(ClawdBotWallet).where(
        ClawdBotWallet.user_id == user.id,
        ClawdBotWallet.is_active == True,
    )
    
    result = await db.execute(query)
    wallets = result.scalars().all()

    return {
        "wallets": [
            {
                "id": str(w.id),
                "wallet_type": w.wallet_type,
                "wallet_name": w.wallet_name,
                "address": w.address[:20] + "..." if w.address and len(w.address) > 20 else w.address,
                "balance_btc": float(w.balance_btc) if w.balance_btc else 0,
                "balance_usd": float(w.balance_usd) if w.balance_usd else 0,
                "is_active": w.is_active,
            }
            for w in wallets
        ]
    }


@router.get("/config")
async def get_config(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user's ClawdBot configuration."""
    query = select(ClawdBotConfig).where(ClawdBotConfig.user_id == user.id)
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        return {
            "is_enabled": False,
            "auto_trade": False,
            "min_opportunity_confidence": 0.7,
            "max_position_size_btc": 0.01,
            "max_daily_loss_btc": 0.05,
        }

    return {
        "is_enabled": config.is_enabled,
        "auto_trade": config.auto_trade,
        "min_opportunity_confidence": float(config.min_opportunity_confidence) if config.min_opportunity_confidence else 0.7,
        "max_position_size_btc": float(config.max_position_size_btc) if config.max_position_size_btc else 0.01,
        "max_daily_loss_btc": float(config.max_daily_loss_btc) if config.max_daily_loss_btc else 0.05,
        "selected_markets": config.selected_markets,
        "excluded_categories": config.excluded_categories,
        "telegram_notify": config.telegram_notify,
    }


@router.post("/config")
async def update_config(
    is_enabled: Optional[bool] = None,
    auto_trade: Optional[bool] = None,
    min_opportunity_confidence: Optional[float] = None,
    max_position_size_btc: Optional[float] = None,
    max_daily_loss_btc: Optional[float] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user's ClawdBot configuration."""
    query = select(ClawdBotConfig).where(ClawdBotConfig.user_id == user.id)
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if not config:
        config = ClawdBotConfig(user_id=user.id)
        db.add(config)

    if is_enabled is not None:
        config.is_enabled = is_enabled
    if auto_trade is not None:
        config.auto_trade = auto_trade
    if min_opportunity_confidence is not None:
        config.min_opportunity_confidence = Decimal(str(min_opportunity_confidence))
    if max_position_size_btc is not None:
        config.max_position_size_btc = Decimal(str(max_position_size_btc))
    if max_daily_loss_btc is not None:
        config.max_daily_loss_btc = Decimal(str(max_daily_loss_btc))

    await db.commit()
    await db.refresh(config)

    return {"status": "updated"}
