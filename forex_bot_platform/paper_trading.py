"""Internal simulation scaffold for Phase 2.10.

This module provides internal simulation (app-only simulated trades),
including deterministic fixtures, per-trade risk sizing, and SQLite-backed storage.
No broker orders are placed. No real money is used.
Backtest Mode uses historical data. Internal Simulation uses live data without broker.
"""
from typing import List, Optional, Dict, Any
import pandas as pd
import sqlite3
import os
from datetime import datetime, timezone

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

class PaperTrade:
    def __init__(self, date_open: Optional[pd.Timestamp] = None, pair: Optional[str] = None,
                 side: Optional[int] = None, units: int = 0, entry_price: float = 0.0,
                 stop_price: Optional[float] = None, take_price: Optional[float] = None,
                 exit_price: Optional[float] = None, exit_reason: Optional[str] = None,
                 date_close: Optional[pd.Timestamp] = None, equity_at_entry: float = 0.0,
                 duration: Optional[int] = None, unrealised_pnl: Optional[float] = None,
                 realised_pnl: Optional[float] = None):
        self.date_open = date_open
        self.date_close = date_close
        self.pair = pair
        self.side = side
        self.units = units
        self.entry_price = entry_price
        self.stop_price = stop_price
        self.take_price = take_price
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        self.equity_at_entry = equity_at_entry
        self.duration = duration
        self.unrealised_pnl = unrealised_pnl
        self.realised_pnl = realised_pnl
        self.pnl = (exit_price - entry_price) * self.side * self.units if (exit_price is not None and self.side is not None) else None

    def unrealised_pnl_at(self, price: float) -> float:
        if self.entry_price is None or self.units is None or self.side is None:
            return 0.0
        return (price - self.entry_price) * self.side * max(0, self.units)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date_open": str(self.date_open) if self.date_open else None,
            "date_close": str(self.date_close) if self.date_close else None,
            "pair": self.pair,
            "side": self.side,
            "units": self.units,
            "entry_price": self.entry_price,
            "stop_price": self.stop_price,
            "take_price": self.take_price,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "equity_at_entry": self.equity_at_entry,
            "duration": self.duration,
            "realised_pnl": self.realised_pnl,
            "unrealised_pnl": self.unrealised_pnl,
        }

class PaperSession:
    def __init__(self, session_id: Optional[int] = None, pair: str = "EURUSD",
                 initial_balance: float = 100000.0, current_balance: float = 100000.0,
                 start_date: Optional[str] = None, end_date: Optional[str] = None,
                 status: str = "active"):
        self.session_id = session_id
        self.pair = pair
        self.initial_balance = initial_balance
        self.current_balance = current_balance
        self.start_date = start_date
        self.end_date = end_date
        self.status = status

