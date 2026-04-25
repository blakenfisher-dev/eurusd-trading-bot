"""Enhanced Streamlit dashboard (Phase 3.1) - Demo Trading Mode enabled."""
try:
    import streamlit as st
except Exception:
    st = None

from forex_bot_platform.paper_trading import PaperTrader, PaperTradeStorage
from forex_bot_platform.data.provider import DataProvider
from forex_bot_platform.strategies.breakout import Breakout
from forex_bot_platform.execution.mt5_executor import (
    MT5DemoExecutor, SafetyConfig, OrderSide, AccountType
)
import pandas as pd
from datetime import datetime

# Initialize session state for MT5 demo executor
def _init_mt5_executor() -> MT5DemoExecutor:
    if not hasattr(st, 'session_state'):
        return None
    if not hasattr(st.session_state, 'mt5'):
        config = SafetyConfig(
            max_daily_loss=1000.0,
            max_open_trades=3,
            max_exposure_per_currency=10000.0,
            max_spread=3.0,
            require_stop_loss=True,
        )
        st.session_state.mt5 = MT5DemoExecutor(safety_config=config)
    return st.session_state.mt5

def _init_paper_trader(pair: str, timeframe: str) -> PaperTrader:
    provider = DataProvider(use_real=False)
    df = provider.fetch(pair, timeframe, periods=60)
    strat = Breakout()
    storage = PaperTradeStorage()
    return PaperTrader(initial_balance=100000.0, data=df, pair=pair, strategy=strat, storage=storage)

