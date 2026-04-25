"""Mean reversion strategy placeholder."""
from .base import Strategy
import pandas as pd

class MeanReversion(Strategy):
    def __init__(self, window: int = 20, rsi_threshold: float = 30.0):
        super().__init__("MeanReversion", window=window, rsi_threshold=rsi_threshold)

    def generate_signal(self, data: pd.DataFrame) -> int:
        if data is None or len(data) < self.params["window"]:
            return 0
        # RSI-based trading signal
        window = self.params["window"]
        deltas = data["close"].diff()
        seed = deltas[:1+window]
        up = deltas.clip(lower=0)
        down = -deltas.clip(upper=0)
        roll_up = up.rolling(window=window).mean()
        roll_down = down.rolling(window=window).mean()
        rs = roll_up / (roll_down + 1e-6)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        last_rsi = float(rsi.iloc[-1]) if not rsi.empty else 50.0
        if last_rsi < self.params["rsi_threshold"]:
            return 1
        if last_rsi > 100 - self.params["rsi_threshold"]:
            return -1
        return 0
