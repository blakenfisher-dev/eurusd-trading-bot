"""Dashboard integration helpers for Phase 2.8."""
from forex_bot_platform.backtesting.engine import run_backtest
from forex_bot_platform.strategies.breakout import Breakout
from forex_bot_platform.data.provider import DataProvider
import pandas as pd

def run_backtest_with_settings(data: pd.DataFrame, pair: str, timeframe: str, strategy_name: str,
                             presets: dict, spread_pips: float, slippage_pct: float, risk_per_trade: float,
                             initial_balance: float = 100000.0):
    provider = DataProvider(use_real=False)
    df = data if data is not None else provider.fetch(pair, timeframe, periods=365)
    # Instantiate strategy by name
    strat_class = {
        "Breakout": Breakout,
    }.get(strategy_name, Breakout)
    strat = strat_class()
    result = run_backtest(df, strat, initial_capital=initial_balance, spread_pips=spread_pips, slippage_pct=slippage_pct, risk_per_trade=risk_per_trade, data_pair=pair)
    return result
