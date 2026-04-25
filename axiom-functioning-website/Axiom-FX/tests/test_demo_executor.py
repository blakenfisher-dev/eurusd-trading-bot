"""Tests for MT5 Demo Executor."""
import pytest
from forex_bot_platform.execution import MT5DemoExecutor, LiveGuard, LiveSafety
from forex_bot_platform.risk import RiskManager, RiskLimits

def test_demo_executor_initialization():
    """Test demo executor initializes correctly."""
    executor = MT5DemoExecutor(login="12345", server="MetaQuotes-Demo")
    assert executor.login == "12345"
    assert executor.server == "MetaQuotes-Demo"
    assert executor.connected is False

def test_connect_to_demo():
    """Test connecting to demo account."""
    executor = MT5DemoExecutor(login="12345", server="MetaQuotes-Demo")
    success, message = executor.connect()
    
    assert success is True
    assert "demo" in message.lower()
    assert executor.connected is True

def test_reject_live_server():
    """Test live servers are rejected."""
    executor = MT5DemoExecutor(login="12345", server="ICMarkets-Live")
    success, message = executor.connect()
    
    assert success is False
    assert "demo" in message.lower()

def test_is_demo_account():
    """Test demo account verification."""
    executor = MT5DemoExecutor(login="12345", server="MetaQuotes-Demo")
    executor.connect()
    
    assert executor.is_demo_account() is True

def test_place_order_not_connected():
    """Test cannot place order when not connected."""
    executor = MT5DemoExecutor()
    result = executor.place_order("buy", "EURUSD", 0.1, 1.0800)
    
    assert result.success is False
    assert "connected" in result.message.lower()

def test_place_order_demo_success():
    """Test placing demo order succeeds."""
    executor = MT5DemoExecutor(login="12345", server="MetaQuotes-Demo")
    executor.connect()
    
    result = executor.place_order("buy", "EURUSD", 0.1, 1.0750, 1.0900)
    
    assert result.success is True
    assert result.order_id is not None

def test_live_guard_emergency_stop():
    """Test emergency stop blocks trading."""
    import os
    import json
    
    guard = LiveGuard(approval_file="nonexistent_approval.json", emergency_stop_file="test_emergency.json")
    guard.trigger_emergency_stop("Test")
    
    can_trade, reason = guard.can_trade_live()
    assert can_trade is False
    assert "emergency" in reason.lower()
    
    guard.clear_emergency_stop()

def test_live_safety_forbidden_strategies():
    """Test live safety blocks forbidden strategies."""
    safety = LiveSafety()
    
    valid, reason = safety.validate_trade("buy", 1.0800, 1.0900, "martingale")
    assert valid is False
    assert "forbidden" in reason.lower()

def test_live_safety_requires_stop_loss():
    """Test live safety requires stop loss."""
    safety = LiveSafety()
    
    valid, reason = safety.validate_trade("buy", 0, 1.0900, "Breakout")
    assert valid is False
    assert "stop loss" in reason.lower()

def test_live_safety_check_daily_loss():
    """Test daily loss check."""
    safety = LiveSafety(max_daily_loss=100.0)
    
    valid, reason = safety.check_daily_loss(-100.0)
    assert valid is False
    assert "loss" in reason.lower()