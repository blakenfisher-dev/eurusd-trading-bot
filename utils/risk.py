import numpy as np
import pandas as pd
from typing import List, Optional
from datetime import datetime
import uuid

from models import Trade, TradeDirection, TradeStatus, Balance, TradingSignal, OHLC


class RiskManager:
    def __init__(self,
                 max_risk_per_trade: float = 0.02,
                 max_daily_loss: float = 0.05,
                 max_drawdown: float = 0.15,
                 max_open_positions: int = 1,
                 max_leverage: float = 30.0):
        self.max_risk_per_trade = max_risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.max_open_positions = max_open_positions
        self.max_leverage = max_leverage
        
        self.initial_balance = 0.0
        self.daily_start_balance = 0.0
        self.daily_pnl = 0.0
        self.peak_balance = 0.0

    def calculate_position_size(self, 
                               signal: TradingSignal, 
                               account_balance: float,
                               pip_value: float = 10.0) -> float:
        
        risk_amount = account_balance * self.max_risk_per_trade
        
        if signal.stop_loss is None:
            return 0.0
            
        pip_risk = abs(signal.price - signal.stop_loss) * 10000
        
        if pip_risk < 3:
            pip_risk = 3
        
        position_size = risk_amount / (pip_risk * pip_value)
        
        max_position = (account_balance * self.max_leverage) / signal.price
        position_size = min(position_size, max_position)
        
        position_size = max(0.1, position_size)
        position_size = round(position_size, 1)
        
        return position_size

    def can_open_trade(self, 
                       current_positions: List[Trade],
                       account_balance: float,
                       daily_trades: int = 0) -> tuple[bool, str]:
        
        if len(current_positions) >= self.max_open_positions:
            return False, f"Max positions ({self.max_open_positions}) reached"
        
        if account_balance <= 0:
            return False, "Insufficient balance"
        
        if self.daily_pnl <= -self.max_daily_loss * self.initial_balance:
            return False, f"Daily loss limit reached (${self.daily_pnl:.2f})"
        
        if self.peak_balance > 0:
            current_drawdown = (self.peak_balance - account_balance) / self.peak_balance
            if current_drawdown >= self.max_drawdown:
                return False, f"Max drawdown reached ({current_drawdown*100:.1f}%)"
        
        return True, "OK"

    def validate_signal(self, signal: TradingSignal) -> tuple[bool, str]:
        if signal.strength < 0.5:
            return False, f"Signal strength too low ({signal.strength})"
        
        if signal.direction == TradeDirection.FLAT:
            return False, "No direction"
            
        return True, "OK"

    def update_daily_pnl(self, pnl: float):
        self.daily_pnl += pnl

    def reset_daily(self, balance: float):
        self.daily_start_balance = balance
        self.daily_pnl = 0.0

    def update_peak_balance(self, balance: float):
        if balance > self.peak_balance:
            self.peak_balance = balance


class PortfolioManager:
    def __init__(self, 
                 initial_balance: float = 10000.0,
                 risk_manager: Optional[RiskManager] = None):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.risk_manager = risk_manager or RiskManager()
        self.risk_manager.initial_balance = initial_balance
        self.risk_manager.peak_balance = initial_balance
        self.risk_manager.daily_start_balance = initial_balance
        
        self.trades: List[Trade] = []
        self.closed_trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.daily_returns: List[float] = []
        
        self.total_pnl = 0.0
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0

    def open_trade(self, signal: TradingSignal) -> Optional[Trade]:
        can_open, reason = self.risk_manager.can_open_trade(
            self.get_open_trades(),
            self.balance
        )
        
        if not can_open:
            return None
            
        is_valid, _ = self.risk_manager.validate_signal(signal)
        if not is_valid:
            return None
            
        position_size = self.risk_manager.calculate_position_size(
            signal, self.balance
        )
        
        if position_size <= 0:
            return None

        trade = Trade(
            id=str(uuid.uuid4())[:8],
            direction=signal.direction,
            entry_price=signal.price,
            entry_time=signal.timestamp,
            quantity=position_size,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            status=TradeStatus.OPEN
        )
        
        self.trades.append(trade)
        self.total_trades += 1
        
        return trade

    def close_trade(self, trade: Trade, price: float, time: datetime, reason: str = "") -> float:
        pnl = trade.close(price, time, reason)
        
        self.trades.remove(trade)
        self.closed_trades.append(trade)
        
        self.balance += pnl
        self.equity += pnl
        self.total_pnl += pnl
        
        self.risk_manager.update_daily_pnl(pnl)
        self.risk_manager.update_peak_balance(self.balance)
        
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
            
        return pnl

    def check_stops(self, current_price: float, current_time: datetime) -> List[tuple[Trade, str, float]]:
        triggered = []
        
        for trade in self.trades:
            if trade.stop_loss is not None:
                if trade.direction == TradeDirection.LONG and current_price <= trade.stop_loss:
                    triggered.append((trade, "stop_loss", trade.stop_loss))
                elif trade.direction == TradeDirection.SHORT and current_price >= trade.stop_loss:
                    triggered.append((trade, "stop_loss", trade.stop_loss))
                    
            if trade.take_profit is not None:
                if trade.direction == TradeDirection.LONG and current_price >= trade.take_profit:
                    triggered.append((trade, "take_profit", trade.take_profit))
                elif trade.direction == TradeDirection.SHORT and current_price <= trade.take_profit:
                    triggered.append((trade, "take_profit", trade.take_profit))
                    
        return triggered

    def get_open_trades(self) -> List[Trade]:
        return [t for t in self.trades if t.status == TradeStatus.OPEN]

    def get_equity(self) -> float:
        open_pnl = 0.0
        for trade in self.trades:
            if trade.direction == TradeDirection.LONG:
                open_pnl += (self.equity - trade.entry_price) * trade.quantity
            else:
                open_pnl += (trade.entry_price - self.equity) * trade.quantity
        return self.balance + open_pnl

    def get_stats(self) -> dict:
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0
        
        avg_win = 0.0
        avg_loss = 0.0
        if self.winning_trades > 0:
            wins = [t.pnl for t in self.closed_trades if t.pnl > 0]
            avg_win = sum(wins) / len(wins) if wins else 0
        if self.losing_trades > 0:
            losses = [t.pnl for t in self.closed_trades if t.pnl < 0]
            avg_loss = abs(sum(losses) / len(losses)) if losses else 0
        
        profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        return {
            'balance': self.balance,
            'equity': self.equity,
            'total_pnl': self.total_pnl,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'open_positions': len(self.trades)
        }