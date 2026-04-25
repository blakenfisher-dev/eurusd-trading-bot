"""Live Trading Audit Logger (Phase 4).

This module logs ALL live trading events for audit trail.
Logs are append-only where practical.

DISABLED BY DEFAULT - Requires --enable-live-trading flag.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path

class AuditEventType(Enum):
    CONNECTION_ATTEMPT = "connection_attempt"
    ACCOUNT_VERIFICATION = "account_verification"
    APPROVAL_VERIFICATION = "approval_verification"
    ORDER_ATTEMPT = "order_attempt"
    ORDER_REJECTION = "order_rejection"
    ORDER_SUCCESS = "order_success"
    ORDER_FAILURE = "order_failure"
    SL_TP_MODIFICATION = "sl_tp_modification"
    POSITION_CLOSE = "position_close"
    EMERGENCY_STOP = "emergency_stop"
    RECONNECT_EVENT = "reconnect_event"
    SAFETY_BREACH = "safety_breach"
    CONFIG_CHANGE = "config_change"
    LIVE_MODE_ENABLE = "live_mode_enable"
    LIVE_MODE_DISABLE = "live_mode_disable"

@dataclass
class AuditEvent:
    """Single audit event."""
    timestamp: str
    event_type: str
    success: bool
    details: str
    user: str = "system"
    ip_address: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "success": self.success,
            "details": self.details,
            "user": self.user,
            "ip_address": self.ip_address,
            "metadata": self.metadata,
        }

class LiveAuditLogger:
    """Append-only audit logger for live trading.
    
    All live trading events MUST be logged.
    """
    
    def __init__(self, log_file: str = "live_trading_audit.log"):
        self.log_file = log_file
        self._events: List[AuditEvent] = []
        self._load_existing()
    
    def _load_existing(self) -> None:
        """Load existing audit log."""
        if os.path.exists(self.log_file):
            try:
                with open(self.log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            self._events.append(AuditEvent(
                                timestamp=data["timestamp"],
                                event_type=data["event_type"],
                                success=data["success"],
                                details=data["details"],
                                user=data.get("user", "system"),
                                ip_address=data.get("ip_address", ""),
                                metadata=data.get("metadata", {}),
                            ))
            except Exception:
                pass
    
    def log(self, event_type: AuditEventType, success: bool, details: str,
            user: str = "system", metadata: Optional[Dict] = None) -> None:
        """Log an audit event."""
        event = AuditEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type.value,
            success=success,
            details=details,
            user=user,
            metadata=metadata or {},
        )
        
        self._events.append(event)
        
        # Append to file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + "\n")
        except Exception:
            pass
    
    def log_connection(self, success: bool, details: str) -> None:
        """Log connection attempt."""
        self.log(AuditEventType.CONNECTION_ATTEMPT, success, details)
    
    def log_account_verify(self, success: bool, details: str) -> None:
        """Log account verification."""
        self.log(AuditEventType.ACCOUNT_VERIFICATION, success, details)
    
    def log_approval_verify(self, success: bool, details: str) -> None:
        """Log approval verification."""
        self.log(AuditEventType.APPROVAL_VERIFICATION, success, details)
    
    def log_order_attempt(self, success: bool, details: str, metadata: Optional[Dict] = None) -> None:
        """Log order attempt."""
        self.log(AuditEventType.ORDER_ATTEMPT, success, details, metadata=metadata)
    
    def log_order_rejection(self, details: str, reason: str) -> None:
        """Log order rejection."""
        self.log(AuditEventType.ORDER_REJECTION, False, f"{details}: {reason}")
    
    def log_order_success(self, details: str, ticket: int) -> None:
        """Log order success."""
        self.log(AuditEventType.ORDER_SUCCESS, True, details, metadata={"ticket": ticket})
    
    def log_order_failure(self, details: str, error: str) -> None:
        """Log order failure."""
        self.log(AuditEventType.ORDER_FAILURE, False, f"{details}: {error}")
    
    def log_emergency_stop(self, details: str) -> None:
        """Log emergency stop."""
        self.log(AuditEventType.EMERGENCY_STOP, True, details)
    
    def log_safety_breach(self, details: str, check: str) -> None:
        """Log safety breach."""
        self.log(AuditEventType.SAFETY_BREACH, False, f"{details}: {check}")
    
    def log_live_enable(self) -> None:
        """Log live mode enable."""
        self.log(AuditEventType.LIVE_MODE_ENABLE, True, "Live trading enabled")
    
    def log_live_disable(self) -> None:
        """Log live mode disable."""
        self.log(AuditEventType.LIVE_MODE_DISABLE, True, "Live trading disabled")
    
    def get_events(self, event_type: Optional[AuditEventType] = None,
                  limit: int = 100) -> List[AuditEvent]:
        """Get audit events, optionally filtered."""
        events = self._events
        
        if event_type:
            events = [e for e in events if e.event_type == event_type.value]
        
        return events[-limit:]
    
    def get_recent_events(self, hours: int = 24) -> List[AuditEvent]:
        """Get events from last N hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)
        return [e for e in self._events if datetime.fromisoformat(e.timestamp).timestamp() > cutoff]
    
    def get_failed_events(self) -> List[AuditEvent]:
        """Get all failed events."""
        return [e for e in self._events if not e.success]
    
    def export_json(self, path: str) -> None:
        """Export audit log to JSON."""
        with open(path, 'w') as f:
            json.dump([e.to_dict() for e in self._events], f, indent=2)
    
    def get_audit_report(self) -> str:
        """Get formatted audit report."""
        lines = ["=== Live Trading Audit Log ===", ""]
        
        for event in self._events[-50:]:
            status = "✓" if event.success else "✗"
            lines.append(f"{event.timestamp[:19]} {status} [{event.event_type}] {event.details}")
        
        return "\n".join(lines)
    
    def get_summary(self) -> Dict[str, int]:
        """Get event counts by type."""
        summary = {}
        for event in self._events:
            summary[event.event_type] = summary.get(event.event_type, 0) + 1
        return summary