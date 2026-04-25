"""Combo trading strategy - combines multiple strategies."""
from typing import List

from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal
from forex_bot_platform.data.provider import OHLCV

class ComboStrategy(BaseStrategy):
    """Combo strategy - combines signals from multiple strategies."""
    
    def __init__(self, strategies: List[BaseStrategy], min_agreement: int = 2):
        super().__init__("Combo")
        self.strategies = strategies
        self.min_agreement = min_agreement
    
    def generate_signals(self, data: List[OHLCV]) -> List[TradingSignal]:
        """Generate combined signals from multiple strategies."""
        all_signals = {}
        
        for strategy in self.strategies:
            signals = strategy.generate_signals(data)
            for sig in signals:
                key = sig.timestamp
                if key not in all_signals:
                    all_signals[key] = []
                all_signals[key].append(sig)
        
        combined_signals = []
        
        for timestamp, signals in all_signals.items():
            if len(signals) >= self.min_agreement:
                buy_count = sum(1 for s in signals if s.action == "buy")
                sell_count = sum(1 for s in signals if s.action == "sell")
                
                if buy_count >= self.min_agreement:
                    avg_price = sum(s.price for s in signals if s.action == "buy") / buy_count
                    avg_sl = sum(s.stop_loss for s in signals if s.action == "buy" and s.stop_loss) / buy_count
                    avg_tp = sum(s.take_profit for s in signals if s.action == "buy" and s.take_profit) / buy_count
                    
                    combined = TradingSignal(
                        timestamp=timestamp,
                        action="buy",
                        price=avg_price,
                        stop_loss=avg_sl,
                        take_profit=avg_tp,
                        reason=f"Combo: {buy_count} buy signals"
                    )
                    combined_signals.append(combined)
                
                elif sell_count >= self.min_agreement:
                    avg_price = sum(s.price for s in signals if s.action == "sell") / sell_count
                    avg_sl = sum(s.stop_loss for s in signals if s.action == "sell" and s.stop_loss) / sell_count
                    avg_tp = sum(s.take_profit for s in signals if s.action == "sell" and s.take_profit) / sell_count
                    
                    combined = TradingSignal(
                        timestamp=timestamp,
                        action="sell",
                        price=avg_price,
                        stop_loss=avg_sl,
                        take_profit=avg_tp,
                        reason=f"Combo: {sell_count} sell signals"
                    )
                    combined_signals.append(combined)
        
        return combined_signals