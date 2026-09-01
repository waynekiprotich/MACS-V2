import os
import logging
from typing import Dict, Any, List
from execution.base import BaseEngine

try:
    import alpaca_trade_api as tradeapi
    from alpaca_trade_api.rest import APIError
except ImportError:
    tradeapi = None
    APIError = Exception

logger = logging.getLogger(__name__)

class AlpacaEngine(BaseEngine):
    """
    Connects to Alpaca API using python alpaca-trade-api.
    Implements BaseEngine methods. Fall back gracefully if keys missing.
    """
    def __init__(self):
        self.api_key = os.environ.get("ALPACA_API_KEY")
        self.api_secret = os.environ.get("ALPACA_API_SECRET")
        self.base_url = os.environ.get("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        self.api = None
        
        if tradeapi is None:
            logger.warning("alpaca_trade_api is not installed. AlpacaEngine will not function correctly.")
        elif not self.api_key or not self.api_secret:
            logger.warning("Alpaca API keys are missing. Running in fallback/degraded mode.")
        else:
            try:
                self.api = tradeapi.REST(
                    key_id=self.api_key,
                    secret_key=self.api_secret,
                    base_url=self.base_url,
                    api_version='v2'
                )
            except Exception as e:
                logger.error(f"Failed to initialize Alpaca REST API: {e}")
                self.api = None

    def execute_signal(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api:
            return {"status": "error", "message": "Alpaca API not initialized"}
            
        try:
            sig_type = signal.get("signal")
            if sig_type not in ["BUY", "SELL"]:
                return {"status": "skipped", "reason": f"Unhandled signal type {sig_type}"}
                
            symbol = signal.get("symbol", "AAPL")
            qty = signal.get("quantity", 1)
            
            side = "buy" if sig_type == "BUY" else "sell"
            
            order = self.api.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type='market',
                time_in_force='gtc'
            )
            
            from core.notifications import send_discord_signal
            send_discord_signal(
                symbol=symbol,
                side=side.upper(),
                price=float(signal.get('price', 0.0)),
                strategy=signal.get('strategy', 'unknown'),
                ai_score=signal.get('ai_score'),
                notes=f"Alpaca Order Submitted: {order.id}"
            )
            
            return {
                "status": "success",
                "order_id": order.id,
                "client_order_id": order.client_order_id
            }
        except APIError as e:
            logger.error(f"Alpaca API Error during execution: {e}")
            return {"status": "error", "message": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error during Alpaca execution: {e}")
            return {"status": "error", "message": str(e)}

    def get_positions(self) -> List[Dict[str, Any]]:
        if not self.api:
            return []
            
        try:
            positions = self.api.list_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": float(p.qty),
                    "market_value": float(p.market_value),
                    "unrealized_pl": float(p.unrealized_pl)
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Error fetching Alpaca positions: {e}")
            return []

    def get_account_summary(self) -> Dict[str, Any]:
        if not self.api:
            return {"status": "error", "message": "Alpaca API not initialized"}
            
        try:
            account = self.api.get_account()
            return {
                "status": account.status,
                "equity": float(account.equity),
                "cash": float(account.cash),
                "buying_power": float(account.buying_power),
                "currency": account.currency
            }
        except Exception as e:
            logger.error(f"Error fetching Alpaca account summary: {e}")
            return {"status": "error", "message": str(e)}
