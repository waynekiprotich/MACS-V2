import pytest
from unittest.mock import patch, MagicMock
from execution.deriv_engine import DerivEngine

class MockWS:
    async def __aenter__(self): return self
    async def __aexit__(self, exc_type, exc, tb): pass
    async def send(self, data): pass
    async def recv(self):
        if not hasattr(self, 'called_once'):
            self.called_once = True
            return '{"proposal": {"id": "prop123", "payout": 18.0}}'
        return '{"buy": {"contract_id": "cont123", "buy_price": 10.0}}'

def mock_connect(*args, **kwargs):
    return MockWS()

def test_execute_contract_success(monkeypatch):
    import websockets
    monkeypatch.setattr(websockets, "connect", mock_connect)
    
    import requests
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"data": {"url": "wss://fake"}}
    monkeypatch.setattr(requests, "post", lambda *a, **kw: mock_resp)
    
    engine = DerivEngine()
    engine.token = "fake"
    engine.app_id = "fake"
    
    with patch("execution.deriv_engine.SessionLocal") as mock_db, \
         patch("execution.deriv_engine.send_discord_signal") as mock_discord:
        result = engine.execute_signal("OTC_DJI", "BUY", 10.0, 100.0, "Test Reason")
        assert result['status'] == 'success'
        assert result['contract_id'] == 'cont123'
        mock_discord.assert_called_once()
        mock_db.return_value.add.assert_called_once()
