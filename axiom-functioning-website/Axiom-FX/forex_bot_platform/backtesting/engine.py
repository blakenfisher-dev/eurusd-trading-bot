"""Backtesting engine."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from forex_bot_platform.data.provider import DataProvider, OHLCV
from forex_bot_platform.strategies.base import BaseStrategy, TradingSignal

@dataclass
class Trade:
    """Executed trade record."""
    entry_time: datetime
    exit_time: datetime
    action: str
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    pnl_pct: float
    stop_loss: float
    take_profit: float

@dataclass
class BacktestResult:
    """Results from backtesting."""
    pair: str
    strategy: str
    timeframe: str
    initial_balance: float
    final_balance: float
    total_return_pct: float
    win_rate: float
    profit_factor: float
    max_drawdown_pct: float
    trade_count: int
    average_win: float
    average_loss: float
    best_trade: float
    worst_trade: float
    trades: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "success"
    reasons: str = ""

class BacktestEngine:
    """Backtesting engine for forex strategies."""
    
    def __init__(self, initial_balance: float = 100000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.trades: List[Trade] = []
        self.equity_curve = [initial_balance]
        self.open_positions: Dict[str, Any] = {}
    
    def run(self, pair: str, strategy: BaseStrategy, timeframe: str = "1h", 
            candles: int = 1000) -> BacktestResult:
        """Run backtest on historical data."""
        provider = DataProvider(pair)
        data = provider.get_historical_data(timeframe=timeframe, candles=candles)
        
        signals = strategy.generate_signals(data)
        
        for signal in signals:
            self._process_signal(signal, data)
        
        self._close_all_positions(data[-1] if data else None)
        
        return self._generate_results(pair, strategy.name, timeframe)
    
    def _process_signal(self, signal: TradingSignal, data: List[OHLCV]):
        """Process a trading signal."""
        if signal.action == "buy" and "buy" not in self.open_positions:
            self.open_positions["buy"] = {
                "entry_price": signal.price,
                "entry_time": signal.timestamp,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "size": self.balance * 0.1
            }
        
        elif signal.action == "sell" and "sell" not in self.open_positions:
            self.open_positions["sell"] = {
                "entry_price": signal.price,
                "entry_time": signal.timestamp,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "size": self.balance * 0.1
            }
    
    def _close_all_positions(self, last_candle: Optional[OHLCV]):
        """Close all open positions at the end of backtest."""
        for action, pos in list(self.open_positions.items()):
            if last_candle:
                exit_price = last_candle.close
                pnl = (exit_price - pos["entry_price"]) * pos["size"] if action == "buy" else (pos["entry_price"] - exit_price) * pos["size"]
                self.balance += pnl
                
                trade = Trade(
                    entry_time=pos["entry_time"],
                    exit_time=last_candle.timestamp,
                    action=action,
                    entry_price=pos["entry_price"],
                    exit_price=exit_price,
                    size=pos["size"],
                    pnl=pnl,
                    pnl_pct=pnl / self.initial_balance * 100,
                    stop_loss=pos["stop_loss"],
                    take_profit=pos["take_profit"]
                )
                self.trades.append(trade)
        
        self.open_positions = {}
        self.equity_curve.append(self.balance)
    
    def _generate_results(self, pair: str, strategy_name: str, timeframe: str) -> BacktestResult:
        """Generate backtest results."""
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]
        
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        total_wins = sum(t.pnl for t in winning_trades) if winning_trades else 0
        total_losses = abs(sum(t.pnl for t in losing_trades)) if losing_trades else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        max_equity = max(self.equity_curve)
        max_drawdown = max(max_equity - e for e in self.equity_curve)
        max_drawdown_pct = (max_drawdown / max_equity) * 100 if max_equity > 0 else 0
        
        return BacktestResult(
            pair=pair,
            strategy=strategy_name,
            timeframe=timeframe,
            initial_balance=self.initial_balance,
            final_balance=self.balance,
            total_return_pct=((self.balance - self.initial_balance) / self.initial_balance) * 100,
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown_pct=max_drawdown_pct,
            trade_count=len(self.trades),
            average_win=sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            average_loss=sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            best_trade=max(t.pnl for t in self.trades) if self.trades else 0,
            worst_trade=min(t.pnl for t in self.trades) if self.trades else 0,
            trades=[{
                "entry_time": t.entry_time.isoformat(),
                "exit_time": t.exit_time.isoformat(),
                "action": t.action,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct
            } for t in self.trades]
        )