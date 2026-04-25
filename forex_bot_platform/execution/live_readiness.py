"""Live Trading Readiness Checker (Phase 4).

This module checks if live trading is ready to be enabled.
It does NOT enable live trading - it only checks readiness.

DISABLED BY DEFAULT - Requires --enable-live-trading flag.
"""
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum
import os
import json
from datetime import datetime, timezone, timedelta

from forex_bot_platform.execution.live_executor import (
    LiveApproval, LiveExecutor, LiveRiskLimits
)
from forex_bot_platform.execution.live_guard import LiveGuard, GateResult
from forex_bot_platform.execution.live_safety import LiveSafety

class ReadinessStatus(Enum):
    READY = "ready"
    NOT_READY = "not_ready"
    PARTIAL = "partial"

@dataclass
class ReadinessCheck:
    """Result of a single readiness check."""
    name: str
    status: ReadinessStatus
    message: str
    details: Optional[str] = None

class LiveReadinessConfig:
    """Configuration for live readiness checks."""
    def __init__(self,
                 approval_path: str = "LIVE_APPROVAL.json",
                 live_enabled_required: bool = True,
                 account_match_required: bool = True,
                 risk_limits_file: Optional[str] = None,
                 emergency_stop_file: str = "live_emergency_stop.json"):
        self.approval_path = approval_path
        self.live_enabled_required = live_enabled_required
        self.account_match_required = account_match_required
        self.risk_limits_file = risk_limits_file
        self.emergency_stop_file = emergency_stop_file

