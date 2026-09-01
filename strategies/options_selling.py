import logging
from typing import Dict, Any
import pandas as pd

logger = logging.getLogger(__name__)

class OptionsSellingStrategy:
    """
    Put credit spreads ~15 delta, 7 DTE.
    """
    def __init__(self, target_delta: float = 0.15, target_dte: int = 7):
        self.target_delta = target_delta
        self.target_dte = target_dte

    def generate_signal(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expects current_data to have options chain info:
        - underlying_price
        - puts: list of dicts with 'strike', 'delta', 'dte', 'bid', 'ask'
        """
        try:
            puts = current_data.get('puts', [])
            
            if not isinstance(puts, list):
                return {
                    "strategy": "OptionsSelling",
                    "signal": "ERROR",
                    "error": "Puts must be a list"
                }
            
            # Filter by DTE roughly matching target
            valid_puts = [p for p in puts if isinstance(p, dict) and abs(p.get('dte', 0) - self.target_dte) <= 2]
            
            if not valid_puts:
                return {
                    "strategy": "OptionsSelling",
                    "signal": "NEUTRAL",
                    "reason": "No valid options matching DTE criteria"
                }
                
            # Find closest delta (using absolute value as put deltas are negative)
            closest_put = min(valid_puts, key=lambda x: abs(abs(x.get('delta', 1.0)) - self.target_delta))
            
            if abs(closest_put.get('delta', 1.0)) > 0.3:
                 return {
                    "strategy": "OptionsSelling",
                    "signal": "NEUTRAL",
                    "reason": "Delta too far from target"
                }
                
            # Select long leg for credit spread (e.g., 1 strike below short put)
            short_strike = closest_put.get('strike')
            lower_puts = [p for p in valid_puts if p.get('strike') < short_strike]
            
            if not lower_puts:
                return {
                    "strategy": "OptionsSelling",
                    "signal": "NEUTRAL",
                    "reason": "Cannot form credit spread, no lower strikes available"
                }
                
            long_put = max(lower_puts, key=lambda x: x.get('strike'))
            
            return {
                "strategy": "OptionsSelling",
                "signal": "SELL_PUT_SPREAD",
                "short_leg": closest_put,
                "long_leg": long_put,
                "metadata": current_data
            }
            
        except Exception as e:
            logger.error(f"Error generating signal in OptionsSellingStrategy: {e}")
            return {
                "strategy": "OptionsSelling",
                "signal": "ERROR",
                "error": str(e)
            }
