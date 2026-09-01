import pytest
from unittest.mock import patch, MagicMock
from core.notifications import send_discord_signal
from core.risk_management import RiskManager
from models.database import init_db

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    init_db()

@patch('core.notifications.requests.post')
def test_send_discord_signal(mock_post):
    """Test that discord signal webhook fires with correct payload."""
    from config.settings import settings
    settings.DISCORD_WEBHOOK_URL = "https://mock.discord.com/webhook"
    
    mock_post.return_value.status_code = 200
    
    send_discord_signal(
        symbol="SPY",
        side="BUY",
        price=500.0,
        strategy="TestStrat",
        ai_score=8.5,
        notes="Test note"
    )
    
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert kwargs['timeout'] == 5.0
    payload = kwargs['json']
    assert payload['username'] == "MACS-V2 Bot"
    assert "SPY" in payload['embeds'][0]['title']

def test_risk_manager_state():
    """Test that risk manager initializes safely without locking the database."""
    rm = RiskManager()
    
    # Check that defaults loaded
    assert rm.max_daily_loss == -500.0
    assert rm.consecutive_loss_limit == 3
    
    # Test can_trade logic
    status = rm.can_trade()
    assert status['allowed'] == True

    # Manually trigger consecutive losses to trigger circuit breaker
    rm.update_trade_result(-100.0)
    rm.update_trade_result(-100.0)
    rm.update_trade_result(-100.0)
    
    status = rm.can_trade()
    assert status['allowed'] == False
    assert "Circuit breaker active" in status['reason']
