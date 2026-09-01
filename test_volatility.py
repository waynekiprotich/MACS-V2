import pandas as pd
import numpy as np
from core.regime import detect_regime
from core.signal_combiner import combine_signals
from core.pipeline import TradingPipeline

# Create mock data
data = {
    'Close': [150, 155, 160, 165] * 10,
    'SMA_50': [100, 105, 110, 115] * 10,
    'SMA_200': [80, 85, 90, 95] * 10,
    'ATR_14': [1.0] * 39 + [10.0],  # Last row has extreme volatility to trigger Is_Volatile
    'Tech_Score': [90.0] * 40 # Strong BUY
}
df = pd.DataFrame(data)

# Run regime
df_regime = detect_regime(df)

# Run signal combiner
df_signals = combine_signals(df_regime)

last_row = df_signals.iloc[-1]
print(f"Regime: {last_row['Regime']}, Tech_Score: {last_row['Tech_Score']}, Is_Volatile: {last_row['Is_Volatile']}")
print(f"Final Signal out of signal_combiner.py: {last_row['Signal']}")

