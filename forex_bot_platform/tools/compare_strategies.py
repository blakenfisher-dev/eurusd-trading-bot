"""Compare multiple strategies on a dataset (lightweight)."""
from forex_bot_platform.backtesting.engine import run_backtest
from forex_bot_platform.strategies.base import Strategy
from forex_bot_platform.strategies.breakout import Breakout
import pandas as pd

def compare_strategies(data: pd.DataFrame, strategy_classes=None):
    if strategy_classes is None:
        strategy_classes = [Breakout()]
    results = {}
    for strat in strategy_classes:
        result = run_backtest(data, strat)
        results[strat.name] = result.get("metrics", {})
    return results
