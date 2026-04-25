"""Tests for live trading safety."""
import pytest
from forex_bot_platform.execution import LiveSafety

def test_live_safety_initialization():
    """Test live safety initializes with defaults."""
    safety = LiveSafety()
    assert safety.max_daily_loss == 500.0
    assert safety.max_drawdown == 15.0

def test_validate_trade_with_stop_loss():
    """Test validation passes with stop loss."""
    safety = LiveSafety()
    valid, reason = safety.validate_trade("buy", 1.0800, 1.0900, "Breakout")
    assert valid is True

def test_validate_trade_without_stop_loss():
    """Test validation fails without stop loss."""
    safety = LiveSafety()
    valid, reason = safety.validate_trade("buy", 0, 1.0900, "Breakout")
    assert valid is False

def test_validate_trade_without_take_profit():
    """Test validation fails without take profit."""
    safety = LiveSafety()
    valid, reason = safety.validate_trade("buy", 1.0800, 0, "Breakout")
    assert valid is False

def test_forbidden_martingale_strategy():
    """Test martingale strategy is blocked."""
    safety = LiveSafety()
    valid, reason = safety.validate_trade("buy", 1.0800, 1.0900, "martingale")
    assert valid is False
    assert "forbidden" in reason.lower()

def test_forbidden_grid_strategy():
    """Test grid strategy is blocked."""
    safety = LiveSafety()
    valid, reason = safety.validate_trade("buy", 1.0800, 1.0900, "grid")
    assert valid is False

def test_forbidden_averaging_strategy():
    """Test averaging strategy is blocked."""
    safety = LiveSafety()
    valid, reason = safety.validate_trade("buy", 1.0800, 1.0900, "averaging")
    assert valid is False

def test_check_daily_loss_within_limit():
    """Test daily loss check within limit."""
    safety = LiveSafety(max_daily_loss=100.0)
    valid, reason = safety.check_daily_loss(-50.0)
    assert valid is True

def test_check_daily_loss_at_limit():
    """Test daily loss check at limit."""
    safety = LiveSafety(max_daily_loss=100.0)
    valid, reason = safety.check_daily_loss(-100.0)
    assert valid is False

def test_check_drawdown_within_limit():
    """Test drawdown check within limit."""
    safety = LiveSafety(max_drawdown=20.0)
    valid, reason = safety.check_drawdown(9000, 10000)
    assert valid is True

def test_check_drawdown_exceeds_limit():
    """Test drawdown check exceeds limit."""
    safety = LiveSafety(max_drawdown=15.0)
    valid, reason = safety.check_drawdown(8000, 10000)
    assert valid is False

def test_get_safety_status():
    """Test safety status reporting."""
    safety = LiveSafety(max_daily_loss=500.0, max_drawdown=15.0)
    status = safety.get_safety_status()
    
    assert status["max_daily_loss"] == 500.0
    assert status["max_drawdown"] == 15.0
    assert "martingale" in status["forbidden_strategies"]