"""MT5 Demo Trading Mode (Phase 3).

This module provides MT5 demo account integration for testing strategies
with real market data but demo/lite money only. Live accounts are BLOCKED.

Demo Trading Mode uses live market data from MT5 but places demo orders only.
No real money is used. All live/real accounts are blocked.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import pandas as pd

class AccountType(Enum):
    DEMO = "demo"
    LIVE = "live"
    UNKNOWN = "unknown"

class OrderSide(Enum):
    BUY = 1
    SELL = -1

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"

@dataclass
class DemoAccount:
    account_id: int = 0
    login: str = ""
    server: str = ""
    account_type: AccountType = AccountType.UNKNOWN
    balance: float = 0.0
    equity: float = 0.0
    currency: str = "USD"
    leverage: int = 100
    is_connected: bool = False

@dataclass
class DemoPosition:
    ticket: int = 0
    symbol: str = ""
    side: OrderSide = OrderSide.BUY
    volume: float = 0.0
    entry_price: float = 0.0
    current_price: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    open_time: datetime = None
    profit: float = 0.0
    comment: str = ""

@dataclass
class SafetyConfig:
    max_daily_loss: float = 1000.0
    max_open_trades: int = 3
    max_exposure_per_currency: float = 10000.0
    max_spread: float = 3.0
    require_stop_loss: bool = True
    allow_demo_only: bool = True
    max_trades_per_day: int = 10
    cooldown_seconds: int = 30

@dataclass
class DailyStats:
    date: str = ""
    start_balance: float = 0.0
    realized_pnl: float = 0.0
    open_trades_count: int = 0
    closed_trades_count: int = 0
    emergency_stop_triggered: bool = False
    blocked_reason: Optional[str] = None

@dataclass
class AuditLogEntry:
    timestamp: datetime = None
    action: str = ""
    details: str = ""
    success: bool = True

@dataclass
class RejectionRecord:
    timestamp: datetime = None
    order_symbol: str = ""
    order_side: str = ""
    volume: float = 0.0
    reason: str = ""

class DemoTradingError(Exception):
    """Raised when demo trading safety check fails."""
    pass

class LiveAccountBlockedError(DemoTradingError):
    """Raised when a live account is detected."""
    pass

class SafetyCheckFailedError(DemoTradingError):
    """Raised when a safety check fails."""
    pass

class MT5DemoExecutor:
    """MT5 Demo Trading executor - demo accounts only, no real money."""
    
    def __init__(self, login: Optional[str] = None, password: Optional[str] = None, 
                 server: Optional[str] = None, safety_config: Optional[SafetyConfig] = None):
        self.login = login
        self.password = password  
        self.server = server
        self.safety_config = safety_config or SafetyConfig()
        self.account: Optional[DemoAccount] = None
        self.positions: List[DemoPosition] = []
        self.order_history: List[DemoPosition] = []
        self.next_ticket: int = 1
        self.is_connected: bool = False
        self.session_start: Optional[datetime] = None
        self.daily_stats: DailyStats = DailyStats()
        self._is_initialized: bool = False
        self._last_order_time: Optional[datetime] = None
        self._consecutive_failures: int = 0
        self.audit_log: List[AuditLogEntry] = []
        self.rejection_history: List[RejectionRecord] = []
        self._session_persisted: bool = False

    def connect(self) -> bool:
        """Connect to MT5 demo account. Returns True if connected to demo account."""
        if self._is_initialized:
            return self.is_connected
            
        # Try to initialize MT5 connection (mock for now)
        # In production, would use: import MetaTrader5 as mt5; mt5.initialize()
        if not self.is_connected:
            self._init_mt5()
        
        if not self.is_connected:
            return False
            
        # Verify account type - only DEMO allowed
        if self.account and self.account.account_type != AccountType.DEMO:
            raise LiveAccountBlockedError(
                f"Live account detected ({self.account.account_type.value}). "
                "Demo Trading Mode requires demo account only."
            )
            
        if self.account and self.account.account_type == AccountType.UNKNOWN:
            raise LiveAccountBlockedError(
                "Cannot verify account type. Trading blocked for safety."
            )
            
        self.session_start = datetime.now(timezone.utc)
        self.daily_stats = DailyStats(
            date=self.session_start.date().isoformat(),
            start_balance=self.account.balance if self.account else 0.0
        )
        self._is_initialized = True
        return True

    def _init_mt5(self):
        """Initialize MT5 connection. In production, uses real MT5 API."""
        # Scaffold: in production would be:
        # import MetaTrader5 as mt5
        # mt5.initialize(login=login, password=password, server=server)
        # account_info = mt5.account_info()
        
        # For demo, we simulate a demo account
        if self.login and self.server:
            # In production: verify credentials with MT5
            # For now: simulate demo account
            self.account = DemoAccount(
                account_id=self.next_ticket,
                login=self.login,
                server=self.server,
                account_type=AccountType.DEMO,
                balance=100000.0,
                equity=100000.0,
                currency="USD",
                leverage=100,
                is_connected=True
            )
            self.is_connected = True
        else:
            self.is_connected = False

    def disconnect(self):
        """Disconnect from MT5."""
        if self.is_connected:
            # In production: mt5.shutdown()
            self.is_connected = False
            self.account = None
            self._is_initialized = False

    def get_account_info(self) -> Dict[str, Any]:
        """Get account information. Returns {} if not connected."""
        if not self.is_connected or not self.account:
            return {}
        return {
            "account_id": self.account.account_id,
            "login": self.account.login,
            "server": self.account.server,
            "account_type": self.account.account_type.value,
            "balance": self.account.balance,
            "equity": self.account.equity,
            "currency": self.account.currency,
            "leverage": self.account.leverage,
        }

    def get_symbol_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get symbol info. Returns None if symbol not found."""
        if not self.is_connected:
            return None
        # In production: mt5.symbol_info(symbol)
        # Demo: return mock data
        return {
            "symbol": symbol,
            "bid": 1.0950,
            "ask": 1.0952,
            "spread": 2,
            "digits": 5,
            "trade_contract_size": 100000,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
        }

    def get_latest_tick(self, symbol: str) -> Optional[Dict[str, str]]:
        """Get latest tick for symbol."""
        if not self.is_connected:
            return None
        # In production: mt5.symbol_info_tick(symbol)
        return {
            "symbol": symbol,
            "time": datetime.now(timezone.utc).isoformat(),
            "bid": 1.0950,
            "ask": 1.0952,
        }

    def _safety_checks(self, symbol: str, side: OrderSide, volume: float,
                       stop_loss: Optional[float], take_profit: Optional[float]) -> None:
        """Run all safety checks before placing an order."""
        # Check connection
        if not self.is_connected:
            self._log_audit("safety_check", "Not connected to MT5", success=False)
            raise SafetyCheckFailedError("Not connected to MT5")
        
        # Check account type
        if self.account and self.account.account_type != AccountType.DEMO:
            self._log_audit("safety_check", f"Live account {self.account.account_type.value} not allowed", success=False)
            raise LiveAccountBlockedError(
                f"Live account ({self.account.account_type.value}) not allowed"
            )
        
        # Check account type unknown
        if self.account and self.account.account_type == AccountType.UNKNOWN:
            self._log_audit("safety_check", "Unknown account type", success=False)
            raise LiveAccountBlockedError("Cannot verify account type")
        
        # Check stop-loss required
        if self.safety_config.require_stop_loss and stop_loss is None:
            self._record_rejection(symbol, side, volume, "Stop-loss required")
            raise SafetyCheckFailedError(
                "Stop-loss required for demo trading"
            )
        
        # Check max open trades
        if len(self.positions) >= self.safety_config.max_open_trades:
            self._record_rejection(symbol, side, volume, f"Max open trades {self.safety_config.max_open_trades}")
            raise SafetyCheckFailedError(
                f"Max open trades ({self.safety_config.max_open_trades}) reached"
            )
        
        # Check max trades per day
        if self.daily_stats.closed_trades_count >= self.safety_config.max_trades_per_day:
            self._record_rejection(symbol, side, volume, f"Max trades per day {self.safety_config.max_trades_per_day}")
            raise SafetyCheckFailedError(
                f"Max trades per day ({self.safety_config.max_trades_per_day}) reached"
            )
        
        # Check cooldown
        if self._last_order_time:
            elapsed = (datetime.now(timezone.utc) - self._last_order_time).total_seconds()
            if elapsed < self.safety_config.cooldown_seconds:
                self._record_rejection(symbol, side, volume, f"Cooldown active ({self.safety_config.cooldown_seconds}s)")
                raise SafetyCheckFailedError(
                    f"Cooldown active. Wait {int(self.safety_config.cooldown_seconds - elapsed)}s"
                )
        
        # Check duplicate order
        for p in self.positions:
            if p.symbol == symbol and p.side == side:
                self._record_rejection(symbol, side, volume, f"Duplicate position")
                raise SafetyCheckFailedError(
                    f"Duplicate position: {symbol} {side.name} already open"
                )
        
        # Check max exposure per currency
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info:
            exposure = volume * symbol_info.get("trade_contract_size", 100000)
            if exposure > self.safety_config.max_exposure_per_currency:
                self._record_rejection(symbol, side, volume, f"Max exposure exceeded")
                raise SafetyCheckFailedError(
                    f"Max exposure {self.safety_config.max_exposure_per_currency} exceeded"
                )
        
        # Check spread
        if symbol_info and symbol_info.get("spread", 0) > self.safety_config.max_spread:
            self._record_rejection(symbol, side, volume, f"Spread too high")
            raise SafetyCheckFailedError(
                f"Spread too high: {symbol_info['spread']} > {self.safety_config.max_spread}"
            )
        
        # Check max daily loss
        if self.daily_stats.realized_pnl < -self.safety_config.max_daily_loss:
            self._record_rejection(symbol, side, volume, f"Max daily loss reached")
            raise SafetyCheckFailedError(
                f"Max daily loss reached: {self.daily_stats.realized_pnl}"
            )
            
        # Check trading hours - skip in demo mode for testing
        # In production: check if market is open
        # now = datetime.now(timezone.utc)
        # if now.weekday() >= 5:  # Weekend
        #     raise SafetyCheckFailedError("Trading not allowed on weekends")

    def place_demo_order(self, symbol: str, side: OrderSide, volume: float,
                       stop_loss: Optional[float] = None, 
                       take_profit: Optional[float] = None,
                       comment: str = "") -> int:
        """Place a demo order. Returns ticket number or raises on error."""
        # Run safety checks first
        self._safety_checks(symbol, side, volume, stop_loss, take_profit)
        
        # Get current price
        tick = self.get_latest_tick(symbol)
        entry_price = tick["ask"] if side == OrderSide.BUY else tick["bid"]
        
        # Create position
        position = DemoPosition(
            ticket=self.next_ticket,
            symbol=symbol,
            side=side,
            volume=volume,
            entry_price=entry_price,
            current_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            open_time=datetime.now(timezone.utc),
            comment=comment
        )
        
        self.positions.append(position)
        self.next_ticket += 1
        
        # Update daily stats
        self.daily_stats.open_trades_count = len(self.positions)
        
        return position.ticket

    def close_demo_order(self, ticket: int) -> bool:
        """Close a demo order by ticket. Returns True if closed."""
        for i, p in enumerate(self.positions):
            if p.ticket == ticket:
                # Calculate PnL
                tick = self.get_latest_tick(p.symbol)
                exit_price = tick["bid"] if p.side == OrderSide.BUY else tick["ask"]
                p.current_price = exit_price
                
                # Calculate profit
                if p.side == OrderSide.BUY:
                    p.profit = (exit_price - p.entry_price) * p.volume * 100000
                else:
                    p.profit = (p.entry_price - exit_price) * p.volume * 100000
                    
                # Update balance
                if self.account:
                    self.account.balance += p.profit
                    self.account.equity += p.profit
                    
                # Move to history
                self.order_history.append(p)
                self.positions.pop(i)
                
                # Update daily stats
                self.daily_stats.realized_pnl += p.profit
                self.daily_stats.closed_trades_count += 1
                self.daily_stats.open_trades_count = len(self.positions)
                
                return True
        return False

    def modify_stop_loss_take_profit(self, ticket: int, stop_loss: Optional[float], 
                                take_profit: Optional[float]) -> bool:
        """Modify stop loss and take profit for an order."""
        for p in self.positions:
            if p.ticket == ticket:
                p.stop_loss = stop_loss
                p.take_profit = take_profit
                return True
        return False

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions."""
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "side": p.side.value,
                "volume": p.volume,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "profit": p.profit,
                "open_time": p.open_time.isoformat() if p.open_time else None,
            }
            for p in self.positions
        ]

    def get_order_history(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get order history."""
        return [
            {
                "ticket": p.ticket,
                "symbol": p.symbol,
                "side": p.side.value,
                "volume": p.volume,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "profit": p.profit,
                "close_time": p.open_time.isoformat() if p.open_time else None,
            }
            for p in self.order_history[-count:]
        ]

    def emergency_stop(self) -> str:
        """Trigger emergency stop. Returns reason."""
        self.daily_stats.emergency_stop_triggered = True
        self.daily_stats.blocked_reason = "emergency_stop"
        
        # Close all positions at current price
        for p in list(self.positions):
            self.close_demo_order(p.ticket)
            
        self.disconnect()
        return "emergency_stop_triggered"

    def get_safety_status(self) -> Dict[str, Any]:
        """Get current safety status."""
        return {
            "is_connected": self.is_connected,
            "account_type": self.account.account_type.value if self.account else "unknown",
            "daily_pnl": self.daily_stats.realized_pnl,
            "max_daily_loss": self.safety_config.max_daily_loss,
            "open_trades": len(self.positions),
            "max_open_trades": self.safety_config.max_open_trades,
            "emergency_stop": self.daily_stats.emergency_stop_triggered,
        }

    def get_daily_stats(self) -> Dict[str, Any]:
        """Get daily statistics."""
        return {
            "date": self.daily_stats.date,
            "start_balance": self.daily_stats.start_balance,
            "realized_pnl": self.daily_stats.realized_pnl,
            "open_trades": self.daily_stats.open_trades_count,
            "closed_trades": self.daily_stats.closed_trades_count,
            "emergency_stop": self.daily_stats.emergency_stop_triggered,
            "blocked_reason": self.daily_stats.blocked_reason,
        }

    def _log_audit(self, action: str, details: str, success: bool = True) -> None:
        """Log an audit entry."""
        entry = AuditLogEntry(
            timestamp=datetime.now(timezone.utc),
            action=action,
            details=details,
            success=success
        )
        self.audit_log.append(entry)
    
    def _record_rejection(self, symbol: str, side: OrderSide, volume: float, reason: str) -> None:
        """Record a rejected order."""
        record = RejectionRecord(
            timestamp=datetime.now(timezone.utc),
            order_symbol=symbol,
            order_side=side.name,
            volume=volume,
            reason=reason
        )
        self.rejection_history.append(record)
        self._consecutive_failures += 1
        self.daily_stats.blocked_reason = reason
    
    def get_audit_log(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get recent audit log entries."""
        return [
            {
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "action": e.action,
                "details": e.details,
                "success": e.success
            }
            for e in self.audit_log[-count:]
        ]
    
    def get_rejection_report(self, count: int = 50) -> List[Dict[str, Any]]:
        """Get rejection history."""
        return [
            {
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "symbol": r.order_symbol,
                "side": r.order_side,
                "volume": r.volume,
                "reason": r.reason
            }
            for r in self.rejection_history[-count:]
        ]
    
    def recover_session(self, session_file: str) -> bool:
        """Recover session from file."""
        if not os.path.exists(session_file):
            return False
        try:
            with open(session_file, 'r') as f:
                data = json.load(f)
            self.daily_stats.date = data.get("date", "")
            self.daily_stats.start_balance = data.get("start_balance", 100000.0)
            self.daily_stats.realized_pnl = data.get("realized_pnl", 0.0)
            self.daily_stats.closed_trades_count = data.get("closed_trades_count", 0)
            self._session_persisted = True
            return True
        except Exception:
            return False
    
    def save_session(self, session_file: str) -> bool:
        """Persist session to file."""
        try:
            data = {
                "date": self.daily_stats.date,
                "start_balance": self.daily_stats.start_balance,
                "realized_pnl": self.daily_stats.realized_pnl,
                "closed_trades_count": self.daily_stats.closed_trades_count,
            }
            with open(session_file, 'w') as f:
                json.dump(data, f)
            self._session_persisted = True
            return True
        except Exception:
            return False

class DemoSoakConfig:
    def __init__(self, max_runtime_seconds: int = 3600, max_trades: int = 10,
                 max_daily_loss: float = 1000.0, max_drawdown_pct: float = 10.0,
                 heartbeat_interval: int = 30):
        self.max_runtime_seconds = max_runtime_seconds
        self.max_trades = max_trades
        self.max_daily_loss = max_daily_loss
        self.max_drawdown_pct = max_drawdown_pct
        self.heartbeat_interval = heartbeat_interval

class DemoSoakTest:
    def __init__(self, executor: MT5DemoExecutor, config: DemoSoakConfig):
        self.executor = executor
        self.config = config
        self.status = "initialized"
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.trades_placed = 0
        self.heartbeat_count = 0
        self.last_heartbeat: Optional[datetime] = None
        self.stop_reason: Optional[str] = None
        self._running = False

    def start(self, allow_orders: bool = False) -> bool:
        """Start soak test."""
        if self._running:
            return False
        
        self.executor.connect()
        if not self.executor.is_connected:
            self.status = "connection_failed"
            return False
        
        self.start_time = datetime.now(timezone.utc)
        self._running = True
        self.status = "running" if allow_orders else "validation_only"
        self._log_heartbeat("start")
        return True

    def step(self) -> Dict[str, Any]:
        """Step through soak test. Returns status."""
        if not self._running:
            return self._get_status()
        
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Check runtime
        if elapsed >= self.config.max_runtime_seconds:
            self._stop("max_runtime")
            return self._get_status()
        
        # Check trades
        if self.trades_placed >= self.config.max_trades:
            self._stop("max_trades")
            return self._get_status()
        
        # Check connection
        if not self.executor.is_connected:
            self._stop("connection_lost")
            return self._get_status()
        
        # Check daily loss
        pnl = self.executor.daily_stats.realized_pnl
        if pnl < -self.config.max_daily_loss:
            self._stop("max_daily_loss")
            return self._get_status()
        
        # Check emergency
        if self.executor.daily_stats.emergency_stop_triggered:
            self._stop("emergency_stop")
            return self._get_status()
        
        # Heartbeat
        if not self.last_heartbeat or (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds() >= self.config.heartbeat_interval:
            self._log_heartbeat("heartbeat")
        
        return self._get_status()

    def _log_heartbeat(self, action: str):
        self.heartbeat_count += 1
        self.last_heartbeat = datetime.now(timezone.utc)
        self.executor._log_audit(f"soak_{action}", f"trades={self.trades_placed}, status={self.status}")

    def _stop(self, reason: str):
        self.status = "stopped"
        self.stop_reason = reason
        self._running = False
        self.end_time = datetime.now(timezone.utc)
        self._log_heartbeat(f"stop_{reason}")

    def stop(self, reason: str = "manual"):
        """Manually stop soak test."""
        self._stop(reason)

    def _get_status(self) -> Dict[str, Any]:
        elapsed = 0
        if self.start_time:
            elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return {
            "status": self.status,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "elapsed_seconds": elapsed,
            "trades_placed": self.trades_placed,
            "heartbeat_count": self.heartbeat_count,
            "stop_reason": self.stop_reason,
            "is_validation_only": self.status == "validation_only",
            "executor_connected": self.executor.is_connected,
            "executor_daily_pnl": self.executor.daily_stats.realized_pnl,
            "executor_open_trades": len(self.executor.positions),
            "emergency_stop": self.executor.daily_stats.emergency_stop_triggered,
        }

    def export_reports(self, output_dir: str = "."):
        """Export soak test reports."""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # Report JSON
        status = self._get_status()
        with open(os.path.join(output_dir, "demo_soak_report.json"), "w") as f:
            json.dump(status, f, indent=2)
        
        # Trades CSV
        if self.executor.order_history:
            trades_data = [
                {"ticket": p.ticket, "symbol": p.symbol, "side": p.side.name,
                 "volume": p.volume, "entry": p.entry_price, "profit": p.profit}
                for p in self.executor.order_history
            ]
            pd.DataFrame(trades_data).to_csv(os.path.join(output_dir, "demo_soak_trades.csv"), index=False)
        
        # Rejections JSON
        rejections = self.executor.get_rejection_report(count=100)
        with open(os.path.join(output_dir, "demo_soak_rejections.json"), "w") as f:
            json.dump(rejections, f, indent=2)
        
        # Audit log
        audit = self.executor.get_audit_log(count=500)
        with open(os.path.join(output_dir, "demo_soak_audit.log"), "w") as f:
            for entry in audit:
                f.write(f"{entry['timestamp']} {entry['action']} {entry['details']} {entry['success']}\n")