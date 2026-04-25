"""Data provider for forex market data."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import random

@dataclass
class OHLCV:
    """OHLCV candlestick data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

class DataProvider:
    """Provides forex market data for backtesting."""
    
    def __init__(self, pair: str = "EURUSD"):
        self.pair = pair
    
    def get_historical_data(self, 
                           timeframe: str = "1h",
                           start_date: Optional[datetime] = None,
                           end_date: Optional[datetime] = None,
                           candles: int = 1000) -> List[OHLCV]:
        """Get historical OHLCV data for backtesting."""
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            start_date = end_date - timedelta(days=365)
        
        data = self._generate_synthetic_data(timeframe, start_date, end_date, candles)
        return data
    
    def _generate_synthetic_data(self, timeframe: str, 
                                  start_date: datetime, 
                                  end_date: datetime,
                                  candles: int) -> List[OHLCV]:
        """Generate synthetic forex data for backtesting."""
        base_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 149.50,
            "AUDUSD": 0.6550,
            "USDCAD": 1.3650,
            "USDCHF": 0.8850,
            "NZDUSD": 0.6050,
        }
        
        base_price = base_prices.get(self.pair, 1.0)
        data = []
        
        interval_map = {"1m": 1, "5m": 5, "15m": 15, "1h": 60, "4h": 240, "1d": 1440}
        minutes = interval_map.get(timeframe, 60)
        
        current_price = base_price
        current_time = start_date
        
        for i in range(candles):
            change = random.gauss(0, 0.001) * current_price
            current_price = max(current_price + change, base_price * 0.8)
            
            high = current_price * (1 + abs(random.gauss(0, 0.0005)))
            low = current_price * (1 - abs(random.gauss(0, 0.0005)))
            open_price = random.uniform(low, high)
            close_price = random.uniform(low, high)
            
            candle = OHLCV(
                timestamp=current_time,
                open=open_price,
                high=high,
                low=low,
                close=close_price,
                volume=random.randint(1000, 10000)
            )
            data.append(candle)
            
            current_time += timedelta(minutes=minutes)
        
        return data
    
    def get_current_price(self) -> float:
        """Get current market price (simulated)."""
        base_prices = {
            "EURUSD": 1.0850,
            "GBPUSD": 1.2650,
            "USDJPY": 149.50,
            "AUDUSD": 0.6550,
            "USDCAD": 1.3650,
            "USDCHF": 0.8850,
            "NZDUSD": 0.6050,
        }
        return base_prices.get(self.pair, 1.0)