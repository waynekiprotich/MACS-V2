import pytest
from core.risk_management import RiskManager
from core.scoring import get_ai_analysis
import pandas as pd
from unittest.mock import patch, MagicMock

def test_risk_consecutive_losses(monkeypatch):
    manager = RiskManager(db_path=":memory:")
    # We need to manually inject these into the manager to simulate the state
    import datetime
    manager.cooldown_until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=4)
    status = manager.can_trade()
    assert status['allowed'] == False
    assert "Circuit breaker" in status['reason']

@patch("core.scoring.genai.GenerativeModel.generate_content")
def test_ai_fallback_on_429(mock_generate):
    from google.api_core.exceptions import GoogleAPIError
    mock_generate.side_effect = GoogleAPIError("429 Quota exceeded")
    
    df = pd.DataFrame({'Close': [100], 'Regime': ['bullish']})
    score = get_ai_analysis(df)
    assert score is None
