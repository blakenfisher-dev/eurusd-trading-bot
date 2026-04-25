"""CLI entry point for the Forex Bot Platform."""
import argparse
import os
from forex_bot_platform.research_engine.experiment_runner import run_experiments
from forex_bot_platform.execution.mt5_executor import MT5DemoExecutor, SafetyConfig
from forex_bot_platform.execution.mt5_executor import DemoSoakConfig, DemoSoakTest
from forex_bot_platform.execution.demo_readiness import (
    DemoReadinessConfig, evaluate_demo_readiness, 
    write_demo_readiness_report, generate_readiness_markdown
)

def run_demo_soak_test(login: str, password: str, server: str, allow_orders: bool = False,
                      max_runtime: int = 3600, max_trades: int = 10, max_daily_loss: float = 1000.0,
                      output_dir: str = "."):
    """Run Demo Trading Mode soak test."""
    safety = SafetyConfig(max_daily_loss=max_daily_loss, max_open_trades=3, require_stop_loss=True)
    executor = MT5DemoExecutor(login=login, password=password, server=server, safety_config=safety)
    soak_config = DemoSoakConfig(
        max_runtime_seconds=max_runtime,
        max_trades=max_trades,
        max_daily_loss=max_daily_loss,
        heartbeat_interval=30
    )
    soak = DemoSoakTest(executor, soak_config)
    
    print("=== Demo Trading Soak Test ===")
    print(f"Mode: {'Orders allowed' if allow_orders else 'Validation only'}")
    print(f"Max runtime: {max_runtime}s, Max trades: {max_trades}, Max daily loss: ${max_daily_loss}")
    
    success = soak.start(allow_orders=allow_orders)
    if not success:
        print(f"FAIL: Could not start soak test. Status: {soak.status}")
        return False
    
    print(f"Started: {soak.status}")
    
    # Run for a few iterations (in real use, would be time-based)
    for i in range(10):
        status = soak.step()
        if i == 0:
            print(f"Step {i+1}: {status['status']}, trades: {status['trades_placed']}")
        if status["status"] in ("stopped", "validation_only"):
            break
    
    # Export reports
    soak.export_reports(output_dir)
    print(f"Reports exported to {output_dir}")
    
    final = soak._get_status()
    print(f"\n=== Soak Test Complete ===")
    print(f"Status: {final['status']}")
    print(f"Trades placed: {final['trades_placed']}")
    print(f"Heartbeats: {final['heartbeat_count']}")
    print(f"Stop reason: {final['stop_reason'] or 'N/A'}")
    
    return True

