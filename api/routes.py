import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any

from models.schemas import Signal, Risk, Trade, Position, ExecuteRequest, ExecuteResponse
from models.database import get_db, PaperTrade
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/signals", response_model=List[Signal])
def get_signals():
    return []

@router.get("/risk", response_model=Risk)
def get_risk(symbol: str = "ALL"):
    return Risk(
        symbol=symbol,
        risk_level="NORMAL",
        max_position_size=10.0,
        warnings=[]
    )

@router.get("/trades")
def get_trades(db: Session = Depends(get_db)):
    try:
        trades = db.query(PaperTrade).order_by(PaperTrade.timestamp.desc()).limit(100).all()
        return trades
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/positions", response_model=List[Position])
def get_positions():
    return []

@router.get("/performance")
def get_performance(db: Session = Depends(get_db)):
    try:
        trades = db.query(PaperTrade).all()
        total_trades = len(trades)
        wins = sum(1 for t in trades if t.pnl and t.pnl > 0)
        losses = sum(1 for t in trades if t.pnl and t.pnl < 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0.0
        total_pnl = sum((t.pnl or 0) for t in trades)
        
        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "today_pnl": total_pnl, # Simplify for now
            "consecutive_losses": 0,
            "skipped_trades": 0
        }
    except Exception as e:
        logger.error(f"Error fetching performance: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
