import requests
import json
import asyncio
import websockets
import os
from dotenv import load_dotenv

load_dotenv()
token = os.environ['DERIV_API_TOKEN']
app_id = os.environ['DERIV_APP_ID']
account_id = "DOT90734760"

async def test_deriv():
    headers = {
        'Authorization': f'Bearer {token}',
        'Deriv-App-ID': app_id,
        'Content-Type': 'application/json'
    }

    resp = requests.post(f'https://api.derivws.com/trading/v1/options/accounts/{account_id}/otp', headers=headers)
    ws_url = resp.json()['data']['url']
    
    async with websockets.connect(ws_url) as ws:
        for sym in ["OTC_DJI", "frxXAUUSD"]:
            print(f"\n--- {sym} Contracts ---")
            await ws.send(json.dumps({"contracts_for": sym}))
            response = await ws.recv()
            data = json.loads(response)
            available = data.get('contracts_for', {}).get('available', [])
            for c in available:
                if c['contract_type'] in ('CALL', 'PUT'):
                    print(f"{c['contract_type']} | Expiry: {c['expiry_type']:8s} | Min: {c.get('min_contract_duration'):4s} | Max: {c.get('max_contract_duration')}")

asyncio.run(test_deriv())
