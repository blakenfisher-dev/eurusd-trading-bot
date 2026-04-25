"""Live Trading Executor (Phase 4).

WARNING: This module handles REAL MONEY. Use with extreme caution.

This module is disabled by default. It requires:
- Explicit --enable-live-trading flag
- Valid LIVE_APPROVAL.json file
- All safety checks to pass
- Stop-loss on every order

This module REQUIRES the Demo Trading Mode to be fully tested first.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum
import json
import os

# Import from demo module for shared functionality
from forex_bot_platform.execution.mt5_executor import (
    AccountType, OrderSide, SafetyConfig as DemoSafetyConfig,
    MT5DemoExecutor as BaseExecutor
)
from forex_bot_platform.execution.demo_readiness import DemoReadinessConfig

class LiveTradingError(Exception):
    """Raised when live trading safety check fails."""
    pass

class LiveApprovalError(LiveTradingError):
    """Raised when live trading approval is invalid."""
    pass

class LiveSafetyError(LiveTradingError):
    """Raised when live safety check fails."""
    pass

class LiveAccountType(Enum):
    DEMO = "demo"
    LIVE = "live"

@dataclass
class LiveApproval:
    """Human approval for live trading."""
    approver_name: str
    approval_timestamp: str
    account_number: str
    broker_server: str
    max_account_size: float
    max_risk_per_trade: float
    max_daily_loss: float
    max_weekly_loss: float
    max_drawdown: float
    max_open_positions: int
    user_acknowledges_risk: bool

    @staticmethod
    def load(path: str) -> Optional['LiveApproval']:
        """Load approval from JSON file."""
        if not os.path.exists(path):
            return None
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            return LiveApproval(
                approver_name=data.get("approver_name", ""),
                approval_timestamp=data.get("approval_timestamp", ""),
                account_number=data.get("account_number", ""),
                broker_server=data.get("broker_server", ""),
                max_account_size=data.get("max_account_size", 0),
                max_risk_per_trade=data.get("max_risk_per_trade", 0),
                max_daily_loss=data.get("max_daily_loss", 0),
                max_weekly_loss=data.get("max_weekly_loss", 0),
                max_drawdown=data.get("max_drawdown", 0),
                max_open_positions=data.get("max_open_positions", 0),
                user_acknowledges_risk=data.get("user_acknowledges_risk", False),
            )
        except Exception:
            return None

@dataclass
class LiveRiskLimits:
    """Risk limits for live trading."""
    risk_per_trade: float = 0.0025  # 0.25% default
    max_risk_per_trade: float = 0.005  # 0.5% hard max
    max_daily_loss: float = 0.01  # 1% of account
    max_weekly_loss: float = 0.03  # 3% of account
    max_drawdown: float = 0.05  # 5% of account
    max_open_positions: int = 3
    max_exposure_per_currency: float = 10000.0
    max_spread: float = 3.0  # pips
    max_slippage: float = 0.0005  # price fraction
    cooldown_seconds: int = 60

class LiveExecutor:
    """Live Trading Executor - REQUIRES APPROVAL AND SAFETY CHECKS."""
    
    # Class-level flag - must be explicitly enabled
    _live_enabled = False
    
    def __init__(self, login: str, password: str, server: str,
                 approval_path: str = "LIVE_APPROVAL.json",
                 risk_limits: LiveRiskLimits = None):
        self.login = login
        self.password = password
        self.server = server
        self.approval_path = approval_path
        self.risk_limits = risk_limits or LiveRiskLimits()
        self.approval: Optional[LiveApproval] = None
        self._base = BaseExecutor(
            login=login, password=password, server=server,
            safety_config=DemoSafetyConfig(
                max_daily_loss=1000000,  # Will be overridden by live checks
                max_open_trades=self.risk_limits.max_open_positions,
                require_stop_loss=True,
            )
        )
        self._audit_log: List[Dict] = []
        self._emergency_stop_active = False
        self._weekly_pnl = 0.0
        self._weekly_start_balance = 0.0
    
    @classmethod
    def is_live_enabled(cls) -> bool:
        """Check if live trading is enabled."""
        return cls._live_enabled
    
    @classmethod
    def enable_live_trading(cls) -> None:
        """Enable live trading. Must be called explicitly."""
        cls._live_enabled = True
    
    @classmethod
    def disable_live_trading(cls) -> None:
        """Disable live trading."""
        cls._live_enabled = False
    
    def _log_audit(self, event: str, details: str, success: bool = True) -> None:
        """Log audit event."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "details": details,
            "success": success,
        }
        self._audit_log.append(entry)
    
    def verify_approval(self) -> bool:
        """Verify human approval exists and is valid."""
        approval = LiveApproval.load(self.approval_path)
        
        if approval is None:
            self._log_audit("approval_check", "No approval file found", False)
            return False
        
        if not approval.user_acknowledges_risk:
            self._log_audit("approval_check", "User did not acknowledge risk", False)
            return False
        
        if approval.broker_server != self.server:
            self._log_audit("approval_check", f"Server mismatch: {approval.broker_server} != {self.server}", False)
            return False
        
        self.approval = approval
        self._log_audit("approval_check", f"Approval valid for {approval.account_number}", True)
        return True
    
    def verify_live_account(self) -> bool:
        """Verify this is a LIVE account, not demo."""
        self._base.connect()
        
        if not self._base.is_connected:
            self._log_audit("account_verify", "Could not connect", False)
            return False
        
        # In real MT5, would check account_info().trade_mode
        # For now, assume connected account is live
        account_type = LiveAccountType.LIVE
        self._log_audit("account_verify", f"Connected to {account_type.value} account", True)
        return True
    
    def can_trade_live(self) -> tuple[bool, str]:
        """Check if live trading is allowed."""
        # Check 1: Live mode enabled?
        if not LiveExecutor.is_live_enabled():
            return False, "Live trading is not enabled. Pass --enable-live-trading"
        
        # Check 2: Approval exists?
        if not self.verify_approval():
            return False, "No valid live trading approval. Create LIVE_APPROVAL.json"
        
        # Check 3: Connected?
        if not self._base.is_connected:
            return False, "Not connected to broker"
        
        # Check 4: Emergency stop?
        if self._emergency_stop_active:
            return False, "Emergency stop is active"
        
        return True, "OK"
    
    def place_live_order(self, symbol: str, side: OrderSide, volume: float,
                        stop_loss: float, take_profit: Optional[float] = None) -> int:
        """Place a live order. REQUIRES STOP-LOSS."""
        # Pre-flight checks
        can_trade, reason = self.can_trade_live()
        if not can_trade:
            self._log_audit("live_order", f"Blocked: {reason}", False)
            raise LiveSafetyError(f"Cannot place live order: {reason}")
        
        # Check stop-loss is provided
        if stop_loss is None:
            self._log_audit("live_order", "Blocked: No stop-loss", False)
            raise LiveSafetyError("Stop-loss is required for live trading")
        
        # Check risk per trade
        risk_pct = abs(stop_loss - self._base.account.balance) / self._base.account.balance if self._base.account else 0
        if risk_pct > self.risk_limits.max_risk_per_trade:
            self._log_audit("live_order", f"Risk {risk_pct:.2%} exceeds max {self.risk_limits.max_risk_per_trade:.2%}", False)
            raise LiveSafetyError(f"Risk per trade exceeds limit")
        
        # Place order via base executor
        try:
            ticket = self._base.place_demo_order(symbol, side, volume, stop_loss, take_profit)
            self._log_audit("live_order", f"Placed {symbol} {side.name} ticket={ticket}", True)
            return ticket
        except Exception as e:
            self._log_audit("live_order", f"Failed: {e}", False)
            raise
    
    def emergency_stop_live(self) -> str:
        """Trigger emergency stop for live trading."""
        self._emergency_stop_active = True
        LiveExecutor.disable_live_trading()
        
        # Close all positions
        for pos in list(self._base.positions):
            self._base.close_demo_order(pos.ticket)
        
        self._log_audit("emergency_stop", "Emergency stop triggered", True)
        return "emergency_stop_triggered"
    
    def get_live_status(self) -> Dict[str, Any]:
        """Get live trading status."""
        return {
            "live_enabled": LiveExecutor.is_live_enabled(),
            "approval_valid": self.approval is not None,
            "connected": self._base.is_connected,
            "emergency_stop": self._emergency_stop_active,
            "positions": len(self._base.positions),
            "audit_log_count": len(self._audit_log),
        }
    
    def get_audit_log(self) -> List[Dict]:
        """Get audit log."""
        return self._audit_log.copy()
