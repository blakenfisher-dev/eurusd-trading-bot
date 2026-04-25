"""Live Trading Guard - safety gates for live trading."""
from typing import Tuple, Optional
import os
import json
from datetime import datetime

class LiveGuard:
    """Safety gates for live trading."""
    
    def __init__(self, approval_file: str = "live_approval.json",
                 emergency_stop_file: str = "emergency_stop.json"):
        self.approval_file = approval_file
        self.emergency_stop_file = emergency_stop_file
    
    def can_trade_live(self) -> Tuple[bool, str]:
        """Check if live trading is allowed."""
        if self._is_emergency_stop_active():
            return False, "Emergency stop is active"
        
        if not self._is_approval_valid():
            return False, "No valid approval file"
        
        return True, "OK"
    
    def _is_approval_valid(self) -> bool:
        """Check if approval file exists and is valid."""
        if not os.path.exists(self.approval_file):
            return False
        
        try:
            with open(self.approval_file, 'r') as f:
                approval = json.load(f)
            
            if "expiry" in approval:
                expiry = datetime.fromisoformat(approval["expiry"])
                if datetime.now() > expiry:
                    return False
            
            return True
        except:
            return False
    
    def _is_emergency_stop_active(self) -> bool:
        """Check if emergency stop is active."""
        if not os.path.exists(self.emergency_stop_file):
            return False
        
        try:
            with open(self.emergency_stop_file, 'r') as f:
                stop = json.load(f)
            return stop.get("active", False)
        except:
            return False
    
    def trigger_emergency_stop(self, reason: str = "Manual trigger"):
        """Trigger emergency stop."""
        stop_data = {
            "active": True,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.emergency_stop_file, 'w') as f:
            json.dump(stop_data, f, indent=2)
    
    def clear_emergency_stop(self):
        """Clear emergency stop."""
        if os.path.exists(self.emergency_stop_file):
            os.remove(self.emergency_stop_file)