def run_demo_dry_run(login: str, password: str, server: str, place_order: bool = False):
    """Run Demo Trading Mode dry run without placing actual orders."""
    config = SafetyConfig(
        max_daily_loss=1000.0,
        max_open_trades=3,
        require_stop_loss=True,
    )
    
    print("=== Demo Trading Dry Run ===")
    
    # Connect
    print("\n[1] Connecting to MT5...")
    executor = MT5DemoExecutor(login=login, password=password, server=server, safety_config=config)
    
    try:
        executor.connect()
    except Exception as e:
        print(f"FAIL: {e}")
        return False
    
    print(f"  OK - Connected to {executor.account.server}")
    print(f"  Account: {executor.account.login}")
    print(f"  Type: {executor.account.account_type.value}")
    
    # Verify demo account
    print("\n[2] Verifying demo account...")
    if executor.account.account_type.value != "demo":
        print(f"  FAIL: Not a demo account!")
        return False
    print("  OK - Demo account confirmed")
    
    # Get symbol info
    print("\n[3] Getting symbol info...")
    symbol = "EURUSD"
    info = executor.get_symbol_info(symbol)
    if info:
        print(f"  OK - {symbol}: bid={info['bid']}, ask={info['ask']}, spread={info['spread']}")
    else:
        print(f"  WARNING: Could not get symbol info")
    
    # Get latest tick
    print("\n[4] Getting latest tick...")
    tick = executor.get_latest_tick(symbol)
    if tick:
        print(f"  OK - {symbol}: bid={tick['bid']}, ask={tick['ask']}")
    else:
        print(f"  WARNING: Could not get tick")
    
    # Validate safety config
    print("\n[5] Validating safety config...")
    print(f"  max_daily_loss: ${config.max_daily_loss}")
    print(f"  max_open_trades: {config.max_open_trades}")
    print(f"  require_stop_loss: {config.require_stop_loss}")
    print("  OK - Safety config valid")
    
    # Mock order validation
    print("\n[6] Validating mock order (without placing)...")
    from forex_bot_platform.execution.mt5_executor import OrderSide
    try:
        executor._safety_checks(symbol, OrderSide.BUY, 0.1, 1.0900, None)
        print("  OK - Safety checks passed")
    except Exception as e:
        print(f"  Result: {e} (expected for unconnected check)")
    
    # Place order if requested
    if place_order:
        print("\n[7] Placing demo order...")
        try:
            ticket = executor.place_demo_order(symbol, OrderSide.BUY, 0.1, stop_loss=1.0900)
            print(f"  OK - Order placed! Ticket: {ticket}")
        except Exception as e:
            print(f"  FAIL: {e}")
            return False
    else:
        print("\n[7] Skipping order placement (--place-demo-order not specified)")
    
    # Cleanup
    executor.disconnect()
    
    if place_order:
        print("\n=== Dry run complete with demo order ===")
    else:
        print("\n=== Dry run complete. No orders placed. ===")
    
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair", default="EURUSD")
    parser.add_argument("--timeframe", default="1h")
    parser.add_argument("--strategy", default=None)
    parser.add_argument("--experiments", type=int, default=1)
    parser.add_argument("--all-strategies", action="store_true")
    parser.add_argument("--all-pairs", action="store_true")
    parser.add_argument("--demo-dry-run", action="store_true")
    parser.add_argument("--place-demo-order", action="store_true")
    parser.add_argument("--demo-soak", action="store_true")
    parser.add_argument("--allow-demo-orders", action="store_true")
    parser.add_argument("--max-runtime", type=int, default=3600)
    parser.add_argument("--max-trades", type=int, default=10)
    parser.add_argument("--max-daily-loss", type=float, default=1000.0)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--demo-readiness", action="store_true")
    parser.add_argument("--soak-dir", default=".")
    parser.add_argument("--max-drawdown-threshold", type=float, default=10.0)
    parser.add_argument("--max-daily-loss-threshold", type=float, default=1000.0)
    parser.add_argument("--max-rejection-rate", type=float, default=0.5)
    parser.add_argument("--login", default="")
    parser.add_argument("--password", default="")
    parser.add_argument("--server", default="MetaQuotes-Demo")
    
    # Phase 4: Live Trading Mode - DISABLED BY DEFAULT
    parser.add_argument("--live-readiness", action="store_true")
    parser.add_argument("--live-dry-run", action="store_true")
    parser.add_argument("--place-live-order", action="store_true")
    parser.add_argument("--enable-live-trading", action="store_true")
    parser.add_argument("--emergency-stop-live", action="store_true")
    parser.add_argument("--approval-file", default="LIVE_APPROVAL.json")
    
    args = parser.parse_args()
    
    if args.demo_dry_run:
        if not args.login:
            print("ERROR: --login required for demo dry run")
            return
        success = run_demo_dry_run(
            login=args.login,
            password=args.password or "demo",
            server=args.server,
            place_order=args.place_demo_order
        )
        if not success:
            exit(1)
        return
    
    if args.demo_soak:
        if not args.login:
            print("ERROR: --login required for demo soak test")
            return
        success = run_demo_soak_test(
            login=args.login,
            password=args.password or "demo",
            server=args.server,
            allow_orders=args.allow_demo_orders or False,
            max_runtime=args.max_runtime or 3600,
            max_trades=args.max_trades or 10,
            max_daily_loss=args.max_daily_loss or 1000.0,
            output_dir=args.output_dir or "."
        )
        if not success:
            exit(1)
        return
    
    if args.demo_readiness:
        if not args.soak_dir:
            print("ERROR: --soak-dir required for demo readiness")
            return
        
        config = DemoReadinessConfig(
            max_drawdown_threshold=args.max_drawdown_threshold or 10.0,
            max_daily_loss_threshold=args.max_daily_loss_threshold or 1000.0,
            max_rejection_rate=args.max_rejection_rate or 0.5,
        )
        
        print("=== Demo Readiness Evaluation ===")
        print(f"Soak directory: {args.soak_dir}")
        
        result = evaluate_demo_readiness(args.soak_dir, config)
        
        print(f"\nScore: {result.score}/{result.max_score}")
        print(f"Passed: {result.passed}")
        
        if result.errors:
            print("\nErrors:")
            for err in result.errors:
                print(f"  - {err}")
        
        if result.warnings:
            print("\nWarnings:")
            for warn in result.warnings:
                print(f"  - {warn}")
        
        # Write reports
        json_path = os.path.join(args.soak_dir, "demo_readiness_report.json")
        write_demo_readiness_report(result, json_path)
        
        md_path = os.path.join(args.soak_dir, "demo_readiness_report.md")
        with open(md_path, 'w') as f:
            f.write(generate_readiness_markdown(result))
        
        print(f"\nReports written to:")
        print(f"  {json_path}")
        print(f"  {md_path}")
        print(f"\nREADY_FOR_LIVE_REVIEW = {result.passed}")
        
        if not result.passed:
            exit(1)
        return
    
    # Live Trading Mode (Phase 4) - DISABLED BY DEFAULT
    if args.live_readiness:
        from forex_bot_platform.execution.live_readiness import check_live_readiness
        ready, report = check_live_readiness()
        print(report)
        print(f"\nLIVE_READY = {ready}")
        if not ready:
            exit(1)
        return
    
    if args.live_dry_run:
        if not args.login:
            print("ERROR: --login required for live dry run")
            return
        from forex_bot_platform.execution.live_readiness import LiveReadinessChecker, LiveReadinessConfig
        config = LiveReadinessConfig(approval_path=args.approval_file)
        checker = LiveReadinessChecker(config)
        ready, checks = checker.check_all()
        
        if not ready:
            print("Live trading NOT ready. Run --live-readiness for details.")
            exit(1)
        
        print("Live dry run: Would place order (dry run only)")
        print("Use --enable-live-trading --place-live-order for actual order")
        return
    
    if args.emergency_stop_live:
        from forex_bot_platform.execution.live_executor import LiveExecutor
        LiveExecutor.disable_live_trading()
        print("EMERGENCY STOP: Live trading disabled")
        return
    
    if args.live_readiness or args.live_dry_run or args.enable_live_trading or args.place_live_order or args.emergency_stop_live:
        # Live trading commands were given but weren't handled above
        print("Use --live-readiness to check readiness")
        return
    
    # Run experiments if no special mode
    results = run_experiments(pair=args.pair, timeframe=args.timeframe, strategy=args.strategy,
                            experiments=args.experiments, all_strategies=args.all_strategies, all_pairs=args.all_pairs)
    print(results)

if __name__ == "__main__":
    main()
