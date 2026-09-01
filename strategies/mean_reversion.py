import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MeanReversionStrategy:
    """
    Catch RSI extremes at Bollinger Bands for quick scalps.
    """
    def __init__(self, rsi_overbought: float = 70.0, rsi_oversold: float = 30.0):
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    def generate_signal(self, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expects current_data to have:
        - close
        - rsi
        - bb_upper
        - bb_lower
        """
        try:
            close = current_data.get('close', 0.0)
            rsi = current_data.get('rsi', 50.0)
            bb_upper = current_data.get('bb_upper', 0.0)
            bb_lower = current_data.get('bb_lower', 0.0)
            
            signal_type = "NEUTRAL"
            
            if rsi < self.rsi_oversold and close <= bb_lower:
                signal_type = "BUY"
            elif rsi > self.rsi_overbought and close >= bb_upper:
                signal_type = "SELL"
                
            return {
                "strategy": "MeanReversion",
                "signal": signal_type,
                "metadata": current_data
            }
            
        except Exception as e:
            logger.error(f"Error generating signal in MeanReversionStrategy: {e}")
            return {
                "strategy": "MeanReversion",
                "signal": "ERROR",
                "error": str(e)
            }
