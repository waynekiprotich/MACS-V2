import os
import json
import asyncio
import requests
import websockets
import logging
from execution.base import BaseEngine
from models.database import SessionLocal, PaperTrade
from core.notifications import send_discord_signal

logger = logging.getLogger(__name__)

class DerivEngine(BaseEngine):
    def __init__(self):
        super().__init__()
        self.token = os.environ.get('DERIV_API_TOKEN')
        self.app_id = os.environ.get('DERIV_APP_ID')
        self.account_id = "DOT90734760"

    async def _execute_contract(self, symbol: str, signal: str, quantity: float):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Deriv-App-ID': self.app_id,
            'Content-Type': 'application/json'
        }
        
        # 1. Fetch OTP
        resp = requests.post(f'https://api.derivws.com/trading/v1/options/accounts/{self.account_id}/otp', headers=headers)
        resp.raise_for_status()
        ws_url = resp.json()['data']['url']
        
        async with websockets.connect(ws_url) as ws:
            contract_type = "CALL" if signal.upper() == "BUY" else "PUT"
            
            # 2. Get Proposal
            proposal_req = {
                "proposal": 1,
                "amount": quantity,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": 15,
                "duration_unit": "m",
                "underlying_symbol": symbol
            }
            await ws.send(json.dumps(proposal_req))
            response = json.loads(await ws.recv())
            
            if 'error' in response:
                logger.error(f"Deriv Proposal Error: {response['error']}")
                return None
                
            proposal_id = response['proposal']['id']
            payout = response['proposal']['payout']
            logger.info(f"Deriv Proposal ID: {proposal_id}, Payout: {payout}")
            
            # 3. Buy Contract
            buy_req = {
                "buy": proposal_id,
                "price": quantity
            }
            await ws.send(json.dumps(buy_req))
            buy_response = json.loads(await ws.recv())
            
            if 'error' in buy_response:
                logger.error(f"Deriv Buy Error: {buy_response['error']}")
                return None
                
            contract_id = buy_response['buy']['contract_id']
            buy_price = buy_response['buy']['buy_price']
            logger.info(f"Deriv Execution Success! Contract ID: {contract_id}, Price: {buy_price}")
            
            return {
                "contract_id": contract_id,
                "buy_price": buy_price,
                "contract_type": contract_type
            }

    def execute_signal(self, symbol: str, signal: str, quantity: float, price: float, reason: str = "") -> dict:
        """
        Synchronous wrapper to execute a contract and log it.
        """
        if signal.upper() not in ('BUY', 'SELL'):
            return {"status": "ignored"}
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self._execute_contract(symbol, signal, quantity))
        loop.close()
        
        if not result:
            return {"status": "error", "message": "Failed to purchase Deriv contract"}
            
        # Log to DB
        db = SessionLocal()
        try:
            trade = PaperTrade(
                symbol=symbol,
                side=signal.upper(),
                quantity=quantity,
                price=result['buy_price'], # Use the actual stake charged
                status="closed",  # We log options as closed immediately for simplicity, or "open" if we track them
                reason=reason
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            
            # Send Discord Alert
            send_discord_signal(
                symbol=symbol,
                side=signal.upper(),
                price=result['buy_price'],
                strategy="Deriv Engine",
                ai_score=None,
                notes=f"{reason} | Contract: {result['contract_id']}"
            )
            
            return {"status": "success", "trade_id": trade.id, "contract_id": result['contract_id']}
        except Exception as e:
            logger.error(f"Failed to log Deriv trade: {e}")
            db.rollback()
            return {"status": "error"}
        finally:
            db.close()

    def get_positions(self) -> list:
        return []

    def get_account_summary(self) -> dict:
        return {"balance": 0.0}
