"""Backtesting metrics helpers."""
import numpy as np

def _sharpe_ratio(returns: list, risk_free: float = 0.0) -> float:
    if len(returns) < 2:
        return 0.0
    rets = np.array(returns)
    mean = rets.mean()
    std = rets.std()
    if std == 0:
        return 0.0
    return (mean - risk_free) / std * np.sqrt(252)

def compute_metrics(equity_path):
    if equity_path is None or len(equity_path) < 2:
        return {}
    returns = equity_path.pct_change().dropna().tolist()
    metrics = {
        "sharpe": _sharpe_ratio(returns),
        "max_drawdown_pct": 0.0,
        "total_return_pct": (equity_path.iloc[-1] - equity_path.iloc[0]) / equity_path.iloc[0] * 100.0,
        "trade_count": max(0, len(returns) - 1),
    }
    # naive max drawdown
    peak = equity_path.iloc[0]
    max_dd = 0.0
    for v in equity_path:
        if v > peak:
            peak = v
        dd = (peak - v) / peak
        if dd > max_dd:
            max_dd = dd
    metrics["max_drawdown_pct"] = max_dd * 100.0
    return metrics
