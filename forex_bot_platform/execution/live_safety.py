"""Live Safety Module - Risk Limits and Safety Checks (Phase 4).

This module contains risk limits and safety checks specific to live trading.
It works with LiveGuard for maximum safety.

DISABLED BY DEFAULT - Requires --enable-live-trading flag.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import os

class SafetyLevel(Enum):
    DISABLED = "disabled"
    DRY_RUN = "dry_run"
    LIVE = "live"

@dataclass
class LiveRiskState:
    """Current risk state for live trading."""
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    total_pnl: float = 0.0
    positions_today: int = 0
    max_drawdown: float = 0.0
    last_reset: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "daily_pnl": self.daily_pnl,
            "weekly_pnl": self.weekly_pnl,
            "total_pnl": self.total_pnl,
            "positions_today": self.positions_today,
            "max_drawdown": self.max_drawdown,
            "last_reset": self.last_reset.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'LiveRiskState':
        return cls(
            daily_pnl=data.get("daily_pnl", 0),
            weekly_pnl=data.get("weekly_pnl", 0),
            total_pnl=data.get("total_pnl", 0),
            positions_today=data.get("positions_today", 0),
            max_drawdown=data.get("max_drawdown", 0),
            last_reset=datetime.fromisoformat(data["last_reset"]) if data.get("last_reset") else datetime.now(timezone.utc),
        )

class LiveSafety:
    """Safety checks for live trading.
    
    Default limits are conservative to protect capital.
    """
    
    DEFAULT_RISK_PER_TRADE = 0.0025  # 0.25%
    HARD_MAX_RISK_PER_TRADE = 0.005  # 0.5%
    DEFAULT_MAX_DAILY_LOSS = 0.01  # 1%
    DEFAULT_MAX_WEEKLY_LOSS = 0.03  # 3%
    DEFAULT_MAX_DRAWDOWN = 0.05  # 5%
    DEFAULT_MAX_POSITIONS = 3
    DEFAULT_MAX_EXPOSURE = 10000.0
    DEFAULT_MAX_SPREAD = 3.0  # pips
    DEFAULT_MAX_SLIPPAGE = 0.0005
    DEFAULT_COOLDOWN = 60  # seconds
    
    def __init__(self, account_balance: float):
        self.account_balance = account_balance
        self.risk_state = LiveRiskState()
        self._state_file = "live_risk_state.json"
    
    def get_limits(self) -> Dict[str, float]:
        """Get current risk limits."""
        return {
            "risk_per_trade": self.DEFAULT_RISK_PER_TRADE,
            "max_risk_per_trade": self.HARD_MAX_RISK_PER_TRADE,
            "max_daily_loss": self.account_balance * self.DEFAULT_MAX_DAILY_LOSS,
            "max_weekly_loss": self.account_balance * self.DEFAULT_MAX_WEEKLY_LOSS,
            "max_drawdown": self.account_balance * self.DEFAULT_MAX_DRAWDOWN,
            "max_positions": self.DEFAULT_MAX_POSITIONS,
            "max_exposure": self.DEFAULT_MAX_EXPOSURE,
            "max_spread": self.DEFAULT_MAX_SPREAD,
            "max_slippage": self.DEFAULT_MAX_SLIPPAGE,
            "cooldown": self.DEFAULT_COOLDOWN,
        }
    
    def check_risk_per_trade(self, risk_pct: float) -> bool:
        """Check if risk per trade is within limit."""
        return risk_pct <= self.HARD_MAX_RISK_PER_TRADE
    
    def check_daily_loss(self, pnl: float) -> bool:
        """Check if daily loss is within limit."""
        max_loss = self.account_balance * self.DEFAULT_MAX_DAILY_LOSS
        return pnl >= -max_loss
    
    def check_weekly_loss(self, pnl: float) -> bool:
        """Check if weekly loss is within limit."""
        max_loss = self.account_balance * self.DEFAULT_MAX_WEEKLY_LOSS
        return pnl >= -max_loss
    
    def check_drawdown(self, current_balance: float) -> bool:
        """Check if drawdown is within limit."""
        peak = self.account_balance
        dd = (peak - current_balance) / peak
        return dd <= self.DEFAULT_MAX_DRAWDOWN
    
    def check_max_positions(self, open_positions: int) -> bool:
        """Check if max positions not exceeded."""
        return open_positions < self.DEFAULT_MAX_POSITIONS
    
    def check_max_exposure(self, total_exposure: float) -> bool:
        """Check if total exposure within limit."""
        return total_exposure <= self.DEFAULT_MAX_EXPOSURE
    
    def check_spread(self, spread: float) -> bool:
        """Check if spread is within limit."""
        return spread <= self.DEFAULT_MAX_SPREAD
    
    def check_slippage(self, slippage: float) -> bool:
        """Check if slippage is within limit."""
        return slippage <= self.DEFAULT_MAX_SLIPPAGE
    
    def save_state(self) -> None:
        """Persist risk state."""
        with open(self._state_file, 'w') as f:
            json.dump(self.risk_state.to_dict(), f)
    
    def load_state(self) -> bool:
        """Load persisted risk state. Returns True if loaded."""
        if not os.path.exists(self._state_file):
            return False
        try:
            with open(self._state_file, 'r') as f:
                data = json.load(f)
            self.risk_state = LiveRiskState.from_dict(data)
            return True
        except Exception:
            return False
    
    def reset_daily(self) -> None:
        """Reset daily tracking."""
        self.risk_state.daily_pnl = 0.0
        self.risk_state.positions_today = 0
        self.risk_state.last_reset = datetime.now(timezone.utc)
    
    def reset_all(self) -> None:
        """Reset all tracking."""
        self.risk_state = LiveRiskState()
        if os.path.exists(self._state_file):
            os.remove(self._state_file)
    
    def get_safety_report(self) -> str:
        """Get formatted safety report."""
        limits = self.get_limits()
        state = self.risk_state
        
        return f"""=== Live Safety Status ===
Balance: ${self.account_balance:,.2f}

Risk Limits:
  Max Risk/Trade: {limits['max_risk_per_trade']:.2%}
  Max Daily Loss: ${limits['max_daily_loss']:,.2f}
  Max Weekly Loss: ${limits['max_weekly_loss']:,.2f}
  Max Drawdown: {limits['max_drawdown']:.2%}
  Max Positions: {limits['max_positions']}
  Max Exposure: ${limits['max_exposure']:,.2f}

Current State:
  Daily P&L: ${state.daily_pnl:,.2f}
  Weekly P&L: ${state.weekly_pnl:,.2f}
  Total P&L: ${state.total_pnl:,.2f}
  Positions Today: {state.positions_today}
  Max Drawdown: {state.max_drawdown:.2%}
"""