class LiveReadinessChecker:
    """Checks if live trading is ready to be enabled.
    
    This does NOT enable live trading - it only checks readiness.
    Use --enable-live-trading to actually enable.
    """
    
    def __init__(self, config: LiveReadinessConfig = None):
        self.config = config or LiveReadinessConfig()
        self.checks: List[ReadinessCheck] = []
    
    def check_all(self) -> Tuple[bool, List[ReadinessCheck]]:
        """Run all readiness checks. Returns (all_ready, results)."""
        self.checks = []
        
        # Check 1: Approval file exists
        self.checks.append(self._check_approval_file())
        
        # Check 2: Approval valid
        self.checks.append(self._check_approval_valid())
        
        # Check 3: Approval not expired
        self.checks.append(self._check_approval_not_expired())
        
        # Check 4: Risk limits file exists
        self.checks.append(self._check_risk_limits())
        
        # Check 5: Emergency stop file
        self.checks.append(self._check_emergency_stop())
        
        # Check 6: Live trading explicitly enabled (via config/env)
        self.checks.append(self._check_live_enabled_flag())
        
        # Check 7: Config file check
        self.checks.append(self._check_config())
        
        all_ready = all(c.status == ReadinessStatus.READY for c in self.checks)
        return all_ready, self.checks
    
    def _check_approval_file(self) -> ReadinessCheck:
        """Check approval file exists."""
        if os.path.exists(self.config.approval_path):
            return ReadinessCheck("approval_file", ReadinessStatus.READY,
                              f"File exists: {self.config.approval_path}")
        return ReadinessCheck("approval_file", ReadinessStatus.NOT_READY,
                            "Approval file not found",
                            f"Create {self.config.approval_path}")
    
    def _check_approval_valid(self) -> ReadinessCheck:
        """Check approval is valid."""
        approval = LiveApproval.load(self.config.approval_path)
        
        if approval is None:
            return ReadinessCheck("approval_valid", ReadinessStatus.NOT_READY,
                                "Cannot load approval")
        
        if not approval.user_acknowledges_risk:
            return ReadinessCheck("approval_valid", ReadinessStatus.NOT_READY,
                                "Risk not acknowledged by user")
        
        if not approval.approver_name:
            return ReadinessCheck("approval_valid", ReadinessStatus.NOT_READY,
                                "Approver name missing")
        
        return ReadinessCheck("approval_valid", ReadinessStatus.READY,
                          f"Approved by {approval.approver_name}")
    
    def _check_approval_not_expired(self) -> ReadinessCheck:
        """Check approval not expired (30 days)."""
        approval = LiveApproval.load(self.config.approval_path)
        
        if approval is None:
            return ReadinessCheck("approval_expiry", ReadinessStatus.NOT_READY,
                                "No approval to check")
        
        try:
            ts = datetime.fromisoformat(approval.approval_timestamp)
            age = datetime.now(timezone.utc) - ts
            
            if age > timedelta(days=30):
                return ReadinessCheck("approval_expiry", ReadinessStatus.NOT_READY,
                                   f"Approval expired ({age.days} days old)")
            
            if age > timedelta(days=25):
                return ReadinessCheck("approval_expiry", ReadinessStatus.PARTIAL,
                                   f"Approval expires soon ({30 - age.days} days left)")
            
            return ReadinessCheck("approval_expiry", ReadinessStatus.READY,
                               f"Approval valid ({age.days} days old)")
        except Exception as e:
            return ReadinessCheck("approval_expiry", ReadinessStatus.PARTIAL,
                               f"Cannot parse timestamp: {e}")
    
    def _check_risk_limits(self) -> ReadinessCheck:
        """Check risk limits are defined."""
        if self.config.risk_limits_file and os.path.exists(self.config.risk_limits_file):
            return ReadinessCheck("risk_limits", ReadinessStatus.READY,
                                  "Risk limits file exists")
        
        # Default limits always available
        return ReadinessCheck("risk_limits", ReadinessStatus.READY,
                          "Using default risk limits")
    
    def _check_emergency_stop(self) -> ReadinessCheck:
        """Check emergency stop state."""
        if os.path.exists(self.config.emergency_stop_file):
            try:
                with open(self.config.emergency_stop_file, 'r') as f:
                    data = json.load(f)
                if data.get("active"):
                    return ReadinessCheck("emergency_stop", ReadinessStatus.NOT_READY,
                                         "Emergency stop is ACTIVE")
            except Exception:
                pass
        
        return ReadinessCheck("emergency_stop", ReadinessStatus.READY,
                             "Emergency stop inactive")
    
    def _check_live_enabled_flag(self) -> ReadinessCheck:
        """Check env/config has live enabled flag."""
        # Check environment variable
        if os.environ.get("LIVE_TRADING_ENABLED", "").lower() == "true":
            return ReadinessCheck("live_enabled_flag", ReadinessStatus.READY,
                                  "LIVE_TRADING_ENABLED=true in env")
        
        # Check config file
        if os.path.exists("config.json"):
            try:
                with open("config.json", 'r') as f:
                    config = json.load(f)
                if config.get("live_trading_enabled"):
                    return ReadinessCheck("live_enabled_flag", ReadinessStatus.READY,
                                        "live_trading_enabled=true in config")
            except Exception:
                pass
        
        return ReadinessCheck("live_enabled_flag", ReadinessStatus.PARTIAL,
                            "Live trading not yet enabled",
                            "Pass --enable-live-trading to enable")
    
    def _check_config(self) -> ReadinessCheck:
        """Check configuration files."""
        if os.path.exists("config.json"):
            return ReadinessCheck("config", ReadinessStatus.READY,
                                 "config.json exists")
        return ReadinessCheck("config", ReadinessStatus.PARTIAL,
                              "No config.json - using defaults")
    
    def get_readiness_score(self) -> int:
        """Get readiness score (0-100)."""
        if not self.checks:
            self.check_all()
        
        ready = sum(1 for c in self.checks if c.status == ReadinessStatus.READY)
        partial = sum(1 for c in self.checks if c.status == ReadinessStatus.PARTIAL)
        
        return (ready * 100 + partial * 50) // len(self.checks) if self.checks else 0
    
    def get_readiness_report(self) -> str:
        """Get formatted readiness report."""
        lines = ["=== Live Trading Readiness ===", ""]
        
        score = self.get_readiness_score()
        lines.append(f"Readiness Score: {score}/100")
        lines.append("")
        
        for check in self.checks:
            if check.status == ReadinessStatus.READY:
                icon = "[PASS]"
            elif check.status == ReadinessStatus.PARTIAL:
                icon = "[PARTIAL]"
            else:
                icon = "[FAIL]"
            
            lines.append(f"{icon} [{check.name}] {check.message}")
        
        return "\n".join(lines)

def check_live_readiness() -> Tuple[bool, str]:
    """Main function to check live trading readiness."""
    checker = LiveReadinessChecker()
    all_ready, checks = checker.check_all()
    
    report = checker.get_readiness_report()
    
    if all_ready:
        return True, report
    return False, report