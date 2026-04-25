"""Configuration settings for Axiom FX."""
from dataclasses import dataclass
from typing import Optional

DEFAULT_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD"]
DEFAULT_TIMEFRAMES = ["1m", "5m", "15m", "1h", "4h", "1d"]

@dataclass
class BacktestConfig:
    pair: str = "EURUSD"
    timeframe: str = "1h"
    start_date: Optional[str] = None
    initial_balance: float = 100000.0

@dataclass
class RiskConfig:
    risk_per_trade: float = 0.01
    max_daily_loss: float = 1000.0
    max_drawdown: float = 0.20
    max_open_trades: int = 3
    min_spread: float = 0.5
    require_stop_loss: bool = True

@dataclass
class DemoConfig:
    login: str = ""
    server: str = "MetaQuotes-Demo"
    password: str = ""

LIVE_MODE_ENABLED = False
APPROVAL_FILE = "live_approval.json"
EMERGENCY_STOP_FILE = "emergency_stop.json"