"""Placeholder SuperTrend strategy."""
from .base import Strategy
import pandas as pd

class SuperTrend(Strategy):
    def __init__(self, period: int = 10, multiplier: float = 3.0):
        super().__init__("SuperTrend", period=period, multiplier=multiplier)
        self._prev_signal = 0

    def _atr(self, series: pd.DataFrame, period: int) -> pd.Series:
        highs = series["high"]
        lows = series["low"]
        closes = series["close"]
        tr = pd.concat([
            (highs - lows).to_frame(name="tr1"),
            (highs - closes.shift(1)).abs().to_frame(name="tr2"),
            (lows - closes.shift(1)).abs().to_frame(name="tr3"),
        ], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def generate_signal(self, data: pd.DataFrame) -> int:
        if data is None or len(data) < self.params["period"] + 1:
            return 0
        series = data[-(self.params["period"] + 1):]
        atr = self._atr(series, self.params["period"])
        hl2 = (series["high"] + series["low"]) / 2.0
        upper = hl2 - self.params["multiplier"] * atr
        lower = hl2 + self.params["multiplier"] * atr
        last_close = series.iloc[-1]["close"]
        upper_last = upper.iloc[-1]
        lower_last = lower.iloc[-1]
        if last_close > upper_last:
            self._prev_signal = 1
            return 1
        if last_close < lower_last:
            self._prev_signal = -1
            return -1
        return self._prev_signal
