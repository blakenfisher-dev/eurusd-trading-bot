"""Tests for trading strategies."""
import pytest
from forex_bot_platform.strategies import (
    BreakoutStrategy,
    SuperTrendStrategy,
    TrendFollowerStrategy,
    MeanReversionStrategy,
    ComboStrategy,
)
from forex_bot_platform.data.provider import DataProvider

def test_breakout_strategy():
    """Test breakout strategy generates signals."""
    strategy = BreakoutStrategy(lookback=10)
    provider = DataProvider("EURUSD")
    data = provider.get_historical_data("1h", candles=50)
    
    signals = strategy.generate_signals(data)
    assert isinstance(signals, list)

def test_supertrend_strategy():
    """Test SuperTrend strategy generates signals."""
    strategy = SuperTrendStrategy(period=10, multiplier=3.0)
    provider = DataProvider("EURUSD")
    data = provider.get_historical_data("1h", candles=50)
    
    signals = strategy.generate_signals(data)
    assert isinstance(signals, list)

def test_trend_follower_strategy():
    """Test trend follower strategy generates signals."""
    strategy = TrendFollowerStrategy(fast_ma=5, slow_ma=15)
    provider = DataProvider("EURUSD")
    data = provider.get_historical_data("1h", candles=50)
    
    signals = strategy.generate_signals(data)
    assert isinstance(signals, list)

def test_mean_reversion_strategy():
    """Test mean reversion strategy generates signals."""
    strategy = MeanReversionStrategy(period=10, std_dev=2.0)
    provider = DataProvider("EURUSD")
    data = provider.get_historical_data("1h", candles=50)
    
    signals = strategy.generate_signals(data)
    assert isinstance(signals, list)

def test_combo_strategy():
    """Test combo strategy combines signals."""
    breakout = BreakoutStrategy(lookback=10)
    trend = TrendFollowerStrategy(fast_ma=5, slow_ma=15)
    
    combo = ComboStrategy([breakout, trend], min_agreement=2)
    provider = DataProvider("EURUSD")
    data = provider.get_historical_data("1h", candles=50)
    
    signals = combo.generate_signals(data)
    assert isinstance(signals, list)

def test_strategy_names():
    """Test strategy names are set correctly."""
    assert BreakoutStrategy().name == "Breakout"
    assert SuperTrendStrategy().name == "SuperTrend"
    assert TrendFollowerStrategy().name == "TrendFollower"
    assert MeanReversionStrategy().name == "MeanReversion"

def test_position_sizing():
    """Test position size calculation in strategy."""
    strategy = BreakoutStrategy()
    size = strategy.calculate_position_size(10000, 0.01, 1.0850, 1.0800)
    
    assert size > 0
    assert isinstance(size, float)