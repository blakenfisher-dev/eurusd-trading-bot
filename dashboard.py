import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import yfinance as yf

st.set_page_config(page_title="EURUSD Trading Bot", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Geist+Mono:wght@400;500;600;700&display=swap');
    
    :root {
        --bg: #09090b;
        --card: rgba(255, 255, 255, 0.02);
        --card-border: rgba(255, 255, 255, 0.08);
        --emerald: #10b981;
        --emerald-glow: rgba(16, 185, 129, 0.15);
        --text: #ffffff;
        --text-muted: #71717a;
        --ring: rgba(16, 185, 129, 0.3);
    }
    
    * { box-sizing: border-box; }
    
    body {
        background: var(--bg) !important;
        font-family: system-ui, -apple-system, sans-serif;
    }
    
    .stApp { background: var(--bg) !important; }
    
    .dot-grid {
        background-image: radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px);
        background-size: 24px 24px;
    }
    
    .glow-blob {
        position: absolute;
        border-radius: 50%;
        filter: blur(100px);
        opacity: 0.5;
    }
    
    .card {
        background: var(--card);
        backdrop-filter: blur(20px);
        border: 1px solid var(--card-border);
        border-radius: 12px;
    }
    
    .mono { font-family: 'Geist Mono', monospace !important; }
    
    .logo-text {
        font-family: 'Geist Mono', monospace;
        background: linear-gradient(135deg, var(--text) 0%, var(--emerald) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .emerald-text { color: var(--emerald) !important; }
    .green-glow { text-shadow: 0 0 30px var(--emerald-glow); }
    
    .metric-box {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        transition: all 0.2s;
    }
    
    .metric-box:hover {
        border-color: var(--emerald);
        box-shadow: 0 0 30px var(--emerald-glow);
    }
    
    .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--text);
        line-height: 1;
        margin-bottom: 4px;
    }
    
    .metric-label {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: var(--text-muted);
    }
    
    .metric-delta {
        font-size: 0.75rem;
        margin-top: 8px;
    }
    
    .stMetric > div { gap: 0 !important; }
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.7rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: var(--text-muted) !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.75rem !important;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 4px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        color: var(--text-muted) !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        border: none !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: var(--emerald) !important;
        color: var(--bg) !important;
        font-weight: 600 !important;
    }
    
    .stButton > button {
        background: var(--emerald) !important;
        color: var(--bg) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 12px 24px !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.2s !important;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 40px var(--emerald-glow) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--card) !important;
        border: 1px solid var(--card-border) !important;
        border-radius: 10px !important;
    }
    
    .stSlider > div > div > div > div {
        background: var(--emerald) !important;
    }
    
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
        animation: pulse 2s infinite;
    }
    
    .status-running { background: var(--emerald); }
    .status-stopped { background: #ef4444; }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
        50% { opacity: 0.8; box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }
    }
    
    .table-container {
        background: var(--card);
        border: 1px solid var(--card-border);
        border-radius: 12px;
        overflow: hidden;
    }
    
    .dataframe {
        background: transparent !important;
    }
    
    .stDataFrame > div > div > div > table {
        background: transparent !important;
        border: none !important;
    }
    
    .stDataFrame [data-testid="stDataFrame"] {
        border: none !important;
    }
    
    section[data-testid="stMainBlockContainer"] {
        padding-top: 1rem !important;
    }
    
    div[data-testid="stHorizontalBlock"] {
        gap: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="position: fixed; top: 0; left: 0; right: 0; bottom: 0; pointer-events: none; z-index: 0;">
    <div class="dot-grid" style="position: absolute; inset: 0; opacity: 0.4;"></div>
    <div style="position: absolute; top: 0; left: 50%; transform: translateX(-50%); width: 600px; height: 400px; background: radial-gradient(ellipse at center, rgba(16,185,129,0.08) 0%, transparent 70%);"></div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="text-align: center; padding: 1rem 0 2rem; position: relative; z-index: 1;">
    <span style="font-family: 'Geist Mono', monospace; font-size: 1.5rem; font-weight: 700;">
        <span style="display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; background: rgba(16,185,129,0.15); border: 1px solid rgba(16,185,129,0.25); border-radius: 6px; font-size: 0.75rem; margin-right: 8px; color: var(--emerald);">&lt;/&gt;</span>
        <span class="mono" style="font-size: 1.75rem;">poly<span style="color: var(--emerald);">bot</span></span>
    </span>
    <p class="mono" style="color: var(--text-muted); font-size: 0.875rem; margin-top: 0.5rem;">EURUSD Trading Bot — Backtest & Paper Trading</p>
</div>
""", unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    st.session_state.initialized = True
    st.session_state.balance = 10000.0
    st.session_state.initial_balance = 10000.0
    st.session_state.equity = 10000.0
    st.session_state.trades = []
    st.session_state.equity_curve = [10000.0]
    st.session_state.profit_curve = [0.0]
    st.session_state.profit_total = 0
    st.session_state.win_count = 0
    st.session_state.loss_count = 0
    st.session_state.trading = False
    st.session_state.backtesting = False

with st.sidebar:
    st.markdown("""
    <div class="card" style="padding: 20px; margin-bottom: 16px;">
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
            <span class="status-dot status-running" id="statusDot"></span>
            <span id="statusText" style="color: var(--text); font-weight: 500;">Stopped</span>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div class="card" style="padding: 12px; text-align: center; cursor: pointer;" onclick="document.querySelectorAll('button')[0].click()">
                <div style="font-size: 1.25rem;">▶️</div>
                <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Start</div>
            </div>
            <div class="card" style="padding: 12px; text-align: center; cursor: pointer;" onclick="document.querySelectorAll('button')[1].click()">
                <div style="font-size: 1.25rem;">⏹️</div>
                <div style="font-size: 0.7rem; color: var(--text-muted); text-transform: uppercase;">Stop</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("#### Strategy")
    strategy_choice = st.selectbox("Select", ["Breakout", "SuperTrend", "TrendFollower", "MeanReversion", "Combo"], label_visibility="collapsed")
    
    st.markdown("#### Risk Management")
    risk_per_trade = st.slider("Risk %", 0.5, 5.0, 2.0, step=0.5)
    max_leverage = st.slider("Leverage", 10, 100, 30, step=10)
    
    st.markdown("#### Account")
    initial_balance = st.number_input("Balance", 1000, 100000, 10000, step=1000, label_visibility="collapsed")
    
    st.markdown("#### Backtest")
    st.session_state.backtesting = st.checkbox("Enable Backtest (2024-Today)", value=False)
    
    st.divider()
    
    st.markdown("""
    <div style="text-align: center; color: var(--text-muted); font-size: 0.7rem; font-family: 'Geist Mono', monospace;">
        > polybot v2.0<br>
        > non-custodial
    </div>
    """, unsafe_allow_html=True)

cols = st.columns(5)
metrics = [
    ("Balance", f"${st.session_state.balance:,.2f}", f"{st.session_state.profit_total:+,.2f}"),
    ("Equity", f"${st.session_state.equity:,.2f}", f"{((st.session_state.equity - st.session_state.initial_balance)/st.session_state.initial_balance)*100:+.2f}%"),
    ("Win Rate", f"{(st.session_state.win_count / max(1, st.session_state.win_count + st.session_state.loss_count) * 100):.1f}%", f"{st.session_state.win_count}W/{st.session_state.loss_count}L"),
    ("Trades", f"{st.session_state.win_count + st.session_state.loss_count}", ""),
    ("Max DD", f"{max(0, ((max(st.session_state.equity_curve) - st.session_state.equity_curve[-1]) / max(st.session_state.equity_curve) * 100) if len(st.session_state.equity_curve) > 1 else 0):.2f}%", "")
]

for i, (label, value, delta) in enumerate(metrics):
    with cols[i]:
        st.metric(label=label, value=value, delta=delta if delta else None)

st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Equity Curve", "Cumulative Profit", "Performance", "Trade History", "Live EURUSD"])

with tab1:
    if len(st.session_state.equity_curve) > 1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(st.session_state.equity_curve))),
            y=st.session_state.equity_curve,
            mode='lines',
            line=dict(color='#10b981', width=2),
            fill='tozeroy',
            fillcolor='rgba(16,185,129,0.1)'
        ))
        fig.add_hline(y=st.session_state.initial_balance, line_dash="dash", line_color="rgba(255,255,255,0.2)", annotation_text="Initial")
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color='#71717a'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.03)', showgrid=True, zeroline=False, showticklabels=False),
            yaxis=dict(gridcolor='rgba(255,255,255,0.03)', showgrid=True, zeroline=False)
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("▶️ Click Start in the sidebar to begin trading simulation")

