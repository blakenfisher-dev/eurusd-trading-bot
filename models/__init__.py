from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
import pandas as pd


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1
    FLAT = 0


class TradeStatus(Enum):
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


@dataclass
class OHLC:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume
        }


@dataclass
class Trade:
    id: str
    direction: TradeDirection
    entry_price: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    quantity: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: TradeStatus = TradeStatus.PENDING
    pnl: float = 0.0
    commission: float = 0.0

    def close(self, price: float, time: datetime, reason: str = ""):
        self.exit_price = price
        self.exit_time = time
        self.status = TradeStatus.CLOSED
        
        pip_value = 10.0
        pip_diff = abs(price - self.entry_price) * 10000
        
        if self.direction == TradeDirection.LONG:
            if price > self.entry_price:
                self.pnl = pip_diff * self.quantity * pip_value
            else:
                self.pnl = -pip_diff * self.quantity * pip_value
        else:
            if price < self.entry_price:
                self.pnl = pip_diff * self.quantity * pip_value
            else:
                self.pnl = -pip_diff * self.quantity * pip_value
        
        self.pnl -= self.commission
        return self.pnl


@dataclass
class Balance:
    equity: float
    balance: float
    margin_used: float = 0.0
    free_margin: float = 0.0
    margin_level: float = 0.0


@dataclass
class TradingSignal:
    timestamp: datetime
    direction: TradeDirection
    strength: float
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}