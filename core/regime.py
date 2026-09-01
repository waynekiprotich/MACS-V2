import pandas as pd
import logging

logger = logging.getLogger(__name__)

def detect_regime(df: pd.DataFrame) -> pd.DataFrame:
    """Detect market regime."""
    if df.empty or 'SMA_50' not in df.columns or 'SMA_200' not in df.columns or 'ATR_14' not in df.columns:
        logger.warning("Required indicators missing for regime detection")
        return df

    df = df.copy()
    try:
        df['Regime'] = 'bearish'
        
        # Trend conditions
        bullish_condition = (df['Close'] > df['SMA_50']) & (df['Close'] > df['SMA_200']) & (df['SMA_50'] > df['SMA_200'])
        bearish_condition = (df['Close'] < df['SMA_50']) & (df['Close'] < df['SMA_200']) & (df['SMA_50'] < df['SMA_200'])
        
        df.loc[bullish_condition, 'Regime'] = 'bullish'
        df.loc[bearish_condition, 'Regime'] = 'bearish'
        
        # Volatility condition (separate flag, so it doesn't mask the regime)
        avg_atr = df['ATR_14'].rolling(window=20).mean()
        df['Is_Volatile'] = df['ATR_14'] > (1.3 * avg_atr)
        
        df.dropna(inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error detecting regime: {e}")
        return df
