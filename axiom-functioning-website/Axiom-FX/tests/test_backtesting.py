"""Tests for backtesting engine."""
import pytest
from forex_bot_platform.backtesting import BacktestEngine
from forex_bot_platform.strategies import BreakoutStrategy, TrendFollowerStrategy
from forex_bot_platform.data.provider import DataProvider, OHLCV
from datetime import datetime, timedelta

def test_backtest_engine_initialization():
    """Test backtest engine initializes correctly."""
    engine = BacktestEngine(initial_balance=100000.0)
    assert engine.initial_balance == 100000.0
    assert engine.balance == 100000.0
    assert engine.trades == []

def test_backtest_runs_without_error():
    """Test backtest runs without errors."""
    engine = BacktestEngine(initial_balance=100000.0)
    strategy = BreakoutStrategy()
    result = engine.run("EURUSD", strategy, "1h", candles=100)
    
    assert result is not None
    assert result.pair == "EURUSD"
    assert result.strategy == "Breakout"
    assert result.initial_balance == 100000.0

def test_backtest_with_trend_follower():
    """Test backtest with trend follower strategy."""
    engine = BacktestEngine(initial_balance=100000.0)
    strategy = TrendFollowerStrategy(fast_ma=5, slow_ma=10)
    result = engine.run("EURUSD", strategy, "1h", candles=100)
    
    assert result is not None
    assert result.strategy == "TrendFollower"

def test_data_provider_generates_data():
    """Test data provider generates synthetic data."""
    provider = DataProvider("EURUSD")
    data = provider.get_historical_data("1h", candles=100)
    
    assert len(data) == 100
    assert all(isinstance(c, OHLCV) for c in data)

def test_multiple_pairs():
    """Test backtest on multiple currency pairs."""
    pairs = ["EURUSD", "GBPUSD", "USDJPY"]
    strategy = BreakoutStrategy()
    engine = BacktestEngine()
    
    for pair in pairs:
        result = engine.run(pair, strategy, "1h", candles=50)
        assert result is not None
        assert result.pair == pair