import pandas as pd
import logging
import json
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

from config.settings import settings

logger = logging.getLogger(__name__)

def calculate_technical_score(row: pd.Series) -> float:
    """Calculate technical score 0-10 based on trend, RSI, MACD, volume."""
    score = 5.0
    
    try:
        if row.get('Regime') == 'bullish':
            score += 2
        elif row.get('Regime') == 'bearish':
            score -= 2
            
        rsi = row.get('RSI_14', 50)
        if rsi < 30:
            score += 1.5
        elif rsi > 70:
            score -= 1.5
            
        macd_diff = row.get('MACD_diff', 0)
        if macd_diff > 0:
            score += 1
        else:
            score -= 1
            
        vol = row.get('Volume', 0)
        vol_sma = row.get('Volume_SMA_20', 1)
        if vol > vol_sma:
            if score > 5:
                score += 0.5
            elif score < 5:
                score -= 0.5
                
        return max(0.0, min(100.0, score * 10))
    except Exception as e:
        logger.error(f"Error calculating technical score: {e}")
        return 50.0

def get_ai_analysis(context_df: pd.DataFrame) -> float:
    """Uses Gemini API for market sentiment scoring, returning a score from 0-10."""
    api_key = settings.GEMINI_API_KEY
    if not api_key:
        logger.warning("GEMINI_API_KEY not set. Defaulting AI score to 0.")
        return 0.0

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-3.6-flash')
        
        # Prepare context (last 10 rows)
        data_str = context_df.tail(10).to_csv(index=False)
        prompt = f"Analyze this recent market data and provide a bullishness score from 0 to 10. Only reply with a number.\n\nData:\n{data_str}"
        
        import concurrent.futures
        
        import threading
        
        result = [None]
        def _call_api():
            try:
                result[0] = model.generate_content(prompt, request_options={"timeout": 45.0})
            except Exception as e:
                result[0] = e
                
        thread = threading.Thread(target=_call_api, daemon=True)
        thread.start()
        thread.join(timeout=45.0)
        
        if thread.is_alive():
            logger.warning("Gemini API Timeout: 45s deadline exceeded. Defaulting AI score to 0.")
            return 0.0
            
        if isinstance(result[0], Exception):
            raise result[0]
            
        response = result[0]
        score_text = response.text.strip()
        
        # Extract number
        import re
        match = re.search(r'([0-9.]+)', score_text)
        if match:
            return min(100.0, max(0.0, float(match.group(1)) * 10))
        return 0.0
        
    except concurrent.futures.TimeoutError:
        logger.warning("Gemini API Timeout: 45s deadline exceeded. Defaulting AI score to 0.")
        return 0.0
    except GoogleAPIError as e:
        logger.warning(f"Gemini API GoogleAPIError (auth/network): {e}. Defaulting AI score to 0.")
        return 0.0
    except Exception as e:
        logger.warning(f"Unexpected error calling Gemini API: {e}. Defaulting AI score to 0.")
        return 0.0

def score_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply scoring to dataframe."""
    if df.empty:
        return df
    
    df = df.copy()
    try:
        df['Tech_Score'] = df.apply(calculate_technical_score, axis=1)
        # Adding AI Score conditionally. We only run AI analysis on the most recent data to save tokens, 
        # but for simplicity in this implementation, we apply it to the whole DF or just default to 0 for historical.
        # Here we just set it to 0 as a baseline, and it's up to pipeline.py to call get_ai_analysis for the latest row.
        df['AI_Score'] = 0.0
        return df
    except Exception as e:
        logger.error(f"Error scoring data: {e}")
        return df
