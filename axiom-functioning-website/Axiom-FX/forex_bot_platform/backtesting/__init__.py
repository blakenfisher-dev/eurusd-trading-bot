"""Backtesting module."""
from forex_bot_platform.backtesting.engine import BacktestEngine, BacktestResult, Trade
from forex_bot_platform.backtesting.metrics import (
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_profit_factor,
    format_metrics
)

__all__ = [
    "BacktestEngine",
    "BacktestResult", 
    "Trade",
    "calculate_sharpe_ratio",
    "calculate_sortino_ratio",
    "calculate_max_drawdown",
    "calculate_win_rate",
    "calculate_profit_factor",
    "format_metrics",
]