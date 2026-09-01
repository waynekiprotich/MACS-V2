import pytest
from strategies.ultra_filtered import UltraFilteredStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.options_selling import OptionsSellingStrategy

def test_ultra_filtered_strategy():
    strategy = UltraFilteredStrategy()
    
    # Test data that passes all 8 conditions
    bullish_data = {
        "close": 100.0,
        "regime": "bull",
        "sma_short": 50,
        "sma_long": 40,
        "rsi": 55,
        "stoch_k": 75,
        "stoch_d": 70,
        "volume": 1500,
        "volume_sma": 1000,
        "support_level": 90.0,
        "macd": 1.5,
        "macd_signal": 1.0,
        "ai_confidence": 0.8,
        "atr": 2.0
    }
    
    signal = strategy.generate_signal(bullish_data)
    assert signal["strategy"] == "UltraFiltered"
    assert signal["signal"] == "BUY"
    assert signal["take_profit"] == 100.0 + (2.0 * 0.4)
    assert signal["stop_loss"] == 100.0 - (2.0 * 3.0)
    assert signal["conditions_met"] == 8

def test_ultra_filtered_strategy_neutral():
    strategy = UltraFilteredStrategy()
    
    # Fails most conditions
    bearish_data = {
        "close": 100.0,
        "regime": "bear",
        "sma_short": 40,
        "sma_long": 50,
        "rsi": 20,
        "stoch_k": 20,
        "stoch_d": 30,
        "volume": 500,
        "volume_sma": 1000,
        "support_level": 110.0,
        "macd": -1.5,
        "macd_signal": -1.0,
        "ai_confidence": 0.3,
        "atr": 2.0
    }
    
    signal = strategy.generate_signal(bearish_data)
    assert signal["signal"] == "NEUTRAL"

def test_mean_reversion_strategy():
    strategy = MeanReversionStrategy()
    
    # Oversold at lower BB
    buy_data = {
        "close": 90.0,
        "rsi": 25.0,
        "bb_lower": 95.0,
        "bb_upper": 110.0
    }
    signal = strategy.generate_signal(buy_data)
    assert signal["signal"] == "BUY"
    
    # Overbought at upper BB
    sell_data = {
        "close": 115.0,
        "rsi": 75.0,
        "bb_lower": 95.0,
        "bb_upper": 110.0
    }
    signal = strategy.generate_signal(sell_data)
    assert signal["signal"] == "SELL"
    
    # Middle of range
    neutral_data = {
        "close": 100.0,
        "rsi": 50.0,
        "bb_lower": 90.0,
        "bb_upper": 110.0
    }
    signal = strategy.generate_signal(neutral_data)
    assert signal["signal"] == "NEUTRAL"

def test_options_selling_strategy():
    strategy = OptionsSellingStrategy(target_delta=0.15, target_dte=7)
    
    data = {
        "underlying_price": 100.0,
        "puts": [
            {"strike": 90.0, "delta": -0.16, "dte": 7, "bid": 1.0, "ask": 1.1},
            {"strike": 85.0, "delta": -0.05, "dte": 7, "bid": 0.5, "ask": 0.6}
        ]
    }
    
    signal = strategy.generate_signal(data)
    assert signal["signal"] == "SELL_PUT_SPREAD"
    assert signal["short_leg"]["strike"] == 90.0
    assert signal["long_leg"]["strike"] == 85.0

def test_options_selling_strategy_error_handling():
    strategy = OptionsSellingStrategy()
    
    # Missing puts data should be neutral due to no valid options
    signal = strategy.generate_signal({})
    assert signal["signal"] == "NEUTRAL"
