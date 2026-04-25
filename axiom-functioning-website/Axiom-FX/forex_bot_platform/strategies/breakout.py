"""Breakout trading strategy."""
from typing import List
from datetime import datetime

from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal
from forex_bot_platform.data.provider import OHLCV

class BreakoutStrategy(BaseStrategy):
    """Breakout strategy - trades when price breaks resistance/support levels."""
    
    def __init__(self, lookback: int = 20, risk_reward: float = 2.0):
        super().__init__("Breakout")
        self.lookback = lookback
        self.risk_reward = risk_reward
    
    def generate_signals(self, data: List[OHLCV]) -> List[TradingSignal]:
        """Generate breakout signals."""
        signals = []
        
        if len(data) < self.lookback + 1:
            return signals
        
        for i in range(self.lookback, len(data)):
            current = data[i]
            lookback_data = data[i - self.lookback:i]
            
            highest = max(c.high for c in lookback_data)
            lowest = min(c.low for c in lookback_data)
            
            if current.close > highest:
                stop_loss = lowest
                take_profit = current.close + (current.close - stop_loss) * self.risk_reward
                
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="buy",
                    price=current.close,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=f"Breakout above {highest:.5f}"
                )
                signals.append(signal)
            
            elif current.close < lowest:
                stop_loss = highest
                take_profit = current.close - (stop_loss - current.close) * self.risk_reward
                
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="sell",
                    price=current.close,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=f"Breakout below {lowest:.5f}"
                )
                signals.append(signal)
        
        return signals