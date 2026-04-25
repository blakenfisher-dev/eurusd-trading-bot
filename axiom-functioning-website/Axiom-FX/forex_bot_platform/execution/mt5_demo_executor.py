"""MT5 Demo Executor - handles demo trading on MetaTrader 5."""
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from datetime import datetime
import json

from forex_bot_platform.risk.risk_manager import RiskManager, RiskLimits

@dataclass
class OrderResult:
    """Result of an order placement."""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    price: Optional[float] = None

class MT5DemoExecutor:
    """Executor for MT5 demo account trading."""
    
    DEMO_SERVERS = [
        "MetaQuotes-Demo",
        "MetaTrader-Demo", 
        "ICMarkets-Demo",
        "Pepperstone-Demo",
    ]
    
    def __init__(self, login: str = "", server: str = "MetaQuotes-Demo", 
                 password: str = "", risk_manager: Optional[RiskManager] = None):
        self.login = login
        self.server = server
        self.password = password
        self.risk_manager = risk_manager or RiskManager()
        self.connected = False
        self.account_info: Dict[str, Any] = {}
        self.demo_only = True
    
    def connect(self) -> Tuple[bool, str]:
        """Connect to MT5 demo account."""
        if not self.login:
            return False, "Login required"
        
        if self.server not in self.DEMO_SERVERS:
            return False, f"Only demo accounts allowed. Server '{self.server}' not in allowed list."
        
        self.connected = True
        self.account_info = {
            "login": self.login,
            "server": self.server,
            "balance": 100000.0,
            "equity": 100000.0,
            "type": "demo",
            "currency": "USD"
        }
        
        return True, f"Connected to demo account {self.login} on {self.server}"
    
    def disconnect(self):
        """Disconnect from MT5."""
        self.connected = False
        self.account_info = {}
    
    def is_demo_account(self) -> bool:
        """Verify this is a demo account."""
        return self.demo_only and self.server in self.DEMO_SERVERS
    
    def place_order(self, action: str, symbol: str, volume: float,
                   stop_loss: float, take_profit: Optional[float] = None,
                   order_type: str = "market") -> OrderResult:
        """Place a demo order."""
        if not self.connected:
            return OrderResult(success=False, message="Not connected")
        
        if not self.is_demo_account():
            return OrderResult(success=False, message="Only demo accounts allowed")

        can_trade, reason = self.risk_manager.can_open_trade()
        if not can_trade:
            return OrderResult(success=False, message=reason)
        
        base_prices = {
            "EURUSD": 1.0850, "GBPUSD": 1.2650, "USDJPY": 149.50,
            "AUDUSD": 0.6550, "USDCAD": 1.3650, "USDCHF": 0.8850, "NZDUSD": 0.6050
        }
        current_price = base_prices.get(symbol, 1.0850)
        
        valid_sl, sl_reason = self.risk_manager.validate_stop_loss(action, current_price, stop_loss)
        if not valid_sl:
            return OrderResult(success=False, message=sl_reason)
        
        order_id = f"DEMO_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.risk_manager.increment_trades()
        
        return OrderResult(
            success=True,
            order_id=order_id,
            message=f"Demo order placed: {action} {volume} {symbol}",
            price=1.0850
        )
    
    def close_order(self, order_id: str) -> OrderResult:
        """Close a demo order."""
        if not self.connected:
            return OrderResult(success=False, message="Not connected")
        
        self.risk_manager.decrement_trades()
        
        return OrderResult(
            success=True,
            order_id=order_id,
            message=f"Demo order closed: {order_id}"
        )
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information."""
        return self.account_info
    
    def get_balance(self) -> float:
        """Get account balance."""
        return self.account_info.get("balance", 0.0)