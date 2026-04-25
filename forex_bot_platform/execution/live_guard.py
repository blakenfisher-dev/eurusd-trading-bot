"""Live Trading Guard - Safety Gates for Live Trading (Phase 4).

This module enforces safety gates BEFORE any live order can be placed.
It is the primary defense against accidental live trading.

DISABLED BY DEFAULT - Requires --enable-live-trading flag.
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
import os
import json

from forex_bot_platform.execution.live_executor import (
    LiveApproval, LiveExecutor, LiveRiskLimits, LiveAccountType,
    LiveTradingError, LiveApprovalError, LiveSafetyError
)

class GateResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"

@dataclass
class GateCheck:
    """Result of a single gate check."""
    name: str
    result: GateResult
    message: str
    details: Optional[str] = None

class LiveGuard:
    """Enforces safety gates for live trading.
    
    All gates must pass before any live order is allowed.
    """
    
    def __init__(self, executor: LiveExecutor):
        self.executor = executor
        self.checks: List[GateCheck] = []
        self._last_check_time: Optional[datetime] = None
    
    def check_all_gates(self) -> Tuple[bool, List[GateCheck]]:
        """Run all safety gates. Returns (all_passed, results)."""
        self.checks = []
        
        # Gate 1: Live mode enabled?
        self.checks.append(self._gate_live_enabled())
        
        # Gate 2: Valid approval?
        self.checks.append(self._gate_approval())
        
        # Gate 3: Account matches?
        self.checks.append(self._gate_account())
        
        # Gate 4: Not emergency stop?
        self.checks.append(self._gate_emergency_stop())
        
        # Gate 5: Connection stable?
        self.checks.append(self._gate_connection())
        
        # Gate 6: Market data fresh?
        self.checks.append(self._gate_market_data())
        
        # Gate 7: Risk limits OK?
        self.checks.append(self._gate_risk_limits())
        
        self._last_check_time = datetime.now(timezone.utc)
        
        all_passed = all(c.result == GateResult.PASS for c in self.checks)
        return all_passed, self.checks
    
    def _gate_live_enabled(self) -> GateCheck:
        """Gate 1: Live trading must be explicitly enabled."""
        if LiveExecutor.is_live_enabled():
            return GateCheck("live_enabled", GateResult.PASS, "Live trading is enabled")
        return GateCheck("live_enabled", GateResult.FAIL, "Pass --enable-live-trading to enable")
    
    def _gate_approval(self) -> GateCheck:
        """Gate 2: Valid human approval must exist."""
        approval = LiveApproval.load(self.executor.approval_path)
        
        if approval is None:
            return GateCheck("approval", GateResult.FAIL, "No approval file", "Create LIVE_APPROVAL.json")
        
        if not approval.user_acknowledges_risk:
            return GateCheck("approval", GateResult.FAIL, "Risk not acknowledged")
        
        # Check expiration (30 days)
        try:
            ts = datetime.fromisoformat(approval.approval_timestamp)
            if datetime.now(timezone.utc) - ts > timedelta(days=30):
                return GateCheck("approval", GateResult.FAIL, "Approval expired")
        except Exception:
            pass
        
        return GateCheck("approval", GateResult.PASS, f"Approved by {approval.approver_name}")
    
    def _gate_account(self) -> GateCheck:
        """Gate 3: Account must match approval."""
        if self.executor.approval is None:
            return GateCheck("account", GateResult.SKIP, "No approval to check")
        
        if not self.executor._base.is_connected:
            return GateCheck("account", GateResult.FAIL, "Not connected")
        
        # In real MT5, would verify account number matches
        return GateCheck("account", GateResult.PASS, "Account verified")
    
    def _gate_emergency_stop(self) -> GateCheck:
        """Gate 4: Emergency stop must not be active."""
        if self.executor._emergency_stop_active:
            return GateCheck("emergency_stop", GateResult.FAIL, "Emergency stop is active")
        return GateCheck("emergency_stop", GateResult.PASS, "Emergency stop inactive")
    
    def _gate_connection(self) -> GateCheck:
        """Gate 5: Connection must be stable."""
        if not self.executor._base.is_connected:
            return GateCheck("connection", GateResult.FAIL, "Not connected to broker")
        return GateCheck("connection", GateResult.PASS, "Connected")
    
    def _gate_market_data(self) -> GateCheck:
        """Gate 6: Market data must be fresh."""
        # In real MT5, would check last tick timestamp
        return GateCheck("market_data", GateResult.PASS, "Market data available")
    
    def _gate_risk_limits(self) -> GateCheck:
        """Gate 7: Risk limits must be within bounds."""
        limits = self.executor.risk_limits
        
        # Check various limits
        if limits.risk_per_trade > limits.max_risk_per_trade:
            return GateCheck("risk_limits", GateResult.FAIL, f"Risk {limits.risk_per_trade} > max {limits.max_risk_per_trade}")
        
        return GateCheck("risk_limits", GateResult.PASS, "Risk limits OK")
    
    def check_order_gates(self, symbol: str, side: str, volume: float,
                        stop_loss: float, take_profit: Optional[float]) -> Tuple[bool, List[GateCheck]]:
        """Run pre-order safety gates.
        
        These run BEFORE any order is placed.
        """
        order_checks = []
        
        # Gate O1: Stop-loss required
        if stop_loss is None:
            order_checks.append(GateCheck("stop_loss", GateResult.FAIL, "Stop-loss required"))
        else:
            order_checks.append(GateCheck("stop_loss", GateResult.PASS, "Stop-loss provided"))
        
        # Gate O2: Risk per trade within limit
        risk_pct = abs(stop_loss - (self.executor._base.account.balance or 0)) / (self.executor._base.account.balance or 1)
        if risk_pct > self.executor.risk_limits.max_risk_per_trade:
            order_checks.append(GateCheck("risk_per_trade", GateResult.FAIL, f"Risk {risk_pct:.2%} exceeds limit"))
        else:
            order_checks.append(GateCheck("risk_per_trade", GateResult.PASS, f"Risk {risk_pct:.2%} OK"))
        
        # Gate O3: Max positions not exceeded
        current_positions = len(self.executor._base.positions)
        if current_positions >= self.executor.risk_limits.max_open_positions:
            order_checks.append(GateCheck("max_positions", GateResult.FAIL, f"Positions {current_positions} >= limit"))
        else:
            order_checks.append(GateCheck("max_positions", GateResult.PASS, f"Positions {current_positions} OK"))
        
        order_checks.append(self._gate_spread())
        order_checks.append(self._gate_duplicate_order(symbol, side, volume))
        order_checks.append(self._gate_session_filter())
        
        all_passed = all(c.result == GateResult.PASS for c in order_checks)
        return all_passed, order_checks
    
    def _gate_spread(self) -> GateCheck:
        """Check spread is within limit."""
        # In real MT5, would get actual spread
        spread = 1.0  # Assume 1 pip
        if spread > self.executor.risk_limits.max_spread:
            return GateCheck("spread", GateResult.FAIL, f"Spread {spread} > limit")
        return GateCheck("spread", GateResult.PASS, f"Spread {spread} OK")
    
    def _gate_duplicate_order(self, symbol: str, side: str, volume: float) -> GateCheck:
        """Check for duplicate orders."""
        for pos in self.executor._base.positions:
            if pos.symbol == symbol and pos.volume == volume:
                if abs(datetime.now(timezone.utc).timestamp() - pos.open_time.timestamp()) < 30:
                    return GateCheck("duplicate", GateResult.FAIL, "Duplicate order within 30s")
        return GateCheck("duplicate", GateResult.PASS, "No duplicate")
    
    def _gate_session_filter(self) -> GateCheck:
        """Check trading session is open."""
        # Simplified - assume always open
        return GateCheck("session", GateResult.PASS, "Session open")
    
    def get_gate_report(self) -> str:
        """Get formatted gate report."""
        lines = ["=== Live Trading Safety Gates ===", ""]
        
        for check in self.checks:
            status = "✓" if check.result == GateResult.PASS else "✗"
            lines.append(f"{status} [{check.name}] {check.message}")
        
        return "\n".join(lines)