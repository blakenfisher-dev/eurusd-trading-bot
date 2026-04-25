"""SuperTrend trading strategy."""
from typing import List
from datetime import datetime

from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal
from forex_bot_platform.data.provider import OHLCV

class SuperTrendStrategy(BaseStrategy):
    """SuperTrend strategy - trend-following indicator strategy."""
    
    def __init__(self, period: int = 10, multiplier: float = 3.0, risk_reward: float = 2.0):
        super().__init__("SuperTrend")
        self.period = period
        self.multiplier = multiplier
        self.risk_reward = risk_reward
    
    def generate_signals(self, data: List[OHLCV]) -> List[TradingSignal]:
        """Generate SuperTrend signals."""
        signals = []
        
        if len(data) < self.period + 1:
            return signals
        
        atr_values = self._calculate_atr(data)
        
        for i in range(self.period, len(data)):
            current = data[i]
            upper_band = current.close + (self.multiplier * atr_values[i - self.period])
            lower_band = current.close - (self.multiplier * atr_values[i - self.period])
            
            prev_close = data[i - 1].close
            
            if prev_close > upper_band and current.close < upper_band:
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="sell",
                    price=current.close,
                    stop_loss=upper_band,
                    take_profit=current.close - (upper_band - lower_band) * self.risk_reward,
                    reason="SuperTrend trend reversal to down"
                )
                signals.append(signal)
            
            elif prev_close < lower_band and current.close > lower_band:
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="buy",
                    price=current.close,
                    stop_loss=lower_band,
                    take_profit=current.close + (upper_band - lower_band) * self.risk_reward,
                    reason="SuperTrend trend reversal to up"
                )
                signals.append(signal)
        
        return signals
    
    def _calculate_atr(self, data: List[OHLCV]) -> List[float]:
        """Calculate Average True Range."""
        atr = []
        
        for i in range(len(data)):
            if i == 0:
                tr = data[i].high - data[i].low
            else:
                tr = max(
                    data[i].high - data[i].low,
                    abs(data[i].high - data[i - 1].close),
                    abs(data[i].low - data[i - 1].close)
                )
            atr.append(tr)
        
        return atr