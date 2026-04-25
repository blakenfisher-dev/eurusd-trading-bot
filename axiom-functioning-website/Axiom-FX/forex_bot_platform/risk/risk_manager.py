"""Risk management for forex trading."""
from dataclasses import dataclass
from typing import Optional, Tuple
import os

@dataclass
class RiskLimits:
    """Risk management limits."""
    max_daily_loss: float = 1000.0
    max_drawdown_pct: float = 20.0
    max_open_trades: int = 3
    risk_per_trade: float = 0.01
    min_spread: float = 0.5
    require_stop_loss: bool = True

class RiskManager:
    """Risk management for trading."""
    
    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()
        self.daily_pnl = 0.0
        self.open_trades = 0
    
    def can_open_trade(self, spread: float = 1.0) -> Tuple[bool, str]:
        """Check if a new trade can be opened."""
        if self.open_trades >= self.limits.max_open_trades:
            return False, f"Max open trades reached: {self.open_trades}"
        
        if self.daily_pnl <= -self.limits.max_daily_loss:
            return False, f"Daily loss limit reached: ${self.daily_pnl:.2f}"
        
        if spread < self.limits.min_spread:
            return False, f"Spread too low: {spread} < {self.limits.min_spread}"
        
        return True, "OK"
    
    def calculate_position_size(self, account_balance: float, 
                                entry_price: float, 
                                stop_loss: float) -> float:
        """Calculate position size based on risk per trade."""
        if not self.limits.require_stop_loss or stop_loss == 0:
            return 0.0
        
        risk_amount = account_balance * self.limits.risk_per_trade
        pips_risk = abs(entry_price - stop_loss)
        
        if pips_risk == 0:
            return 0.0
        
        position_size = risk_amount / pips_risk
        return round(min(position_size, 1.0), 2)
    
    def validate_stop_loss(self, action: str, entry: float, stop_loss: float) -> Tuple[bool, str]:
        """Validate stop loss is present and reasonable."""
        if not self.limits.require_stop_loss:
            return True, "OK"
        
        if stop_loss is None or stop_loss == 0:
            return False, "Stop loss required"
        
        if action == "buy" and stop_loss >= entry - 0.0001:
            return False, "Stop loss must be below entry for buy"
        
        if action == "sell" and stop_loss <= entry + 0.0001:
            return False, "Stop loss must be above entry for sell"
        
        return True, "OK"
    
    def check_drawdown(self, current_equity: float, initial_equity: float) -> Tuple[bool, str]:
        """Check if drawdown exceeds limit."""
        if initial_equity == 0:
            return True, "OK"
        
        drawdown_pct = (initial_equity - current_equity) / initial_equity * 100
        
        if drawdown_pct >= self.limits.max_drawdown_pct:
            return False, f"Drawdown limit reached: {drawdown_pct:.2f}%"
        
        return True, "OK"
    
    def update_daily_pnl(self, pnl: float):
        """Update daily PnL tracking."""
        self.daily_pnl += pnl
    
    def reset_daily(self):
        """Reset daily tracking (call at start of new day)."""
        self.daily_pnl = 0.0
    
    def increment_trades(self):
        """Increment open trade counter."""
        self.open_trades += 1
    
    def decrement_trades(self):
        """Decrement open trade counter."""
        self.open_trades = max(0, self.open_trades - 1)