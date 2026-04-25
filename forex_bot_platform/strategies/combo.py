"""Combo strategy placeholder: combines Breakout and TrendFollower."""
from .breakout import Breakout
from .trend_follower import TrendFollower

class Combo(Breakout, TrendFollower):
    def __init__(self, **kwargs):
        Breakout.__init__(self, lookback=2)
        TrendFollower.__init__(self, short=12, long=26)
        self.name = "Combo"

    def generate_signal(self, data: pd.DataFrame) -> int:
        s1 = Breakout.generate_signal(self, data)
        s2 = TrendFollower.generate_signal(self, data)
        # Require both signals align for a stronger confirmation
        if s1 == 1 and s2 == 1:
            return 1
        if s1 == -1 or s2 == -1:
            return -1
        return 0
