"""Experiment runner for evaluating strategies."""
import argparse
from typing import List, Optional
import pandas as pd
from forex_bot_platform.data.provider import DataProvider
from forex_bot_platform.data_quality import validate_data
import os
import pandas as pd
from forex_bot_platform.backtesting.engine import run_backtest
from forex_bot_platform.strategies.breakout import Breakout
from forex_bot_platform.strategies.trend_follower import TrendFollower
from forex_bot_platform.strategies.mean_reversion import MeanReversion
from forex_bot_platform.strategies.supertrend import SuperTrend
import json
import datetime
from forex_bot_platform.backtesting.engine import run_backtest

STRATEGY_MAP = [Breakout, TrendFollower, MeanReversion, SuperTrend]
MIN_TRADES = 2
MAX_DRAWDOWN_PCT = 5.0
PROFIT_FACTOR_MIN = 1.0

def _resolve_strategies(all_strategies: bool, explicit_strategy: Optional[str]) -> List:
    if not all_strategies and explicit_strategy:
        # Only the one requested
        for cls in STRATEGY_MAP:
            if cls.__name__ == explicit_strategy:
                return [cls()]
        return [Breakout()]
    if all_strategies:
        return [cls() for cls in STRATEGY_MAP]
    return [Breakout()]

def run_experiments(pair: str = "EURUSD", timeframe: str = "1h", strategy: Optional[str] = None,
                    experiments: int = 1, all_strategies: bool = False, all_pairs: bool = False):
    # Simple demo: load 1 year of data and run experiments split into in/out of sample
    provider = DataProvider(use_real=True)
    data = provider.fetch(pair, timeframe, periods=365)
    # Data quality check
    dq = validate_data(data, timeframe)
    data_source = dq.get("details", {}).get("source", "synthetic")
    # Attach a simple flag in results if data issues exist
    # Ensure a consistent date index
    if "date" not in data.columns:
        data["date"] = pd.date_range(start=pd.Timestamp.today(), periods=len(data), freq="D")
    split = int(len(data) * 0.7)
    in_sample = data.iloc[:split]
    out_sample = data.iloc[split:]
    strategy_classes = _resolve_strategies(all_strategies, strategy)
    results = []
    rejected = []
    for strat in strategy_classes:
        res_in = run_backtest(in_sample, strat, data_pair=pair)
        res_out = run_backtest(out_sample, strat, data_pair=pair)
        entry = {"strategy": strat.name, "samples": "in+out", "metrics_in": res_in.get("metrics", {}), "metrics_out": res_out.get("metrics", {})}
        # Evaluate rejection criteria
        in_trades = res_in.get("metrics", {}).get("trades", 0)
        out_drawdown = res_out.get("metrics", {}).get("max_drawdown_pct", 0.0)
        profit_factor = res_out.get("metrics", {}).get("profit_factor", 0.0)
        out_return = res_out.get("metrics", {}).get("total_return_pct", 0.0)
        is_pass = (in_trades >= MIN_TRADES) and (out_drawdown <= MAX_DRAWDOWN_PCT) and (profit_factor is not None and profit_factor >= PROFIT_FACTOR_MIN) and (out_return > 0)
        if not is_pass:
            reasons = []
            if in_trades < MIN_TRADES:
                reasons.append("too_few_trades")
            if out_drawdown > MAX_DRAWDOWN_PCT:
                reasons.append("max_drawdown_too_high")
            if profit_factor is not None and profit_factor < PROFIT_FACTOR_MIN:
                reasons.append("profit_factor_too_low")
            if out_return <= 0:
                reasons.append("out_of_sample_failed")
            entry["status"] = "rejected"
            entry["reasons"] = ", ".join(reasons) if reasons else "unspecified_reason"
            rejected.append(entry.copy())
        else:
            entry["status"] = "passed"
        results.append(entry)
    # Persist rejected_experiments.json with human-readable reasons if any
    if rejected:
        path = os.path.join(os.path.dirname(__file__), "rejected_experiments.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rejected, f, indent=2)
        except Exception:
            pass
    # Best config: pick best among the passed experiments
    passed = [r for r in results if r.get("status") == "passed"]
    if passed:
        best = max(passed, key=lambda r: r.get("metrics_out", {}).get("total_return_pct", 0) if r.get("metrics_out") else 0)
        best_conf = {"strategy": best.get("strategy"), "samples": best.get("samples"), "params_suggested": {}}
        best_path = os.path.join(os.path.dirname(__file__), "best_config.json")
        try:
            with open(best_path, "w", encoding="utf-8") as f:
                json.dump(best_conf, f, indent=2)
        except Exception:
            pass
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="EURUSD")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--strategy", default=None)
    parser.add_argument("--experiments", type=int, default=1)
    parser.add_argument("--all-strategies", action="store_true")
    parser.add_argument("--all-pairs", action="store_true")
    args = parser.parse_args()
    results = run_experiments(pair=args.pair, timeframe=args.timeframe, strategy=args.strategy,
                            experiments=args.experiments, all_strategies=args.all_strategies, all_pairs=args.all_pairs)
    # Persist a simple leaderboard and best config
    leaderboard_path = os.path.join(os.path.dirname(__file__), "leaderboard.csv")
    try:
        import pandas as pd
        df = pd.DataFrame(results)
        df.to_csv(leaderboard_path, index=False)
    except Exception:
        pass
    best_config_path = os.path.join(os.path.dirname(__file__), "best_config.json")
    try:
        with open(best_config_path, "w", encoding="utf-8") as f:
            json.dump({"best": None}, f, indent=2)
    except Exception:
        pass
    print(results)
    # Enhanced CLI-style summary
    if results:
        m = results[0].get("metrics_out", {})
        final_balance = m.get("final_balance", None)
        total_return = m.get("total_return_pct", None)
        trades = m.get("trades", None)
        win_rate = m.get("win_rate", None)
        profit_factor = m.get("profit_factor", None)
        max_dd = m.get("max_drawdown_pct", None)
        sh = m.get("sharpe_like", None)
        best = m.get("best_trade", None)
        worst = m.get("worst_trade", None)
        print("Summary:")
        print(f" Pair: {pair}  Timeframe: {timeframe}  Strategy: {results[0]['strategy']}")
        print(f" Data source: synthetic")
        print(f" Final balance: {final_balance}  Total return %: {total_return}")
        print(f" Trades: {trades}  Win rate: {win_rate}  Profit factor: {profit_factor}")
        print(f" Max drawdown %: {max_dd}  Sharpe-like: {sh}")
        print(f" Best trade: {best}  Worst trade: {worst}")
    # Simple hardening: save rejected experiments with reasons
    rejected = []
    for r in results:
        m_in = r.get("metrics_in", {})
        m_out = r.get("metrics_out", {})
        reason = None
        if m_in and m_in.get("trades", 0) < 2:
            reason = "too_few_trades"
        if m_out and m_out.get("max_drawdown_pct", 0) > 5.0:
            reason = (reason or "").rstrip() + ("; max_drawdown_too_high" if reason is None else ", max_drawdown_too_high")
            reason = reason.strip('; ')
        if m_out and m_out.get("profit_factor", 0) < 1.0:
            reason = (reason or "").rstrip() + ("; profit_factor_too_low" if reason is None else ", profit_factor_too_low")
            reason = reason.strip('; ')
        if reason:
            rejected.append({"strategy": r.get("strategy"), "reason": reason, "in_sample_trades": m_in.get("trades"), "out_sample_trades": m_out.get("trades")})
    if rejected:
        path = os.path.join(os.path.dirname(__file__), "rejected_experiments.json")
        try:
            import json
            with open(path, "w", encoding="utf-8") as f:
                json.dump(rejected, f, indent=2)
        except Exception:
            pass

if __name__ == "__main__":
    main()
