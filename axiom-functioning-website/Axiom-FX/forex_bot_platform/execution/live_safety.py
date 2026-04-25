"""Live Trading Safety - additional safety checks for live trading."""
from typing import Tuple, List
import json
from datetime import datetime

class LiveSafety:
    """Safety checks for live trading."""
    
    FORBIDDEN_STRATEGIES = [
        "martingale",
        "grid",
        "averaging",
        "pyramiding",
    ]
    
    def __init__(self, max_daily_loss: float = 500.0, 
                 max_drawdown: float = 15.0):
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.daily_loss = 0.0
    
    def validate_trade(self, action: str, stop_loss: float, 
                      take_profit: float, strategy_name: str) -> Tuple[bool, str]:
        """Validate a trade before execution."""
        if strategy_name.lower() in self.FORBIDDEN_STRATEGIES:
            return False, f"Strategy '{strategy_name}' is forbidden (martingale/grid/averaging)"
        
        if stop_loss is None or stop_loss == 0:
            return False, "Stop loss is required for all live trades"
        
        if take_profit is None or take_profit == 0:
            return False, "Take profit is required for all live trades"
        
        return True, "OK"
    
    def check_daily_loss(self, current_loss: float) -> Tuple[bool, str]:
        """Check if daily loss limit is reached."""
        if current_loss <= -self.max_daily_loss:
            return False, f"Daily loss limit reached: ${current_loss:.2f}"
        return True, "OK"
    
    def check_drawdown(self, equity: float, initial: float) -> Tuple[bool, str]:
        """Check if drawdown limit is reached."""
        if initial == 0:
            return True, "OK"
        
        drawdown = (initial - equity) / initial * 100
        
        if drawdown >= self.max_drawdown:
            return False, f"Drawdown limit reached: {drawdown:.2f}%"
        
        return True, "OK"
    
    def log_trade(self, trade_data: dict):
        """Log trade for audit trail."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            **trade_data
        }
        
        try:
            with open("trade_audit.json", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass
    
    def get_safety_status(self) -> dict:
        """Get current safety status."""
        return {
            "daily_loss": self.daily_loss,
            "max_daily_loss": self.max_daily_loss,
            "max_drawdown": self.max_drawdown,
            "forbidden_strategies": self.FORBIDDEN_STRATEGIES
        }