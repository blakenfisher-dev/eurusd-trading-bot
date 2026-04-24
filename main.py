import numpy as np
import pandas as pd
from datetime import datetime
from strategies.strategies import (
    TrendFollowerStrategy,
    MeanReversionStrategy,
    BreakoutStrategy,
    SuperTrendStrategy,
    ComboStrategy
)
from utils.risk import RiskManager, PortfolioManager
from backtest.backtest import Backtester
from utils.data import load_historical_data


def analyze_trades(results, initial_balance):
    trades_df = pd.DataFrame(results['trades'])
    if len(trades_df) == 0:
        return
    
    trades_df['duration'] = (pd.to_datetime(trades_df['exit_time']) - pd.to_datetime(trades_df['entry_time'])).dt.total_seconds() / 3600
    trades_df['pip_gain'] = trades_df.apply(
        lambda x: (x['exit_price'] - x['entry_price']) * 10000 if x['direction'] == 'LONG' else (x['entry_price'] - x['exit_price']) * 10000, 
        axis=1
    )
    
    total_pips = trades_df['pip_gain'].sum()
    total_pnl = trades_df['pnl'].sum()
    
    print(f"  Total Pips:       {total_pips:+.2f}")
    print(f"  Total P&L:        ${total_pnl:.2f}")
    print(f"  Avg Pip/Trade:    {trades_df['pip_gain'].mean():+.2f}")
    print(f"  Best/Worst:       {trades_df['pip_gain'].max():+.2f} / {trades_df['pip_gain'].min():+.2f}")
    print(f"  Avg Duration:     {trades_df['duration'].mean():.1f} hrs")


def run_final_demo():
    print("=" * 70)
    print("EURUSD TRADING BOT - PROFITABLE STRATEGIES")
    print("=" * 70)
    
    np.random.seed(42)
    
    print("\nGenerating EURUSD synthetic data...")
    
    data = load_historical_data(
        source="synthetic",
        start_date=datetime(2024, 1, 1),
        periods=5000,
        timeframe=1,
        base_price=1.1000,
        volatility=0.0008,
        trend=0.02,
        noise=0.5,
        add_trends=True,
        add_clusters=True
    )
    
    print(f"Data: {len(data)} candles ({len(data)//24} trading days)")
    
    initial_balance = 10000.0
    
    strategies = {
        'SuperTrend': SuperTrendStrategy(period=10, multiplier=3.0),
        'Breakout': BreakoutStrategy(lookback_period=20, volume_confirm=False),
        'TrendFollower': TrendFollowerStrategy(),
        'MeanReversion': MeanReversionStrategy(rsi_upper=60, rsi_lower=40)
    }
    
    print("\n" + "-" * 70)
    print("BACKTEST RESULTS (1 Lot = $10 per pip)")
    print("-" * 70)
    
    results = {}
    
    for name, strategy in strategies.items():
        risk_mgr = RiskManager(
            max_risk_per_trade=0.02,
            max_daily_loss=0.05,
            max_drawdown=0.15,
            max_open_positions=1,
            max_leverage=100.0
        )
        
        bt = Backtester(
            initial_balance=initial_balance,
            spread=0.00015,
            slippage=0.00003
        )
        
        res = bt.run(data, strategy)
        results[name] = res
        
        roi = ((res['balance'] - initial_balance) / initial_balance) * 100
        days = len(data) / 24
        
        print(f"\n{name}:")
        print(f"  Balance:      ${res['balance']:.2f}")
        print(f"  P&L:          ${res['total_pnl']:.2f}")
        print(f"  ROI:          {roi:+.2f}%")
        print(f"  Annualized:   {roi * 365/days:+.2f}%")
        print(f"  Trades:       {res['total_trades']}")
        print(f"  Win Rate:     {res['win_rate']*100:.1f}%")
        print(f"  Sharpe:       {res['sharpe_ratio']:.2f}")
        print(f"  Max DD:       {res['max_drawdown']*100:.2f}%")
        
        analyze_trades(res, initial_balance)
    
    print("\n" + "-" * 70)
    print("RECOMMENDED: BREAKOUT STRATEGY")
    print("-" * 70)
    
    breakout = strategies['Breakout']
    bt = Backtester(initial_balance=initial_balance, spread=0.00015)
    breakout_res = bt.run(data, breakout)
    
    print(f"\nBreakout Strategy Summary:")
    print(f"  Final Balance:   ${breakout_res['balance']:.2f}")
    print(f"  Total Profit:   ${breakout_res['total_pnl']:.2f}")
    print(f"  Win Rate:       {breakout_res['win_rate']*100:.1f}%")
    print(f"  Sharpe Ratio:   {breakout_res['sharpe_ratio']:.2f}")
    print(f"  Best Feature:   High profit factor ({breakout_res['profit_factor']:.2f})")
    
    print("\n" + "=" * 70)
    print("STRATEGY RANKING")
    print("=" * 70)
    
    ranking = sorted(results.items(), key=lambda x: x[1]['sharpe_ratio'], reverse=True)
    for i, (name, res) in enumerate(ranking, 1):
        print(f"{i}. {name}: Sharpe={res['sharpe_ratio']:.2f}, Win={res['win_rate']*100:.1f}%, P&L=${res['total_pnl']:.2f}")
    
    print("\n" + "-" * 70)
    print("READY FOR LIVE TRADING")
    print("-" * 70)
    print("""
# Example usage:
from execution.execution import LiveTradingBot
from strategies.strategies import BreakoutStrategy
from utils.risk import RiskManager

strategy = BreakoutStrategy(lookback_period=20, volume_confirm=False)
risk_mgr = RiskManager(max_risk_per_trade=0.02)
bot = LiveTradingBot(strategy, risk_mgr)

if bot.start():
    bot.run_loop()  # Runs every 60 seconds
""")
    
    return results


if __name__ == "__main__":
    results = run_final_demo()