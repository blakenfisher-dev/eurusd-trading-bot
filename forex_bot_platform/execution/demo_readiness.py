"""Demo Trading Readiness Evaluator (Phase 3.5).

This module evaluates whether Demo Trading Mode is ready for human review
before any future Live Trading Mode work. It does NOT enable live trading.
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import pandas as pd

@dataclass
class DemoReadinessConfig:
    max_drawdown_threshold: float = 10.0  # percent
    max_daily_loss_threshold: float = 1000.0  # dollars
    max_rejection_rate: float = 0.5  # 50% max
    max_connection_failures: int = 3

@dataclass
class DemoReadinessResult:
    passed: bool = False
    score: int = 0
    max_score: int = 100
    
    # Verification checks
    demo_account_verified: bool = False
    live_account_attempts: int = 0
    unknown_account_attempts: int = 0
    missing_stop_loss_orders: int = 0
    
    # Safety checks
    emergency_stop_events: int = 0
    connection_failures: int = 0
    max_drawdown_pct: float = 0.0
    max_daily_loss: float = 0.0
    
    # Activity
    total_trades: int = 0
    total_rejections: int = 0
    
    # Files
    audit_log_exists: bool = False
    soak_report_exists: bool = False
    order_history_readable: bool = False
    open_positions_readable: bool = False
    safety_status_readable: bool = False
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

def evaluate_demo_readiness(soak_dir: str, config: DemoReadinessConfig = None) -> DemoReadinessResult:
    """Evaluate demo readiness from soak test output."""
    config = config or DemoReadinessConfig()
    result = DemoReadinessResult()
    
    # Check required files exist
    report_path = os.path.join(soak_dir, "demo_soak_report.json")
    audit_path = os.path.join(soak_dir, "demo_soak_audit.log")
    trades_path = os.path.join(soak_dir, "demo_soak_trades.csv")
    rejections_path = os.path.join(soak_dir, "demo_soak_rejections.json")
    
    result.soak_report_exists = os.path.exists(report_path)
    result.audit_log_exists = os.path.exists(audit_path)
    
    if not result.soak_report_exists:
        result.errors.append("Soak report not found")
        return result
    
    # Load soak report
    with open(report_path, 'r') as f:
        soak_status = json.load(f)
    
    # Check demo account
    result.demo_account_verified = soak_status.get("executor_connected", False)
    
    # Check audit log for issues
    if result.audit_log_exists:
        with open(audit_path, 'r') as f:
            audit_lines = f.readlines()
        
        for line in audit_lines:
            if "Live account" in line or "live" in line.lower():
                result.live_account_attempts += 1
            if "unknown" in line.lower():
                result.unknown_account_attempts += 1
            if "stop_loss" in line.lower() and "required" in line.lower():
                result.missing_stop_loss_orders += 1
    
    # Check soak status for safety
    result.emergency_stop_events = 1 if soak_status.get("emergency_stop", False) else 0
    result.max_drawdown_pct = soak_status.get("max_drawdown_pct", 0.0)
    result.max_daily_loss = abs(soak_status.get("executor_daily_pnl", 0.0))
    
    # Check trades
    if os.path.exists(trades_path):
        try:
            trades_df = pd.read_csv(trades_path)
            result.total_trades = len(trades_df)
            result.order_history_readable = True
        except:
            result.warnings.append("Could not read trades CSV")
    
    # Check rejections
    if os.path.exists(rejections_path):
        try:
            rejections_df = pd.read_csv(rejections_path)
            result.total_rejections = len(rejections_df)
        except:
            result.warnings.append("Could not read rejections")
    
    # Check open positions
    result.safety_status_readable = True  # Always readable from soak status
    
    # Calculate score
    score = 100
    
    # Penalties
    if not result.demo_account_verified:
        score -= 30
        result.errors.append("Demo account not verified")
    
    if result.live_account_attempts > 0:
        score -= 20
        result.errors.append(f"Live account attempts: {result.live_account_attempts}")
    
    if result.unknown_account_attempts > 0:
        score -= 20
        result.errors.append(f"Unknown account attempts: {result.unknown_account_attempts}")
    
    if result.emergency_stop_events > 0:
        score -= 25
        result.errors.append("Emergency stop was triggered")
    
    if result.max_drawdown_pct > config.max_drawdown_threshold:
        score -= 15
        result.warnings.append(f"Max drawdown {result.max_drawdown_pct}% > {config.max_drawdown_threshold}%")
    
    if result.max_daily_loss > config.max_daily_loss_threshold:
        score -= 15
        result.warnings.append(f"Max daily loss ${result.max_daily_loss} > ${config.max_daily_loss_threshold}")
    
    if result.total_trades > 0 and result.total_rejections > 0:
        rejection_rate = result.total_rejections / (result.total_trades + result.total_rejections)
        if rejection_rate > config.max_rejection_rate:
            score -= 10
            result.warnings.append(f"Rejection rate {rejection_rate:.1%} > {config.max_rejection_rate:.1%}")
    
    # File checks
    if not result.audit_log_exists:
        score -= 10
        result.errors.append("Audit log not found")
    
    if not result.soak_report_exists:
        score -= 20
        result.errors.append("Soak report not found")
    
    if not result.order_history_readable:
        score -= 5
        result.warnings.append("Order history not readable")
    
    result.score = max(0, score)
    result.passed = result.score >= 70 and len(result.errors) == 0
    
    return result

def write_demo_readiness_report(result: DemoReadinessResult, output_path: str) -> None:
    """Write readiness report to JSON file."""
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": result.passed,
        "score": result.score,
        "max_score": result.max_score,
        "READY_FOR_LIVE_REVIEW": result.passed,
        
        # Verification
        "demo_account_verified": result.demo_account_verified,
        "live_account_attempts": result.live_account_attempts,
        "unknown_account_attempts": result.unknown_account_attempts,
        "missing_stop_loss_orders": result.missing_stop_loss_orders,
        
        # Safety
        "emergency_stop_events": result.emergency_stop_events,
        "max_drawdown_pct": result.max_drawdown_pct,
        "max_daily_loss": result.max_daily_loss,
        
        # Activity
        "total_trades": result.total_trades,
        "total_rejections": result.total_rejections,
        
        # Files
        "audit_log_exists": result.audit_log_exists,
        "soak_report_exists": result.soak_report_exists,
        "order_history_readable": result.order_history_readable,
        
        # Issues
        "warnings": result.warnings,
        "errors": result.errors,
    }
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

def generate_readiness_markdown(result: DemoReadinessResult) -> str:
    """Generate markdown summary of readiness."""
    md = f"""# Demo Trading Readiness Report

