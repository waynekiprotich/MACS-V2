import asyncio
import json
import websockets

async def check_symbols():
    url = "wss://ws.binaryws.com/websockets/v3?app_id=1089"
    async with websockets.connect(url) as ws:
        req = {"authorize": "pat_f3fbd035125d8f010235e2b305b54e50167b8bec6f2c2837ab5dac7a27feb9eb"}
        await ws.send(json.dumps(req))
        response = await ws.recv()
        data = json.loads(response)
        print(data)

asyncio.run(check_symbols())
