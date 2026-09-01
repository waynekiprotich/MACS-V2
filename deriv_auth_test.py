import requests
import json
import asyncio
import websockets

token = "pat_f3fbd035125d8f010235e2b305b54e50167b8bec6f2c2837ab5dac7a27feb9eb"
app_id = "34hlMxQPWXPlcKfXUKfe0"
account_id = "DOT90734760"

async def check_symbols():
    headers = {
        'Authorization': f'Bearer {token}',
        'Deriv-App-ID': app_id,
        'Content-Type': 'application/json'
    }

    resp = requests.post(f'https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp', headers=headers)
    ws_url = resp.json()['data']['url']
    
    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps({"active_symbols": "brief"}))
        response = await ws.recv()
        data = json.loads(response)
        symbols = data.get('active_symbols', [])
        
        for sym in symbols:
            name = sym['underlying_symbol_name'].lower()
            symbol = sym['underlying_symbol']
            if 'gold' in name or 'xau' in symbol.lower():
                print(f"FOUND GOLD: {sym['underlying_symbol_name']} -> {symbol}")
            if 'us ' in name or 'wall' in name or '30' in name or 'dow' in name:
                print(f"FOUND USA: {sym['underlying_symbol_name']} -> {symbol}")
            if 'tech' in name or 'spx' in name or '100' in name or '500' in name:
                print(f"FOUND USA-RELATED: {sym['underlying_symbol_name']} -> {symbol}")

asyncio.run(check_symbols())