Generated: {datetime.now(timezone.utc).isoformat()}

## Overall Status

| Metric | Value |
|--------|-------|
| **PASSED** | {'✅ YES' if result.passed else '❌ NO'} |
| Score | {result.score}/{result.max_score} |

## Verification

| Check | Status |
|-------|--------|
| Demo Account Verified | {'✅' if result.demo_account_verified else '❌'} |
| Live Account Attempts | {result.live_account_attempts} |
| Unknown Account Attempts | {result.unknown_account_attempts} |
| Missing Stop-Loss Orders | {result.missing_stop_loss_orders} |

## Safety

| Check | Value |
|-------|-------|
| Emergency Stop Events | {result.emergency_stop_events} |
| Max Drawdown % | {result.max_drawdown_pct:.1f}% |
| Max Daily Loss | ${result.max_daily_loss:.2f} |

## Activity

| Metric | Count |
|--------|-------|
| Total Trades | {result.total_trades} |
| Total Rejections | {result.total_rejections} |

## File Status

| File | Exists |
|------|--------|
| Audit Log | {'✅' if result.audit_log_exists else '❌'} |
| Soak Report | {'✅' if result.soak_report_exists else '❌'} |
| Order History | {'✅' if result.order_history_readable else '❌'} |

## Issues

### Errors
"""
    for err in result.errors:
        md += f"- ❌ {err}\n"
    
    md += "\n### Warnings\n"
    for warn in result.warnings:
        md += f"- ⚠️ {warn}\n"
    
    md += f"""

## Recommendation

**READY_FOR_LIVE_REVIEW = {'TRUE' if result.passed else 'FALSE'}**

This indicates {'Demo Trading Mode is ready for human review before Live Trading work.' if result.passed else 'Demo Trading Mode requires fixes before Live Trading work.'}

---
Note: This does NOT enable Live Trading Mode. Live trading remains disabled.
"""
    return md