with tab2:
    if len(st.session_state.profit_curve) > 1:
        color = '#10b981' if st.session_state.profit_curve[-1] >= 0 else '#ef4444'
        fill = 'rgba(16,185,129,0.1)' if st.session_state.profit_curve[-1] >= 0 else 'rgba(239,68,68,0.1)'
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=list(range(len(st.session_state.profit_curve))),
            y=st.session_state.profit_curve,
            mode='lines',
            line=dict(color=color, width=2),
            fill='tozeroy',
            fillcolor=fill
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.2)")
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400,
            margin=dict(l=0, r=0, t=10, b=0),
            font=dict(color='#71717a'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.03)', showgrid=True, zeroline=False, showticklabels=False),
            yaxis=dict(gridcolor='rgba(255,255,255,0.03)', showgrid=True, zeroline=False)
        )
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div class='card' style='padding: 16px; text-align: center;'><div class='mono' style='color: var(--emerald); font-size: 1.5rem; font-weight: 700;'>{st.session_state.profit_curve[-1]:+.2f}</div><div style='color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;'>Total P&L</div></div>", unsafe_allow_html=True)
        with col2:
            best = max(st.session_state.profit_curve)
            worst = min(st.session_state.profit_curve)
            st.markdown(f"<div class='card' style='padding: 16px; text-align: center;'><div class='mono' style='color: var(--emerald); font-size: 1.5rem; font-weight: 700;'>{best:+.2f}</div><div style='color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;'>Peak</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='card' style='padding: 16px; text-align: center;'><div class='mono' style='color: #ef4444; font-size: 1.5rem; font-weight: 700;'>{worst:+.2f}</div><div style='color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;'>Valley</div></div>", unsafe_allow_html=True)
    else:
        st.info("Start trading to see profit accumulation")

