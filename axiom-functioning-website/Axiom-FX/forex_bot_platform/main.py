"""Axiom FX - CLI Entry Point."""
import argparse
import sys

from forex_bot_platform.strategies import (
    BreakoutStrategy,
    SuperTrendStrategy,
    TrendFollowerStrategy,
    MeanReversionStrategy,
    ComboStrategy,
)
from forex_bot_platform.backtesting import BacktestEngine
from forex_bot_platform.backtesting.metrics import format_metrics
from forex_bot_platform.execution import MT5DemoExecutor, LiveGuard, LiveSafety
from forex_bot_platform.risk import RiskManager, RiskLimits
from forex_bot_platform.config import LIVE_MODE_ENABLED

def run_backtest(pair: str, strategy_name: str, timeframe: str, candles: int = 1000):
    """Run backtest mode."""
    strategy_map = {
        "breakout": BreakoutStrategy,
        "supertrend": SuperTrendStrategy,
        "trendfollower": TrendFollowerStrategy,
        "trend_follower": TrendFollowerStrategy,
        "meanreversion": MeanReversionStrategy,
        "mean_reversion": MeanReversionStrategy,
        "combo": lambda: ComboStrategy([
            BreakoutStrategy(),
            TrendFollowerStrategy(),
        ], min_agreement=2),
    }
    
    strategy_class = strategy_map.get(strategy_name.lower())
    if not strategy_class:
        print(f"Unknown strategy: {strategy_name}")
        print(f"Available: {', '.join(strategy_map.keys())}")
        return False
    
    strategy = strategy_class() if callable(strategy_class) else strategy_class
    
    print(f"Running backtest: {pair} {timeframe} {strategy.name}")
    
    engine = BacktestEngine(initial_balance=100000.0)
    result = engine.run(pair, strategy, timeframe, candles)
    
    print(format_metrics(result))
    return True

def run_demo_dry_run(login: str, server: str):
    """Run demo trading dry run."""
    print("=== Demo Trading Dry Run ===")
    print(f"Server: {server}")
    print(f"Login: {login}")
    
    risk_manager = RiskManager(RiskLimits())
    executor = MT5DemoExecutor(login=login, server=server, risk_manager=risk_manager)
    
    success, message = executor.connect()
    if not success:
        print(f"FAIL: {message}")
        return False
    
    print(f"OK - {message}")
    print(f"Account Type: {executor.account_info.get('type', 'unknown')}")
    
    if not executor.is_demo_account():
        print("FAIL: Only demo accounts allowed")
        executor.disconnect()
        return False
    
    print("OK - Demo account verified")
    
    result = executor.place_order("buy", "EURUSD", 0.1, 1.0800, 1.0900)
    if result.success:
        print(f"OK - Test order placed: {result.order_id}")
        executor.close_order(result.order_id)
    else:
        print(f"FAIL: {result.message}")
    
    executor.disconnect()
    print("Demo dry run complete")
    return True

def check_live_readiness():
    """Check live trading readiness."""
    print("=== Live Trading Readiness ===")
    print("")
    
    guard = LiveGuard()
    can_trade, reason = guard.can_trade_live()
    
    print(f"Approval File: {'[PASS]' if guard._is_approval_valid() else '[FAIL]'}")
    print(f"Emergency Stop: {'[FAIL]' if guard._is_emergency_stop_active() else '[PASS]'}")
    print(f"Live Mode Enabled: {'[PASS]' if LIVE_MODE_ENABLED else '[FAIL] (disabled by default)'}")
    
    print("")
    print(f"LIVE_READY = {can_trade and LIVE_MODE_ENABLED}")
    
    if not can_trade:
        print(f"Reason: {reason}")
        return False
    
    return True

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Axiom FX - Forex Trading Bot")
    parser.add_argument("--mode", choices=["backtest", "demo-dry-run", "live-readiness"],
                       help="Trading mode")
    parser.add_argument("--pair", default="EURUSD", help="Currency pair")
    parser.add_argument("--strategy", default="Breakout", help="Strategy name")
    parser.add_argument("--timeframe", default="1h", help="Timeframe")
    parser.add_argument("--candles", type=int, default=1000, help="Number of candles")
    parser.add_argument("--login", default="", help="MT5 login")
    parser.add_argument("--server", default="MetaQuotes-Demo", help="MT5 server")
    
    args = parser.parse_args()
    
    if args.mode == "backtest":
        success = run_backtest(args.pair, args.strategy, args.timeframe, args.candles)
        sys.exit(0 if success else 1)
    
    elif args.mode == "demo-dry-run":
        success = run_demo_dry_run(args.login, args.server)
        sys.exit(0 if success else 1)
    
    elif args.mode == "live-readiness":
        success = check_live_readiness()
        sys.exit(0 if success else 1)
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()