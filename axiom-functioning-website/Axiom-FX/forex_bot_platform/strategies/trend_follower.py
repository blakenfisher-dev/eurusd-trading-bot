"""Trend Follower trading strategy."""
from typing import List
from datetime import datetime

from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal
from forex_bot_platform.data.provider import OHLCV

class TrendFollowerStrategy(BaseStrategy):
    """Trend Follower strategy - follows moving average trends."""
    
    def __init__(self, fast_ma: int = 10, slow_ma: int = 50, risk_reward: float = 2.0):
        super().__init__("TrendFollower")
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.risk_reward = risk_reward
    
    def generate_signals(self, data: List[OHLCV]) -> List[TradingSignal]:
        """Generate trend follower signals based on moving average crossovers."""
        signals = []
        
        if len(data) < self.slow_ma + 1:
            return signals
        
        for i in range(self.slow_ma, len(data)):
            current = data[i]
            
            fast_ma = sum(c.close for c in data[i - self.fast_ma:i]) / self.fast_ma
            slow_ma = sum(c.close for c in data[i - self.slow_ma:i]) / self.slow_ma
            
            prev_fast_ma = sum(c.close for c in data[i - self.fast_ma - 1:i - 1]) / self.fast_ma
            prev_slow_ma = sum(c.close for c in data[i - self.slow_ma - 1:i - 1]) / self.slow_ma
            
            if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
                stop_loss = min(c.low for c in data[i - self.fast_ma:i])
                take_profit = current.close + (current.close - stop_loss) * self.risk_reward
                
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="buy",
                    price=current.close,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=f"MA crossover: fast={fast_ma:.5f}, slow={slow_ma:.5f}"
                )
                signals.append(signal)
            
            elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
                stop_loss = max(c.high for c in data[i - self.fast_ma:i])
                take_profit = current.close - (stop_loss - current.close) * self.risk_reward
                
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="sell",
                    price=current.close,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=f"MA crossover: fast={fast_ma:.5f}, slow={slow_ma:.5f}"
                )
                signals.append(signal)
        
        return signals