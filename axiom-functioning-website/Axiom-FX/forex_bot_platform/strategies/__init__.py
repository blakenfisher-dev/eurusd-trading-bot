"""Strategies module."""
from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal
from forex_bot_platform.strategies.breakout import BreakoutStrategy
from forex_bot_platform.strategies.supertrend import SuperTrendStrategy
from forex_bot_platform.strategies.trend_follower import TrendFollowerStrategy
from forex_bot_platform.strategies.mean_reversion import MeanReversionStrategy
from forex_bot_platform.strategies.combo import ComboStrategy

__all__ = [
    "BaseStrategy",
    "TradingSignal",
    "BreakoutStrategy",
    "SuperTrendStrategy", 
    "TrendFollowerStrategy",
    "MeanReversionStrategy",
    "ComboStrategy",
]