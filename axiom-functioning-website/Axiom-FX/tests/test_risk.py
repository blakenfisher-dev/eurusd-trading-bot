"""Tests for risk management."""
import pytest
from forex_bot_platform.risk import RiskManager, RiskLimits

def test_risk_manager_initialization():
    """Test risk manager initializes with default limits."""
    rm = RiskManager()
    assert rm.limits.max_daily_loss == 1000.0
    assert rm.limits.max_drawdown_pct == 20.0
    assert rm.limits.max_open_trades == 3

def test_custom_risk_limits():
    """Test risk manager with custom limits."""
    limits = RiskLimits(max_daily_loss=500.0, max_open_trades=2)
    rm = RiskManager(limits)
    
    assert rm.limits.max_daily_loss == 500.0
    assert rm.limits.max_open_trades == 2

def test_can_open_trade_under_limit():
    """Test can open trade when under limit."""
    rm = RiskManager()
    can_trade, reason = rm.can_open_trade(spread=1.0)
    assert can_trade is True

def test_can_open_trade_at_limit():
    """Test cannot open trade when at limit."""
    rm = RiskManager(RiskLimits(max_open_trades=2))
    rm.open_trades = 2
    
    can_trade, reason = rm.can_open_trade()
    assert can_trade is False
    assert "Max open trades" in reason

def test_daily_loss_limit():
    """Test daily loss limit blocks trading."""
    rm = RiskManager(RiskLimits(max_daily_loss=100.0))
    rm.daily_pnl = -100.0
    
    can_trade, reason = rm.can_open_trade()
    assert can_trade is False
    assert "Daily loss" in reason

def test_position_size_calculation():
    """Test position size calculation."""
    rm = RiskManager(RiskLimits(risk_per_trade=0.01))
    
    size = rm.calculate_position_size(10000.0, 1.0850, 1.0800)
    assert size > 0
    assert size <= 1.0

def test_validate_stop_loss_buy():
    """Test stop loss validation for buy."""
    rm = RiskManager(RiskLimits(require_stop_loss=True))
    
    valid, reason = rm.validate_stop_loss("buy", 1.0850, 1.0800)
    assert valid is True

def test_validate_stop_loss_sell():
    """Test stop loss validation for sell."""
    rm = RiskManager(RiskLimits(require_stop_loss=True))
    
    valid, reason = rm.validate_stop_loss("sell", 1.0850, 1.0900)
    assert valid is True

def test_validate_stop_loss_missing():
    """Test stop loss validation fails when missing."""
    rm = RiskManager(RiskLimits(require_stop_loss=True))
    
    valid, reason = rm.validate_stop_loss("buy", 1.0850, 0)
    assert valid is False
    assert "required" in reason.lower()

def test_check_drawdown():
    """Test drawdown checking."""
    rm = RiskManager(RiskLimits(max_drawdown_pct=20.0))
    
    valid, reason = rm.check_drawdown(9000, 10000)
    assert valid is True
    
    valid, reason = rm.check_drawdown(7500, 10000)
    assert valid is False
    assert "Drawdown" in reason

def test_increment_decrement_trades():
    """Test trade counter."""
    rm = RiskManager()
    assert rm.open_trades == 0
    
    rm.increment_trades()
    assert rm.open_trades == 1
    
    rm.decrement_trades()
    assert rm.open_trades == 0