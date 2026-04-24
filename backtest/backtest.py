import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Callable
import matplotlib.pyplot as plt
from collections import defaultdict

from models import TradeDirection, TradeStatus, TradingSignal
from utils.risk import PortfolioManager, RiskManager
from strategies.strategies import BaseStrategy


class Backtester:
    def __init__(self,
                 initial_balance: float = 10000.0,
                 spread: float = 0.00015,
                 commission: float = 0.0,
                 slippage: float = 0.00005):
        self.initial_balance = initial_balance
        self.spread = spread
        self.commission = commission
        self.slippage = slippage
        
        self.portfolio = PortfolioManager(initial_balance)
        self.risk_manager = self.portfolio.risk_manager
        
        self.trades_history: List[dict] = []
        self.equity_curve: List[float] = []
        self.daily_balance: Dict[str, float] = {}
        
    def apply_spread(self, price: float, direction: TradeDirection) -> float:
        if direction == TradeDirection.LONG:
            return price + self.spread
        else:
            return price - self.spread

    def apply_slippage(self, price: float) -> float:
        return price * (1 + np.random.uniform(-self.slippage, self.slippage))

    def run(self,
            data: pd.DataFrame,
            strategy: BaseStrategy,
            progress_callback: Optional[Callable] = None) -> Dict:
        
        df = strategy.prepare_indicators(data)
        signals = strategy.analyze(df)
        signal_dict = {sig.timestamp: sig for sig in signals}
        
        self.portfolio = PortfolioManager(self.initial_balance)
        self.trades_history = []
        self.equity_curve = []
        self.daily_balance = {}
        
        for idx, row in df.iterrows():
            current_price = row['close']
            current_time = row['timestamp']
            current_date = current_time.date() if isinstance(current_time, datetime) else current_time
            
            if current_date not in self.daily_balance:
                self.daily_balance[current_date] = self.portfolio.balance
            
            self.equity_curve.append(self.portfolio.balance)
            
            if len(self.portfolio.trades) > 0:
                self.portfolio.equity = self.portfolio.balance
            
            triggered_stops = self.portfolio.check_stops(current_price, current_time)
            
            closed_trade_ids = set()
            for trade, reason, exit_price in triggered_stops:
                if trade.id in closed_trade_ids:
                    continue
                final_price = self.apply_slippage(exit_price)
                final_price = self.apply_spread(final_price, trade.direction)
                
                pnl = self.portfolio.close_trade(trade, final_price, current_time, reason)
                closed_trade_ids.add(trade.id)
                
                self.trades_history.append({
                    'trade_id': trade.id,
                    'direction': trade.direction.name,
                    'entry_price': trade.entry_price,
                    'exit_price': final_price,
                    'entry_time': trade.entry_time,
                    'exit_time': current_time,
                    'quantity': trade.quantity,
                    'pnl': pnl,
                    'reason': reason,
                    'strategy': strategy.name
                })
            
            if current_time in signal_dict:
                signal = signal_dict[current_time]
                
                can_open, _ = self.risk_manager.can_open_trade(
                    self.portfolio.get_open_trades(),
                    self.portfolio.balance
                )
                
                if can_open and signal.strength >= 0.6:
                    entry_price = self.apply_spread(
                        self.apply_slippage(signal.price),
                        signal.direction
                    )
                    
                    signal_adjusted = TradingSignal(
                        timestamp=signal.timestamp,
                        direction=signal.direction,
                        strength=signal.strength,
                        price=entry_price,
                        stop_loss=signal.stop_loss,
                        take_profit=signal.take_profit,
                        strategy=signal.strategy
                    )
                    
                    trade = self.portfolio.open_trade(signal_adjusted)
                    
                    if trade:
                        pass
            
            if progress_callback and idx % 100 == 0:
                progress_callback(idx / len(df))
        
        for trade in self.portfolio.trades[:]:
            final_price = self.apply_spread(
                self.apply_slippage(current_price),
                trade.direction
            )
            pnl = self.portfolio.close_trade(trade, final_price, current_time, "end_of_backtest")
            
            self.trades_history.append({
                'trade_id': trade.id,
                'direction': trade.direction.name,
                'entry_price': trade.entry_price,
                'exit_price': final_price,
                'entry_time': trade.entry_time,
                'exit_time': current_time,
                'quantity': trade.quantity,
                'pnl': pnl,
                'reason': 'end_of_backtest',
                'strategy': strategy.name
            })
        
        return self.get_results()

    def get_results(self) -> Dict:
        stats = self.portfolio.get_stats()
        
        if len(self.equity_curve) > 0:
            equity = pd.Series(self.equity_curve)
            returns = equity.pct_change().dropna()
            
            sharpe_ratio = 0.0
            if len(returns) > 0 and returns.std() > 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252 * 24)
            
            max_dd = 0.0
            peak = equity.iloc[0]
            for val in equity:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd
        else:
            sharpe_ratio = 0.0
            max_dd = 0.0
        
        results = {
            **stats,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_dd,
            'trades': self.trades_history,
            'equity_curve': self.equity_curve,
            'daily_balance': self.daily_balance
        }
        
        return results

    def plot_results(self, results: Dict, save_path: Optional[str] = None):
        fig, axes = plt.subplots(3, 1, figsize=(14, 12))
        
        equity_curve = results['equity_curve']
        axes[0].plot(equity_curve, color='blue', linewidth=1.5)
        axes[0].axhline(y=self.initial_balance, color='gray', linestyle='--', alpha=0.7)
        axes[0].set_title('Equity Curve', fontsize=14, fontweight='bold')
        axes[0].set_ylabel('Balance ($)')
        axes[0].grid(True, alpha=0.3)
        
        trades_df = pd.DataFrame(results['trades'])
        if len(trades_df) > 0:
            trades_df['cumulative_pnl'] = trades_df['pnl'].cumsum()
            axes[1].plot(trades_df.index, trades_df['cumulative_pnl'], color='green', linewidth=1.5)
            axes[1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
            axes[1].fill_between(trades_df.index, 0, trades_df['cumulative_pnl'],
                               where=trades_df['cumulative_pnl'] >= 0, color='green', alpha=0.3)
            axes[1].fill_between(trades_df.index, 0, trades_df['cumulative_pnl'],
                               where=trades_df['cumulative_pnl'] < 0, color='red', alpha=0.3)
        axes[1].set_title('Cumulative P&L', fontsize=14, fontweight='bold')
        axes[1].set_ylabel('P&L ($)')
        axes[1].grid(True, alpha=0.3)
        
        daily_returns = []
        dates = []
        for date, balance in sorted(results['daily_balance'].items()):
            if len(dates) > 0:
                prev_balance = results['daily_balance'][dates[-1]]
                daily_return = (balance - prev_balance) / prev_balance
                daily_returns.append(daily_return * 100)
            dates.append(date)
        
        if len(daily_returns) > 0:
            colors = ['green' if r >= 0 else 'red' for r in daily_returns]
            axes[2].bar(range(len(daily_returns)), daily_returns, color=colors, alpha=0.7)
        axes[2].set_title('Daily Returns (%)', fontsize=14, fontweight='bold')
        axes[2].set_ylabel('Return (%)')
        axes[2].set_xlabel('Trading Days')
        axes[2].grid(True, alpha=0.3)
        axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
        
        plt.show()

    def print_results(self, results: Dict):
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Final Balance:      ${results['balance']:.2f}")
        print(f"Total P&L:          ${results['total_pnl']:.2f}")
        print(f"Total Trades:       {results['total_trades']}")
        print(f"Winning Trades:     {results['winning_trades']}")
        print(f"Losing Trades:      {results['losing_trades']}")
        print(f"Win Rate:           {results['win_rate']*100:.2f}%")
        print(f"Average Win:        ${results['avg_win']:.2f}")
        print(f"Average Loss:       ${results['avg_loss']:.2f}")
        print(f"Profit Factor:      {results['profit_factor']:.2f}")
        print(f"Sharpe Ratio:       {results['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:       {results['max_drawdown']*100:.2f}%")
        print("="*60)


class OptimizationEngine:
    def __init__(self, backtester: Backtester):
        self.backtester = backtester
        self.best_params = None
        self.best_sharpe = -float('inf')

    def grid_search(self,
                    param_grid: Dict[str, List],
                    data: pd.DataFrame,
                    strategy_class,
                    metric: str = 'sharpe_ratio') -> Dict:
        
        from itertools import product
        
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        
        results = []
        
        for combo in product(*param_values):
            params = dict(zip(param_names, combo))
            
            strategy = strategy_class(**params)
            backtest_results = self.backtester.run(data, strategy)
            
            result = {
                'params': params,
                'results': backtest_results,
                'metric_value': backtest_results.get(metric, 0)
            }
            results.append(result)
            
            if backtest_results.get(metric, -float('inf')) > self.best_sharpe:
                self.best_sharpe = backtest_results[metric]
                self.best_params = params
        
        results.sort(key=lambda x: x['metric_value'], reverse=True)
        
        return {
            'best_params': self.best_params,
            'best_metric': self.best_sharpe,
            'all_results': results
        }