def render_demo_trading_tab(mt5: MT5DemoExecutor):
    if st is None or mt5 is None:
        return
    st.header("Demo Trading Mode")
    
    # Connection section
    st.subheader("MT5 Connection")
    col1, col2 = st.columns(2)
    with col1:
        login = st.text_input("Login (demo account)", key="mt5_login")
        password = st.text_input("Password", type="password", key="mt5_password")
        server = st.text_input("Server", key="mt5_server", placeholder="MetaQuotes-Demo")
    with col2:
        if st.button("Connect to MT5 Demo"):
            try:
                mt5.login = login
                mt5.password = password
                mt5.server = server
                success = mt5.connect()
                if success:
                    st.success("Connected to MT5 demo account!")
                else:
                    st.error("Connection failed. Check credentials.")
            except Exception as e:
                st.error(f"Connection error: {e}")
    
    # Account info panel
    if mt5.is_connected:
        info = mt5.get_account_info()
        if info:
            st.subheader("Account Info")
            acc_cols = st.columns(4)
            acc_cols[0].metric("Account Type", info.get("account_type", "unknown").upper())
            acc_cols[1].metric("Balance", f"${info.get('balance', 0):,.2f}")
            acc_cols[2].metric("Equity", f"${info.get('equity', 0):,.2f}")
            acc_cols[3].metric("Leverage", f"1:{info.get('leverage', 100)}")
        
        # Symbol tick
        st.subheader("Live Market Data")
        symbol = st.selectbox("Symbol", ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"])
        tick = mt5.get_latest_tick(symbol)
        if tick:
            tick_cols = st.columns(3)
            tick_cols[0].metric("Bid", f"{tick.get('bid', 0):.5f}")
            tick_cols[1].metric("Ask", f"{tick.get('ask', 0):.5f}")
            tick_cols[2].metric("Spread", f"{tick.get('ask', 0) - tick.get('bid', 0):.1f} pips")
        
        # Demo order form
        st.subheader("Place Demo Order")
        ocol1, ocol2 = st.columns(2)
        with ocol1:
            order_symbol = st.selectbox("Symbol", ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"], key="order_symbol")
            order_side = st.radio("Side", ["Buy", "Sell"], horizontal=True)
            volume = st.number_input("Volume (lots)", min_value=0.01, max_value=100.0, value=0.1, step=0.01)
        with ocol2:
            stop_loss = st.number_input("Stop Loss (price)", min_value=0.0, value=1.0900, format="%.5f")
            take_profit = st.number_input("Take Profit (optional)", min_value=0.0, value=1.1100, format="%.5f")
            comment = st.text_input("Comment", placeholder="optional note")
        
        if st.button("Place Demo Order", type="primary"):
            try:
                side = OrderSide.BUY if order_side == "Buy" else OrderSide.SELL
                ticket = mt5.place_demo_order(
                    order_symbol, side, volume, 
                    stop_loss=stop_loss, 
                    take_profit=take_profit if take_profit > 0 else None,
                    comment=comment
                )
                st.success(f"Demo order placed! Ticket: {ticket}")
            except Exception as e:
                st.error(f"Order failed: {e}")
        
        # Open positions
        positions = mt5.get_open_positions()
        if positions:
            st.subheader("Open Demo Positions")
            st.dataframe(pd.DataFrame(positions))
        
        # Order history
        history = mt5.get_order_history(count=20)
        if history:
            st.subheader("Demo Order History")
            st.dataframe(pd.DataFrame(history))
        
        # Safety status
        st.subheader("Safety Status")
        safety = mt5.get_safety_status()
        safe_cols = st.columns(3)
        safe_cols[0].metric("Daily PnL", f"${safety.get('daily_pnl', 0):.2f}")
        safe_cols[1].metric("Max Daily Loss", f"${safety.get('max_daily_loss', 0):.2f}")
        safe_cols[2].metric("Open Trades", f"{safety.get('open_trades', 0)}/{safety.get('max_open_trades', 0)}")
        
        daily = mt5.get_daily_stats()
        if daily.get("emergency_stop"):
            st.error("EMERGENCY STOP TRIGGERED")
        
        # Emergency stop
        if st.button("EMERGENCY STOP", type="st"):
            reason = mt5.emergency_stop()
            st.error(f"Emergency stop triggered: {reason}")
        
        # Disconnect
        if st.button("Disconnect"):
            mt5.disconnect()
            st.info("Disconnected from MT5")
    
    else:
        st.info("Connect to MT5 demo account to start demo trading")

def render_internal_simulation_tab(pt: PaperTrader):
    if st is None:
        return
    st.header("Internal Simulation Mode")
    st.sidebar.header("Sim Settings")
    pair = st.sidebar.selectbox("Pair", ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"], key="sim_pair")
    tf = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m", "1h", "1d"], key="sim_tf")
    
    # Controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start Simulation"):
            pt.start()
        if st.button("Reset Simulation"):
            pt.reset()
        if st.button("Step Simulation"):
            pt.step()
    with col2:
        st.write("Simulation Status:")
        st.write({"balance": pt.balance if hasattr(pt, 'balance') else None, "open": len(pt.open_positions), "closed": len(pt.closed_positions)})
    
    # Open positions
    if pt.open_positions:
        open_tbl = [{"date_open": p.date_open, "pair": p.pair, "side": p.side, "units": p.units, 
                    "entry_price": p.entry_price, "stop_price": p.stop_price, "take_price": p.take_price} 
                   for p in pt.open_positions]
        st.subheader("Open Positions")
        st.dataframe(pd.DataFrame(open_tbl))
    
    # Closed positions
    if pt.closed_positions:
        cl = [{"date_close": p.date_close, "pair": p.pair, "side": p.side, "units": p.units,
               "entry_price": p.entry_price, "exit_price": p.exit_price, 
               "exit_reason": p.exit_reason, "pnl": p.pnl} 
              for p in pt.closed_positions]
        st.subheader("Closed Positions")
        st.dataframe(pd.DataFrame(cl))
    
    # Exports
    if st.button("Export CSV"):
        pt.export_trades_csv("sim_trades.csv")
    if st.button("Export SQLite"):
        pt.export_all_sqlite()
    
    # Equity path
    if hasattr(pt, 'equity_path') and pt.equity_path:
        st.subheader("Equity Path")
        try:
            st.line_chart(pd.Series(pt.equity_path))
        except Exception:
            pass

def render_dashboard():
    if st is None:
        return
    
    st.set_page_config(page_title="Forex Bot Platform", layout="wide")
    st.title("Forex Bot Platform Dashboard (Phase 3.1)")
    
    # Mode selector
    mode = st.radio("Trading Mode", ["Internal Simulation", "Demo Trading"], horizontal=True)
    
    if mode == "Demo Trading":
        mt5 = _init_mt5_executor()
        if mt5:
            render_demo_trading_tab(mt5)
    else:
        if not hasattr(st.session_state, 'pt'):
            st.session_state.pt = _init_paper_trader("EURUSD", "1h")
        pt = st.session_state.pt
        render_internal_simulation_tab(pt)

if __name__ == "__main__":
    render_dashboard()