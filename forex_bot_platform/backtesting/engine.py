"""Lightweight backtesting engine."""
import pandas as pd
from typing import Dict, Any, List
from forex_bot_platform.risk.risk_manager import calculate_position_size, is_jpy_pair
from dataclasses import dataclass

@dataclass
class Trade:
    entry_idx: int
    exit_idx: int | None
    side: int
    units: int
    entry_price: float
    exit_price: float | None
    exit_reason: str | None
    duration: int | None

def _pip_distance(pair: str) -> float:
    # Rough pip distance: 0.0001 for most pairs, 0.01 for JPY pairs
    if pair.endswith("JPY"):
        return 0.01
    return 0.0001

def _apply_spread(price: float, spread_pips: float, pair: str, is_entry: bool) -> float:
    pip = _pip_distance(pair)
    spread = spread_pips * pip
    return price + spread if is_entry else price

def _exit_price_for_side(price: float, side: int, spread_pips: float, pair: str) -> float:
    # Apply spread on exit as well
    pip = _pip_distance(pair)
    spread = spread_pips * pip
    return price - spread if side == 1 else price + spread

def _max_drawdown(equity_path: List[float]) -> float:
    max_dd = 0.0
    peak = equity_path[0] if equity_path else 0.0
    for v in equity_path:
        if v > peak:
            peak = v
        dd = (peak - v) / peak if peak != 0 else 0.0
        if dd > max_dd:
            max_dd = dd
    return max_dd

