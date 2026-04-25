"""Mean Reversion trading strategy."""
from typing import List
from datetime import datetime

from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal
from forex_bot_platform.data.provider import OHLCV

class MeanReversionStrategy(BaseStrategy):
    """Mean Reversion strategy - trades when price deviates from moving average."""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, risk_reward: float = 2.0):
        super().__init__("MeanReversion")
        self.period = period
        self.std_dev = std_dev
        self.risk_reward = risk_reward
    
    def generate_signals(self, data: List[OHLCV]) -> List[TradingSignal]:
        """Generate mean reversion signals."""
        signals = []
        
        if len(data) < self.period + 1:
            return signals
        
        for i in range(self.period, len(data)):
            current = data[i]
            lookback = data[i - self.period:i]
            
            prices = [c.close for c in lookback]
            mean_price = sum(prices) / len(prices)
            
            variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
            std_price = variance ** 0.5
            
            upper_band = mean_price + (self.std_dev * std_price)
            lower_band = mean_price - (self.std_dev * std_price)
            
            if current.close < lower_band:
                stop_loss = min(c.low for c in lookback)
                take_profit = current.close + (current.close - stop_loss) * self.risk_reward
                
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="buy",
                    price=current.close,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=f"Price below lower band: {current.close:.5f} < {lower_band:.5f}"
                )
                signals.append(signal)
            
            elif current.close > upper_band:
                stop_loss = max(c.high for c in lookback)
                take_profit = current.close - (stop_loss - current.close) * self.risk_reward
                
                signal = TradingSignal(
                    timestamp=current.timestamp,
                    action="sell",
                    price=current.close,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reason=f"Price above upper band: {current.close:.5f} > {upper_band:.5f}"
                )
                signals.append(signal)
        
        return signals