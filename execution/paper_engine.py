import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from models.database import PaperTrade, SessionLocal
from execution.base import BaseEngine
from core.notifications import send_discord_signal

logger = logging.getLogger(__name__)

class PaperEngine(BaseEngine):
    """
    Logs trades to SQLite PaperTrade table.
    """
    def __init__(self):
        self.positions = []
        self.account_balance = 100000.0  # Simulated 100k starting balance
        
    def _get_db(self) -> Session:
        try:
            return SessionLocal()
        except Exception as e:
            logger.error(f"Could not create database session: {e}")
            raise

    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        try:
            side = signal.get('action') or signal.get('signal', 'NEUTRAL')
            if side in ["NEUTRAL", "ERROR", "HOLD", "hold", "neutral"]:
                return {"status": "skipped", "reason": side}
                
            symbol = signal.get('symbol', 'UNKNOWN')
            price = signal.get('price', 0.0)
            quantity = signal.get('quantity', 1.0)
            strategy = signal.get('strategy', 'unknown')
            ai_score = signal.get('ai_score')
            reason = signal.get('reason', '')
                
            db = self._get_db()
            
            trade = PaperTrade(
                symbol=symbol,
                side=side.lower(),
                quantity=quantity,
                price=price,
                status="closed",
                reason=f"{strategy}: {reason}"[:255]
            )
                
            db.add(trade)
            db.commit()
            db.refresh(trade)
            db.close()
            
            self.positions.append({
                "symbol": symbol,
                "qty": quantity,
                "side": side
            })
            
            # Send Discord notification
            send_discord_signal(
                symbol=symbol,
                side=side,
                price=price,
                strategy=strategy,
                ai_score=ai_score,
                notes="Paper Trade Executed"
            )
            
            return {"status": "success", "trade_id": getattr(trade, 'id', None)}
        except Exception as e:
            logger.error(f"Error executing paper trade: {e}")
            return {"status": "error", "message": str(e)}

    def get_positions(self) -> List[Dict[str, Any]]:
        return self.positions

    def get_account_summary(self) -> Dict[str, Any]:
        return {
            "balance": self.account_balance,
            "equity": self.account_balance,
            "currency": "USD"
        }