class PaperTradeStorage:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join(os.path.dirname(__file__), "data", "paper_trades.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self._init_db()

    def _init_db(self):
        cur = self.conn.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS paper_sessions (session_id INTEGER PRIMARY KEY AUTOINCREMENT, pair TEXT NOT NULL, initial_balance REAL NOT NULL, current_balance REAL NOT NULL, start_date TEXT, end_date TEXT, status TEXT DEFAULT "active")')
        cur.execute('CREATE TABLE IF NOT EXISTS paper_trades (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, pair TEXT, side INTEGER, units INTEGER, entry_price REAL, exit_price REAL, exit_reason TEXT, equity_at_entry REAL, realised_pnl REAL)')
        cur.execute('CREATE TABLE IF NOT EXISTS open_positions (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id INTEGER, pair TEXT, side INTEGER, units INTEGER, entry_price REAL, stop_price REAL, take_price REAL, equity_at_entry REAL)')
        self.conn.commit()

    def create_session(self, pair: str, initial_balance: float) -> int:
        cur = self.conn.cursor()
        now = _now_iso()
        cur.execute(
            'INSERT INTO paper_sessions (pair, initial_balance, current_balance, start_date, status) VALUES (?, ?, ?, ?, ?)',
            (pair, initial_balance, initial_balance, now, 'active')
        )
        self.conn.commit()
        return cur.lastrowid

    def close_session(self, session_id: int, final_balance: float):
        cur = self.conn.cursor()
        now = _now_iso()
        cur.execute(
            'UPDATE paper_sessions SET current_balance = ?, end_date = ?, status = ? WHERE session_id = ?',
            (final_balance, now, 'closed', session_id)
        )
        self.conn.commit()

    def get_active_session(self) -> Optional[PaperSession]:
        cur = self.conn.cursor()
        cur.execute("SELECT session_id, pair, initial_balance, current_balance, start_date, status FROM paper_sessions WHERE status = 'active' ORDER BY session_id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            return PaperSession(session_id=row[0], pair=row[1], initial_balance=row[2], current_balance=row[3], start_date=row[4], status=row[5])
        return None

    def write_trade(self, trade: PaperTrade, session_id: Optional[int] = None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO paper_trades (session_id, pair, side, units, entry_price, exit_price, exit_reason, equity_at_entry, realised_pnl) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                trade.pair,
                trade.side,
                trade.units,
                trade.entry_price,
                trade.exit_price,
                trade.exit_reason,
                trade.equity_at_entry,
                trade.realised_pnl,
            ),
        )
        self.conn.commit()

    def write_open_position(self, trade: PaperTrade, session_id: Optional[int] = None):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO open_positions (id, session_id, pair, side, units, entry_price, stop_price, take_price, equity_at_entry) VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                trade.pair,
                trade.side,
                trade.units,
                trade.entry_price,
                trade.stop_price if trade.stop_price else 0.0,
                trade.take_price if trade.take_price else 0.0,
                trade.equity_at_entry,
            ),
        )
        self.conn.commit()

    def close_open_position(self, trade: PaperTrade, session_id: Optional[int] = None):
        pass

    def read_trades(self, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if session_id:
            cur.execute("SELECT session_id, pair, side, units, entry_price, exit_price, exit_reason, equity_at_entry, realised_pnl FROM paper_trades WHERE session_id = ?", (session_id,))
        else:
            cur.execute("SELECT session_id, pair, side, units, entry_price, exit_price, exit_reason, equity_at_entry, realised_pnl FROM paper_trades")
        rows = cur.fetchall()
        cols = ['session_id', 'pair', 'side', 'units', 'entry_price', 'exit_price', 'exit_reason', 'equity_at_entry', 'realised_pnl']
        return [dict(zip(cols, r)) for r in rows]

    def read_open_positions(self, session_id: Optional[int] = None) -> List[Dict[str, Any]]:
        cur = self.conn.cursor()
        if session_id:
            cur.execute("SELECT * FROM open_positions WHERE session_id = ? ORDER BY date_open ASC", (session_id,))
        else:
            cur.execute("SELECT * FROM open_positions ORDER BY date_open ASC")
        rows = cur.fetchall()
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, r)) for r in rows]

    def read_session_trades(self, session_id: int) -> List[PaperTrade]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM paper_trades WHERE session_id = ? ORDER BY date_open ASC", (session_id,))
        rows = cur.fetchall()
        trades = []
        for r in rows:
            trades.append(PaperTrade(
                date_open=pd.Timestamp(r[2]) if r[2] else None,
                date_close=pd.Timestamp(r[3]) if r[3] else None,
                pair=r[4],
                side=r[5],
                units=r[6],
                entry_price=r[7],
                stop_price=r[8],
                take_price=r[9],
                exit_price=r[10],
                exit_reason=r[11],
                equity_at_entry=r[12],
                duration=r[13],
                realised_pnl=r[14],
            ))
        return trades

    def get_performance_stats(self, session_id: Optional[int] = None) -> Dict[str, Any]:
        cur = self.conn.cursor()
        if session_id:
            cur.execute("SELECT exit_reason, COUNT(*), SUM(realised_pnl) FROM paper_trades WHERE session_id = ? GROUP BY exit_reason", (session_id,))
        else:
            cur.execute("SELECT exit_reason, COUNT(*), SUM(realised_pnl) FROM paper_trades GROUP BY exit_reason")
        rows = cur.fetchall()
        total_trades = sum(r[1] for r in rows)
        total_pnl = sum(r[2] for r in rows if r[2] is not None) or 0.0
        stats = {"total_trades": total_trades, "total_pnl": total_pnl, "by_exit_reason": {}}
        for r in rows:
            stats["by_exit_reason"][r[0]] = {"count": r[1], "total_pnl": r[2]}
        if session_id:
            cur.execute("SELECT initial_balance, current_balance FROM paper_sessions WHERE session_id = ?", (session_id,))
        else:
            cur.execute("SELECT initial_balance, current_balance FROM paper_sessions ORDER BY session_id DESC LIMIT 1")
        row = cur.fetchone()
        if row:
            stats["initial_balance"] = row[0]
            stats["current_balance"] = row[1]
            stats["return_pct"] = ((row[1] - row[0]) / row[0] * 100) if row[0] > 0 else 0
        return stats

    def export_journal(self, path: str, session_id: Optional[int] = None):
        trades = self.read_trades(session_id)
        if not trades:
            return False
        df = pd.DataFrame(trades)
        df.to_csv(path, index=False)
        return True

    def close(self):
        self.conn.close()

