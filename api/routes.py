import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from models.schemas import Signal, Risk, Trade, Position, ExecuteRequest, ExecuteResponse
from models.database import get_db, PaperTrade
from config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/signals", response_model=List[Signal])
def get_signals():
    try:
        # Returning static signals as a base for future integration
        return [
            Signal(symbol="AAPL", action="BUY", confidence_score=0.85, reasoning="Strong uptrend detected.")
        ]
    except Exception as e:
        logger.error(f"Error fetching signals: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/risk", response_model=Risk)
def get_risk(symbol: str):
    try:
        if not symbol:
            raise HTTPException(status_code=400, detail="Symbol is required")
        # Returning static risk data as a base for future integration
        return Risk(
            symbol=symbol,
            risk_level="MEDIUM",
            max_position_size=10.0,
            stop_loss_price=150.0,
            take_profit_price=170.0,
            warnings=["Market volatility is high."]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating risk for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/trades", response_model=List[Trade])
def get_trades(db: Session = Depends(get_db)):
    try:
        trades = db.query(PaperTrade).order_by(PaperTrade.timestamp.desc()).limit(100).all()
        return [
            Trade(
                symbol=t.symbol,
                side=t.side,
                quantity=t.quantity,
                price=t.price,
                status=t.status,
                order_id=t.order_id,
                reason=t.reason,
                timestamp=t.timestamp
            ) for t in trades
        ]
    except Exception as e:
        logger.error(f"Error fetching trades: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/positions", response_model=List[Position])
def get_positions():
    try:
        # Returning static position data as a base for future integration
        return [
            Position(
                symbol="AAPL",
                quantity=5.0,
                avg_entry_price=155.0,
                current_price=160.0,
                unrealized_pl=25.0,
                unrealized_pl_pc=0.032
            )
        ]
    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/execute", response_model=ExecuteResponse)
def execute_trade(request: ExecuteRequest, db: Session = Depends(get_db)):
    try:
        if request.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")
        
        mock_price = 150.0
        
        new_trade = PaperTrade(
            symbol=request.symbol,
            side=request.action,
            quantity=request.quantity,
            price=mock_price,
            status="executed",
            order_id=f"mock_order_{request.symbol}_{request.action}",
            reason=request.reason
        )
        db.add(new_trade)
        db.commit()
        db.refresh(new_trade)
        
        logger.info(f"Executed {request.action} for {request.quantity} shares of {request.symbol}")
        
        trade_model = Trade(
            symbol=new_trade.symbol,
            side=new_trade.side,
            quantity=new_trade.quantity,
            price=new_trade.price,
            status=new_trade.status,
            order_id=new_trade.order_id,
            reason=new_trade.reason,
            timestamp=new_trade.timestamp
        )
        
        return ExecuteResponse(
            status="success",
            message=f"Successfully executed {request.action} for {request.symbol}",
            trade=trade_model
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
