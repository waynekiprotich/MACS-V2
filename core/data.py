import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def fetch_data(symbol: str, period: str = "60d", interval: str = "15m") -> pd.DataFrame:
    """Fetch 60d of 15m data using yfinance."""
    logger.info(f"Fetching data for {symbol} with period {period} and interval {interval}")
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            logger.warning(f"No data returned for {symbol}")
            return df
        
        df.dropna(inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()