with tab3:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Win / Loss")
        if len(st.session_state.trades) > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses'],
                values=[st.session_state.win_count, st.session_state.loss_count],
                marker=dict(colors=['#10b981', '#ef4444']),
                hole=0.7,
                textinfo='none'
            )])
            fig.update_layout(
                template='plotly_dark',
                height=250,
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trades yet")
    
    with col2:
        st.markdown("### Risk Metrics")
        if len(st.session_state.trades) > 0:
            wins = [t['pnl'] for t in st.session_state.trades if t.get('pnl', 0) > 0]
            losses = [t['pnl'] for t in st.session_state.trades if t.get('pnl', 0) < 0]
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            pf = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
            
            metrics_r = [
                ("Avg Win", f"${avg_win:+.0f}", "#10b981"),
                ("Avg Loss", f"${avg_loss:.0f}", "#ef4444"),
                ("Profit Factor", f"{pf:.2f}", "#10b981"),
                ("Expectancy", f"${(avg_win * len(wins) - abs(avg_loss) * len(losses)) / max(1, len(st.session_state.trades)):.0f}", "#10b981")
            ]
            
            for name, val, clr in metrics_r:
                st.markdown(f"<div class='card' style='padding: 12px 16px; margin-bottom: 8px;'><div style='color: var(--text-muted); font-size: 0.7rem; text-transform: uppercase;'>{name}</div><div class='mono' style='color: {clr}; font-size: 1.25rem; font-weight: 700;'>{val}</div></div>", unsafe_allow_html=True)
        else:
            st.info("No trades yet")

with tab4:
    if len(st.session_state.trades) > 0:
        trades_df = pd.DataFrame(st.session_state.trades)
        trades_df['Result'] = trades_df['pnl'].apply(lambda x: '✅' if x > 0 else '❌')
        green = "#10b981"
        red = "#ef4444"
        trades_df['P&L'] = trades_df['pnl'].apply(lambda x: f"<span style='color: {green if x > 0 else red}'>${x:+,.2f}</span>")
        
        cols_show = ['entry_time', 'direction', 'entry_price', 'exit_price', 'P&L', 'Result']
        avail = [c for c in cols_show if c in trades_df.columns]
        
        st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: var(--text-muted); font-size: 0.875rem;">Recent Trades</span>
            <span class="mono" style="color: var(--text-muted); font-size: 0.75rem;">{} trades</span>
        </div>
        """.format(len(trades_df)), unsafe_allow_html=True)
        
        st.dataframe(
            trades_df[avail].tail(20).sort_index(ascending=False),
            use_container_width=True,
            height=350,
            hide_index=True
        )
        
        col_dl, col_clr = st.columns(2)
        with col_dl:
            st.download_button("📥 Export CSV", trades_df.to_csv(index=False), "trades.csv", "text/csv", use_container_width=True)
        with col_clr:
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.trades = []
                st.session_state.win_count = 0
                st.session_state.loss_count = 0
                st.session_state.equity_curve = [st.session_state.initial_balance]
                st.session_state.profit_curve = [0.0]
                st.session_state.balance = st.session_state.initial_balance
                st.rerun()
    else:
        st.info("📋 No trades recorded yet")

with tab5:
    try:
        eurusd = yf.download("EURUSD=X", period="1d", interval="5m", progress=False)
        
        if not eurusd.empty:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=eurusd.index,
                open=eurusd['Open'],
                high=eurusd['High'],
                low=eurusd['Low'],
                close=eurusd['Close'],
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444'
            ))
            fig.update_layout(
                template='plotly_dark',
                height=450,
                xaxis_rangeslider_visible=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#71717a'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.03)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.03)')
            )
            st.plotly_chart(fig, use_container_width=True)
            
            curr = eurusd['Close'].iloc[-1]
            prev = eurusd['Close'].iloc[-2] if len(eurusd) > 1 else curr
            chg = curr - prev
            pct = (chg / prev) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("EURUSD Price", f"{curr:.5f}", delta=f"{chg:+.5f}")
            with col2:
                st.metric("24h Change", f"{pct:+.3f}%")
    except:
        st.error("Could not load EURUSD data")

def run_backtest():
    import sys
    sys.path.insert(0, r'/mount/src/eurusd-trading-bot' if '/mount' in __file__ else r'C:\trading_bot')
    
    try:
        from strategies.strategies import BreakoutStrategy, SuperTrendStrategy, TrendFollowerStrategy, MeanReversionStrategy
        from backtest.backtest import Backtester
        from utils.data import load_historical_data
        
        st.info("⏳ Running backtest from Jan 2024 to today...")
        
        start_dt = datetime(2024, 1, 1)
        end_dt = datetime.now()
        periods = (end_dt - start_dt).days * 24
        
        data = load_historical_data(
            source="synthetic",
            start_date=start_dt,
            periods=periods,
            timeframe=1,
            base_price=1.1000,
            volatility=0.0008,
            trend=0.02,
            noise=0.5,
            add_trends=True,
            add_clusters=True
        )
        
        strategy_map = {
            "Breakout": BreakoutStrategy(),
            "SuperTrend": SuperTrendStrategy(),
            "TrendFollower": TrendFollowerStrategy(),
            "MeanReversion": MeanReversionStrategy()
        }
        
        strategy = strategy_map.get(strategy_choice, BreakoutStrategy())
        
        bt = Backtester(initial_balance=initial_balance, spread=0.00015)
        results = bt.run(data, strategy)
        
        for trade in results['trades']:
            st.session_state.trades.append({
                'entry_time': trade['entry_time'],
                'direction': trade['direction'],
                'entry_price': trade['entry_price'],
                'exit_price': trade['exit_price'],
                'pnl': trade['pnl'],
                'duration': 24
            })
            
            st.session_state.equity_curve.append(st.session_state.equity_curve[-1] + trade['pnl'])
            st.session_state.profit_curve.append(st.session_state.profit_curve[-1] + trade['pnl'])
            
            if trade['pnl'] > 0:
                st.session_state.win_count += 1
            else:
                st.session_state.loss_count += 1
        
        st.session_state.balance = results['balance']
        st.session_state.equity = results['balance']
        st.session_state.profit_total = results['total_pnl']
        
        roi = ((results['balance'] - initial_balance) / initial_balance) * 100
        st.success(f"✅ Backtest complete! Final: ${results['balance']:,.2f} | ROI: {roi:+.2f}% | Win Rate: {results['win_rate']*100:.1f}%")
        
    except Exception as e:
        st.error(f"Error: {e}")

if st.session_state.trading:
    if st.session_state.backtesting:
        run_backtest()
    else:
        if len(st.session_state.equity_curve) < 300:
            equity_change = np.random.normal(5, 20)
            st.session_state.equity_curve.append(st.session_state.equity_curve[-1] + equity_change)
            st.session_state.profit_curve.append(st.session_state.profit_curve[-1] + equity_change)
            
            if np.random.random() > 0.4:
                trade_pnl = np.random.uniform(-15, 35)
                st.session_state.trades.append({
                    'entry_time': datetime.now(),
                    'direction': np.random.choice(['LONG', 'SHORT']),
                    'entry_price': 1.1000,
                    'exit_price': 1.1001,
                    'pnl': trade_pnl,
                    'duration': np.random.uniform(1, 24)
                })
                
                if trade_pnl > 0:
                    st.session_state.win_count += 1
                else:
                    st.session_state.loss_count += 1
                
                st.session_state.balance += trade_pnl
                st.session_state.profit_total += trade_pnl
    
    time.sleep(0.1)
    st.rerun()

st.markdown("""
<div style="text-align: center; padding: 24px 0; color: var(--text-muted); font-size: 0.75rem; font-family: 'Geist Mono', monospace;">
    > polybot v2.0 — secure & non-custodial — trading involves risk
</div>
""", unsafe_allow_html=True)