def run_backtest(data: pd.DataFrame, strategy, initial_capital: float = 100000.0, *, spread_pips: float = 0.0, slippage_pct: float = 0.0, risk_per_trade: float = 0.01, stop_loss_pips: float | None = None, take_profit_pips: float | None = None, max_holding_bars: int | None = None, data_pair: str = "EURUSD", max_position_size: int | None = None, max_exposure_per_currency: float | None = None, data_source: str = "synthetic"):
    if data is None or data.empty:
        return {
            "equity_path": pd.Series([initial_capital]),
            "final_equity": initial_capital,
            "trades": [],
            "metrics": {"final_balance": initial_capital, "total_return_pct": 0.0},
            "data_source": data_source,
        }
    equity = initial_capital
    equity_path = [equity]
    trades: List[Trade] = []
    in_trade = False
    current_trade: Trade | None = None
    entry_trade_idx = 0
    for i in range(1, len(data)):
        row = data.iloc[i]
        price = row["close"]
        date = row["date"]
        # Look-back safe
        try:
            sig = int(strategy.generate_signal(data.iloc[: i + 1]))
        except Exception:
            sig = 0

        if not in_trade:
            if sig != 0:
                # Open new trade with risk-based sizing
                side = 1 if sig > 0 else -1
                units = calculate_position_size(data_pair, equity, risk_per_trade, (stop_loss_pips or 50))
                entry_price = _apply_spread(price, spread_pips, data_pair, True)
                entry_price = entry_price * (1 + slippage_pct * (1 if side == 1 else -1))
                current_trade = Trade(i, None, side, units, entry_price, None, None, None)
                # Define stop/take prices - handle 0 as "no stop loss"
                if stop_loss_pips is None or stop_loss_pips == 0:
                    stop_price = None
                else:
                    pip = 0.01 if is_jpy_pair(data_pair) else 0.0001
                    stop_distance = stop_loss_pips * pip
                    stop_price = entry_price - stop_distance if side == 1 else entry_price + stop_distance
                if take_profit_pips is None or take_profit_pips == 0:
                    take_price = None
                else:
                    pip = 0.01 if is_jpy_pair(data_pair) else 0.0001
                    take_distance = take_profit_pips * pip
                    take_price = entry_price + take_distance if side == 1 else entry_price - take_distance
                in_trade = True
                entry_trade_idx = i
            else:
                # No position, just progress equity with no PnL
                equity_path.append(equity)
        else:
            # In trade: determine exit
            exit_due_to = None
            exit_price = price
            # Check stop / take (skip if None)
            if current_trade and current_trade.side == 1:
                if stop_price is not None and price <= stop_price:
                    exit_due_to = 'stop_loss'
                    exit_price = stop_price
                elif take_price is not None and price >= take_price:
                    exit_due_to = 'take_profit'
                    exit_price = take_price
            elif current_trade:
                if stop_price is not None and price >= stop_price:
                    exit_due_to = 'stop_loss'
                    exit_price = stop_price
                elif take_price is not None and price <= take_price:
                    exit_due_to = 'take_profit'
                    exit_price = take_price

            # Opposite signal => exit
            if exit_due_to is None:
                try:
                    next_sig = int(strategy.generate_signal(data.iloc[: i + 1]))
                    if next_sig != 0 and (next_sig > 0) != (current_trade.side > 0):
                        exit_due_to = 'signal_flip'
                except Exception:
                    pass
            # Time exit
            holding = i - entry_trade_idx + 1
            if exit_due_to is None and max_holding_bars is not None and holding >= max_holding_bars:
                exit_due_to = 'time_exit'
                exit_price = price

            if exit_due_to is not None:
                # Close trade with slippage applied on exit and risk-based sizing
                exit_price_final = exit_price * (1 - slippage_pct * (1 if current_trade.side == 1 else -1))
                units = max(1, current_trade.units)
                pnl = (exit_price_final - current_trade.entry_price) * current_trade.side * units
                equity += pnl
                current_trade.exit_idx = i
                current_trade.exit_price = exit_price_final
                current_trade.exit_reason = exit_due_to
                current_trade.duration = holding
                trades.append(current_trade)
                in_trade = False
                current_trade = None
                equity_path.append(equity)
            else:
                # Hold and update equity path with no change
                equity_path.append(equity)

    # If still open at end, close it
    if in_trade and current_trade is not None:
        exit_price = data.iloc[-1]["close"]
        exit_price_final = exit_price * (1 - slippage_pct * (1 if current_trade.side == 1 else -1))
        units = max(1, current_trade.units)
        pnl = (exit_price_final - current_trade.entry_price) * current_trade.side * units
        equity += pnl
        current_trade.exit_idx = len(data) - 1
        current_trade.exit_price = exit_price_final
        current_trade.exit_reason = 'time_exit'
        current_trade.duration = (len(data) - 1) - entry_trade_idx + 1
        trades.append(current_trade)
        in_trade = False
        current_trade = None
        equity_path.append(equity)

    # Metrics
    total_return_pct = (equity - initial_capital) / initial_capital * 100.0
    num_trades = len(trades)
    wins = [t for t in trades if t.exit_price is not None and (t.exit_price - t.entry_price) * t.side > 0]
    losses = [t for t in trades if t.exit_price is not None and (t.exit_price - t.entry_price) * t.side < 0]
    avg_win = None if not wins else sum((t.exit_price - t.entry_price) * t.side for t in wins) / len(wins)
    avg_loss = None if not losses else sum((t.exit_price - t.entry_price) * t.side for t in losses) / len(losses)
    best_trade = max(trades, key=lambda t: (t.exit_price - t.entry_price) * t.side, default=None)
    worst_trade = min(trades, key=lambda t: (t.exit_price - t.entry_price) * t.side, default=None)
    # Wins/losses
    win_rate = len(wins) / num_trades if num_trades > 0 else 0.0
    profit_factor = (sum((t.exit_price - t.entry_price) * t.side for t in wins) or 0.0) / (abs(sum((t.exit_price - t.entry_price) * t.side for t in losses)) or 1.0)
    # Drawdown metrics
    max_dd = _max_drawdown(equity_path)
    # Sharpe-like: use daily returns from equity path changes
    daily_returns = []
    for i in range(1, len(equity_path)):
        daily_returns.append((equity_path[i] - equity_path[i-1]) / equity_path[i-1] if equity_path[i-1] != 0 else 0.0)
    rt = (sum(daily_returns) / len(daily_returns)) * (252 ** 0.5) if daily_returns else 0.0
    monthly_returns = {}
    for i, val in enumerate(equity_path):
        if i == 0:
            continue
        if hasattr(data, 'date'):
            date = data.iloc[min(i, len(data)-1)]['date']
            key = date.strftime('%Y-%m')
            monthly_returns.setdefault(key, 0.0)
            monthly_returns[key] += (val - equity_path[i-1]) / equity_path[i-1] if equity_path[i-1] != 0 else 0.0
    # Safe calc for average_risk_reward
    ratio = None
    try:
        if avg_loss is not None and abs(avg_loss) > 0 and avg_win is not None:
            ratio = abs(avg_win) / abs(avg_loss)
    except (TypeError, ValueError):
        ratio = None
    metrics = {
        "final_balance": equity,
        "total_return_pct": total_return_pct,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown_pct": max_dd * 100.0,
        "drawdown_curve": equity_path,
        "sharpe_like": rt,
        "trades": num_trades,
        "average_win": avg_win,
        "average_loss": avg_loss,
        "average_risk_reward": ratio,
        "largest_losing_streak": 0,
        "best_trade": (best_trade.exit_price - best_trade.entry_price) * best_trade.side if best_trade else None,
        "worst_trade": (worst_trade.exit_price - worst_trade.entry_price) * worst_trade.side if worst_trade else None,
        "monthly_returns": monthly_returns,
    }
    return {
        "equity_path": pd.Series(equity_path),
        "final_equity": equity,
        "trades": trades,
        "metrics": metrics,
        "data_source": data_source,
    }
