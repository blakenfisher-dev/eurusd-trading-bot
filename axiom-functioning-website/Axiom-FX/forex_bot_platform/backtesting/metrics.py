"""Backtesting metrics calculations."""
from typing import List, Dict, Any

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """Calculate Sharpe ratio from returns."""
    if not returns:
        return 0.0
    
    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / len(returns)
    std_dev = variance ** 0.5
    
    if std_dev == 0:
        return 0.0
    
    return (avg_return - risk_free_rate) / std_dev

def calculate_sortino_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """Calculate Sortino ratio using downside deviation."""
    if not returns:
        return 0.0
    
    avg_return = sum(returns) / len(returns)
    downside_returns = [r for r in returns if r < 0]
    
    if not downside_returns:
        return 0.0
    
    downside_variance = sum(r ** 2 for r in downside_returns) / len(downside_returns)
    downside_dev = downside_variance ** 0.5
    
    if downside_dev == 0:
        return 0.0
    
    return (avg_return - risk_free_rate) / downside_dev

def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculate maximum drawdown from equity curve."""
    if not equity_curve:
        return 0.0
    
    max_dd = 0.0
    peak = equity_curve[0]
    
    for equity in equity_curve:
        if equity > peak:
            peak = equity
        drawdown = (peak - equity) / peak if peak > 0 else 0
        max_dd = max(max_dd, drawdown)
    
    return max_dd * 100

def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
    """Calculate win rate from trades."""
    if not trades:
        return 0.0
    
    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    return wins / len(trades)

def calculate_profit_factor(trades: List[Dict[str, Any]]) -> float:
    """Calculate profit factor."""
    if not trades:
        return 0.0
    
    gross_profit = sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) > 0)
    gross_loss = abs(sum(t.get("pnl", 0) for t in trades if t.get("pnl", 0) < 0))
    
    if gross_loss == 0:
        return 0.0 if gross_profit == 0 else float('inf')
    
    return gross_profit / gross_loss

def format_metrics(result) -> str:
    """Format backtest metrics for display."""
    return f"""
=== Backtest Results ===
Pair: {result.pair}
Strategy: {result.strategy}
Timeframe: {result.timeframe}

Initial Balance: ${result.initial_balance:,.2f}
Final Balance: ${result.final_balance:,.2f}
Total Return: {result.total_return_pct:.2f}%

Win Rate: {result.win_rate * 100:.2f}%
Profit Factor: {result.profit_factor:.2f}
Max Drawdown: {result.max_drawdown_pct:.2f}%

Trades: {result.trade_count}
Average Win: ${result.average_win:.2f}
Average Loss: ${result.average_loss:.2f}
Best Trade: ${result.best_trade:.2f}
Worst Trade: ${result.worst_trade:.2f}
"""