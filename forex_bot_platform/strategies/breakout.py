"""Simple Breakout strategy placeholder."""
from .base import Strategy
import pandas as pd

class Breakout(Strategy):
    def __init__(self, lookback: int = 2):
        super().__init__("Breakout", lookback=lookback)

    def generate_signal(self, data: pd.DataFrame) -> int:
        if data is None or len(data) < 2:
            return 0
        # Breakout against the immediately preceding candle range
        prev = data.iloc[-2]
        curr = data.iloc[-1]
        prev_high = prev["high"]
        prev_low = prev["low"]
        close = curr["close"]
        if close > prev_high:
            return 1
        if close < prev_low:
            return -1
        return 0