class PaperTrader:
    def __init__(self, initial_balance: float, data: pd.DataFrame, pair: str, strategy,
                 risk_per_trade: float = 0.01, stop_loss_pips: int = 50, take_profit_pips: Optional[int] = None,
                 max_concurrent: int = 3, storage: Optional[PaperTradeStorage] = None):
        self.balance = initial_balance
        self.initial_balance = initial_balance
        self.data = data
        self.pair = pair
        self.strategy = strategy
        self.risk_per_trade = risk_per_trade
        self.stop_loss_pips = stop_loss_pips
        self.take_profit_pips = take_profit_pips or (stop_loss_pips * 2)
        self.max_concurrent = max_concurrent
        self.storage = storage or PaperTradeStorage()
        self.open_positions: List[PaperTrade] = []
        self.closed_positions: List[PaperTrade] = []
        self.daily_pnl: List[float] = []
        self.equity_path: List[float] = [initial_balance]
        self.current_index = 0
        self.running = False
        self.session_id: Optional[int] = None

    def _calc_units(self, price: float) -> int:
        try:
            from forex_bot_platform.risk.risk_manager import calculate_position_size, is_jpy_pair
        except Exception:
            calculate_position_size = lambda *a, **k: 1
        units = calculate_position_size(self.pair, self.balance, self.risk_per_trade, self.stop_loss_pips, max_position_size=None, max_exposure_per_currency=None)
        return max(1, int(units))

    def start(self, session_id: Optional[int] = None):
        if session_id:
            self.session_id = session_id
        else:
            self.session_id = self.storage.create_session(self.pair, self.initial_balance)
        self.open_positions.clear()
        self.closed_positions.clear()
        self.daily_pnl.clear()
        self.equity_path = [self.balance]
        self.current_index = 0
        self.running = True

    def recover_session(self, session_id: int) -> bool:
        session = self.storage.get_active_session()
        if not session or session.session_id != session_id:
            return False
        self.session_id = session_id
        self.balance = session.current_balance
        self.initial_balance = session.initial_balance
        open_pos = self.storage.read_open_positions(session_id)
        self.open_positions.clear()
        for p in open_pos:
            self.open_positions.append(PaperTrade(
                date_open=pd.Timestamp(p["date_open"]),
                pair=p["pair"],
                side=p["side"],
                units=p["units"],
                entry_price=p["entry_price"],
                stop_price=p["stop_price"],
                take_price=p["take_price"],
                equity_at_entry=p["equity_at_entry"],
            ))
        closed = self.storage.read_session_trades(session_id)
        self.closed_positions = closed
        self.current_index = 0
        self.running = True
        return True

    def get_open_positions_count(self) -> int:
        return len(self.open_positions)

    def reset(self):
        self.start()

    def step(self) -> bool:
        if not self.running:
            return False
        if self.current_index >= len(self.data):
            self.running = False
            return False
        row = self.data.iloc[self.current_index]
        price = row["close"]
        date = row["date"]
        try:
            sig = int(self.strategy.generate_signal(self.data.iloc[: self.current_index + 1]))
        except Exception:
            sig = 0

        # Open new position if allowed - but only if we don't have ANY positions open (signal flip should close, not replace)
        if len(self.open_positions) == 0 and sig != 0:
            side = 1 if sig > 0 else -1
            units = self._calc_units(price)
            entry_price = price
            # Handle stop_loss_pips=0 as "no stop loss"
            if self.stop_loss_pips and self.stop_loss_pips > 0:
                # Pips are in 1/10000 (4th decimal): 50 pips = 0.0050
                pip_multiplier = 0.0001
                stop_price = entry_price - (self.stop_loss_pips * pip_multiplier) if side == 1 else entry_price + (self.stop_loss_pips * pip_multiplier)
            else:
                stop_price = None
            if self.take_profit_pips and self.take_profit_pips > 0:
                pip_multiplier = 0.0001
                take_price = entry_price + (self.take_profit_pips * pip_multiplier) if side == 1 else entry_price - (self.take_profit_pips * pip_multiplier)
            else:
                take_price = None
            trade = PaperTrade(date_open=date, pair=self.pair, side=side, units=units, entry_price=entry_price,
                               stop_price=stop_price, take_price=take_price, exit_price=None, exit_reason=None,
                               date_close=None, equity_at_entry=self.balance, duration=None, unrealised_pnl=None, realised_pnl=None)
            self.open_positions.append(trade)

        # Manage existing positions
        to_close = []
        for t in self.open_positions:
            # Unrealised PnL per position
            current_pnL = (price - t.entry_price) * t.side * t.units
            t.unrealised_pnl = current_pnL
            # Exit on stop / take
            if t.stop_price is not None:
                if (t.side == 1 and price <= t.stop_price) or (t.side == -1 and price >= t.stop_price):
                    t.exit_price = t.stop_price
                    t.exit_reason = 'stop_loss'
                    t.duration = (self.current_index - row.name) if hasattr(row, 'name') else None
                    to_close.append(t)
                    continue
            if t.take_price is not None:
                if (t.side == 1 and price >= t.take_price) or (t.side == -1 and price <= t.take_price):
                    t.exit_price = t.take_price
                    t.exit_reason = 'take_profit'
                    t.duration = (self.current_index - row.name) if hasattr(row, 'name') else None
                    to_close.append(t)
                    continue
            # Signal flip exit: opposite signal closes position
            should_flip = sig != 0 and ((t.side == 1 and sig < 0) or (t.side == -1 and sig > 0))
            if should_flip:
                t.exit_price = price
                t.exit_reason = 'signal_flip'
                t.duration = (self.current_index - row.name) if hasattr(row, 'name') else None
                to_close.append(t)
                continue
        for t in to_close:
            self.open_positions.remove(t)
            t.date_close = date
            t.realised_pnl = (t.exit_price - t.entry_price) * t.side * t.units
            self.balance += t.realised_pnl
            self.closed_positions.append(t)
            # Persist closed trade with session
            self.storage.write_trade(t, self.session_id)
            self.storage.close_open_position(t, self.session_id)
        for t in self.open_positions:
            self.storage.write_open_position(t, self.session_id)
        self.current_index += 1
        self.equity_path.append(self.balance)
        self.daily_pnl.append(self.balance - (self.equity_path[-2] if len(self.equity_path) >= 2 else self.balance))
        return True

    def run_to_end(self):
        self.start()
        while self.step():
            pass
        return self.get_performance_report()

    def close_session(self):
        if self.session_id:
            self.storage.close_session(self.session_id, self.balance)

    def get_performance_report(self) -> Dict[str, Any]:
        if not self.session_id:
            return {}
        stats = self.storage.get_performance_stats(self.session_id)
        return stats

    def export_trades_csv(self, path: str = "paper_trades.csv"):
        records = []
        for t in self.closed_positions:
            records.append({"date_open": t.date_open, "date_close": t.date_close, "pair": t.pair, "side": t.side, "units": t.units, "entry_price": t.entry_price, "exit_price": t.exit_price, "exit_reason": t.exit_reason, "equity_at_entry": t.equity_at_entry, "pnl": t.realised_pnl, "duration": t.duration})
        if records:
            pd.DataFrame(records).to_csv(path, index=False)
        return path

    def export_all_sqlite(self, db_path: Optional[str] = None):
        path = db_path or self.storage.db_path
        self.storage = self.storage if hasattr(self, 'storage') else PaperTradeStorage(db_path=path)
        for t in self.closed_positions:
            self.storage.write_trade(t, self.session_id)
        return path

    def export_journal(self, path: str = "paper_trading_journal.csv"):
        self.storage.export_journal(path, self.session_id)
