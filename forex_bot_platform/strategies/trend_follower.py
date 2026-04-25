"""Trend follower strategy placeholder."""
from .base import Strategy
import pandas as pd

class TrendFollower(Strategy):
    def __init__(self, short=12, long=26):
        super().__init__("TrendFollower", short=short, long=long)
        self._last_cross = 0

    def generate_signal(self, data: pd.DataFrame) -> int:
        if data is None or len(data) < self.params["long"]:
            return 0
        closes = data["close"]
        ema_fast = closes.ewm(span=self.params["short"], adjust=False).mean()
        ema_slow = closes.ewm(span=self.params["long"], adjust=False).mean()
        cross = 1 if (ema_fast.iloc[-1] > ema_slow.iloc[-1] and ema_fast.iloc[-2] <= ema_slow.iloc[-2]) else -1 if (ema_fast.iloc[-1] < ema_slow.iloc[-1] and ema_fast.iloc[-2] >= ema_slow.iloc[-2]) else 0
        if cross != 0:
            self._last_cross = cross
        return self._last_cross
