import os
import json
import asyncio
import requests
import websockets
import pandas as pd
from datetime import datetime
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class DerivDataProvider:
    def __init__(self):
        self.token = os.environ.get('DERIV_API_TOKEN')
        self.app_id = os.environ.get('DERIV_APP_ID')
        # Hardcoding the demo account we discovered, since we only want to test safely
        self.account_id = "DOT90734760"

    async def _fetch_candles(self, symbol: str, count: int = 1000, granularity: int = 900) -> pd.DataFrame:
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Deriv-App-ID': self.app_id,
            'Content-Type': 'application/json'
        }
        
        # 1. Fetch OTP
        resp = requests.post(f'https://api.derivws.com/trading/v1/options/accounts/{self.account_id}/otp', headers=headers)
        resp.raise_for_status()
        ws_url = resp.json()['data']['url']
        
        # 2. Connect to WS
        async with websockets.connect(ws_url) as ws:
            req = {
                "ticks_history": symbol,
                "end": "latest",
                "count": count,
                "granularity": granularity,
                "style": "candles"
            }
            await ws.send(json.dumps(req))
            response = await ws.recv()
            data = json.loads(response)
            
            if 'error' in data:
                logger.error(f"Error fetching data for {symbol}: {data['error']}")
                return pd.DataFrame()
                
            candles = data.get('candles', [])
            if not candles:
                logger.warning(f"No candles returned for {symbol}")
                return pd.DataFrame()
                
            # 3. Format DataFrame
            df = pd.DataFrame(candles)
            df['Datetime'] = pd.to_datetime(df['epoch'], unit='s')
            df.set_index('Datetime', inplace=True)
            df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close'}, inplace=True)
            # Deriv doesn't provide Volume for these instruments, mock it so indicators don't crash
            df['Volume'] = 1000.0
            
            # Reorder columns
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
            return df

    def fetch_data(self, symbol: str, period: str = '60d', interval: str = '15m') -> pd.DataFrame:
        """
        Synchronous wrapper to match existing pipeline architecture.
        """
        # interval '15m' -> 900 seconds
        granularity = 900
        if interval == '5m': granularity = 300
        elif interval == '1h': granularity = 3600
        elif interval == '1d': granularity = 86400
        
        # Request a large enough count to ensure SMA 200 works
        count = 1000
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        df = loop.run_until_complete(self._fetch_candles(symbol, count, granularity))
        loop.close()
        return df
