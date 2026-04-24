import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time
import yfinance as yf

st.set_page_config(
    page_title="EURUSD Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    :root {
        --bg-primary: #0a0a0f;
        --bg-secondary: #12121a;
        --bg-card: rgba(18, 18, 26, 0.8);
        --accent-primary: #6366f1;
        --accent-secondary: #8b5cf6;
        --accent-green: #10b981;
        --accent-red: #ef4444;
        --accent-yellow: #f59e0b;
        --accent-cyan: #06b6d4;
        --text-primary: #ffffff;
        --text-secondary: #a1a1aa;
        --text-muted: #71717a;
        --border-color: rgba(255, 255, 255, 0.1);
        --glow-primary: rgba(99, 102, 241, 0.4);
    }
    
    * {
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-cyan));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-radius: 12px;
        padding: 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--text-secondary);
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        box-shadow: 0 4px 20px var(--glow-primary);
    }
    
    .glass-card {
        background: var(--bg-card);
        backdrop-filter: blur(20px);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 24px;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        box-shadow: 0 8px 32px rgba(99, 102, 241, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.05));
        border: 1px solid rgba(99, 102, 241, 0.2);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, var(--text-primary), var(--text-secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .metric-label {
        color: var(--text-muted);
        font-size: 0.875rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .metric-delta {
        font-size: 0.875rem;
        margin-top: 4px;
    }
    
    .profit { color: var(--accent-green) !important; }
    .loss { color: var(--accent-red) !important; }
    
    .stMetric {
        background: transparent !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary)) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 32px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 20px var(--glow-primary) !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 32px var(--glow-primary) !important;
    }
    
    .stSelectbox > div > div {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 12px !important;
    }
    
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, var(--accent-primary), var(--accent-secondary)) !important;
    }
    
    .sidebar .stSlider > div > div > div {
        background: var(--bg-secondary) !important;
    }
    
    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-running {
        background: var(--accent-green);
        animation: pulse-green 2s infinite;
    }
    
    .status-stopped {
        background: var(--accent-red);
    }
    
    @keyframes pulse-green {
        0%, 100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        50% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
    }
    
    .section-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 16px;
    }
    
    .nav-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 16px 0;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 24px;
    }
    
    .glow-text {
        text-shadow: 0 0 20px var(--glow-primary);
    }
    
    .chart-container {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 16px;
        padding: 20px;
    }
    
    div[data-testid="stHorizontalBlock"] {
        gap: 16px;
    }
    
    .stSuccess { background: var(--accent-green) !important; }
    .stWarning { background: var(--accent-yellow) !important; }
    .stError { background: var(--accent-red) !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<h1 class="main-header glow-text">📈 EURUSD Trading Bot</h1>', unsafe_allow_html=True)

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
    st.session_state.mode = 'demo'
    st.session_state.backtesting = False
    st.session_state.paper_trading = False
    st.session_state.backtest_days = 90
    st.session_state.backtest_speed = 10

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    mode = st.radio("Mode", ["🎮 Demo", "📄 Paper Trading", "💰 Live"], horizontal=True)
    
    if mode == "🎮 Demo":
        st.session_state.mode = 'demo'
        st.session_state.backtesting = st.checkbox("⏪ Backtest Mode", value=False)
    elif mode == "📄 Paper Trading":
        st.session_state.mode = 'paper'
        st.session_state.paper_trading = True
    else:
        st.session_state.mode = 'live'
    
    st.divider()
    
    st.markdown("**Strategy**")
    strategy_choice = st.selectbox(
        "Select",
        ["Breakout", "SuperTrend", "TrendFollower", "MeanReversion", "Combo"],
        label_visibility="collapsed"
    )
    
    st.divider()
    
    st.markdown("**Risk Management**")
    risk_per_trade = st.slider("Risk per Trade", 0.5, 5.0, 2.0)
    max_daily_loss = st.slider("Max Daily Loss", 1.0, 10.0, 5.0)
    max_leverage = st.slider("Max Leverage", 10, 100, 30)
    
    st.divider()
    
    st.markdown("**Account**")
    initial_balance = st.number_input("Balance", 1000, 100000, 10000, step=1000, label_visibility="collapsed")
    
    if st.session_state.backtesting:
        st.divider()
        st.markdown("**Backtest**")
        st.session_state.backtest_days = st.slider("Days", 30, 365, 90)
        st.session_state.backtest_speed = st.slider("Speed", 1, 100, 10)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Start", use_container_width=True):
            st.session_state.trading = True
    with col2:
        if st.button("⏹️ Stop", use_container_width=True):
            st.session_state.trading = False
    
    st.divider()
    
    status_text = "Running" if st.session_state.trading else "Stopped"
    status_class = "status-running" if st.session_state.trading else "status-stopped"
    st.markdown(f"**Status:** <span class='status-dot {status_class}'></span>{status_text}", unsafe_allow_html=True)
    
    if st.session_state.mode == 'live':
        st.warning("⚠️ Real money at risk")
    elif st.session_state.mode == 'paper':
        st.info("📝 Paper trading")

cols = st.columns(5)

metrics_data = [
    ("💰", "Balance", f"${st.session_state.balance:,.2f}", f"{st.session_state.profit_total:+,.2f}"),
    ("📊", "Equity", f"${st.session_state.equity:,.2f}", f"{((st.session_state.equity - st.session_state.initial_balance)/st.session_state.initial_balance)*100:+.2f}%"),
    ("🎯", "Win Rate", f"{(st.session_state.win_count / (st.session_state.win_count + st.session_state.loss_count) * 100) if (st.session_state.win_count + st.session_state.loss_count) > 0 else 0:.1f}%", f"{st.session_state.win_count}W/{st.session_state.loss_count}L"),
    ("📈", "Total Trades", f"{st.session_state.win_count + st.session_state.loss_count}", ""),
    ("📉", "Max DD", f"{max(0, ((max(st.session_state.equity_curve) - st.session_state.equity_curve[-1]) / max(st.session_state.equity_curve) * 100) if len(st.session_state.equity_curve) > 1 else 0):.2f}%", "")
]

for i, (icon, label, value, delta) in enumerate(metrics_data):
    with cols[i]:
        st.metric(label=label, value=value, delta=delta if delta else None)

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 Equity", "💰 Profit", "📊 Performance", "📋 History", "🕐 Chart"])

with tab1:
    if len(st.session_state.equity_curve) > 1:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=list(range(len(st.session_state.equity_curve))),
            y=st.session_state.equity_curve,
            mode='lines',
            name='Equity',
            line=dict(color='#6366f1', width=3),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.15)'
        ))
        
        fig.add_hline(
            y=st.session_state.initial_balance,
            line_dash="dash",
            line_color="rgba(255,255,255,0.3)",
            annotation_text="Initial Balance"
        )
        
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450,
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(color='#a1a1aa'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True, zeroline=False),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True, zeroline=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("🎯 Start trading to see your equity curve")

with tab2:
    if len(st.session_state.profit_curve) > 1:
        fig = go.Figure()
        
        color = '#10b981' if st.session_state.profit_curve[-1] >= 0 else '#ef4444'
        fill_color = 'rgba(16, 185, 129, 0.2)' if st.session_state.profit_curve[-1] >= 0 else 'rgba(239, 68, 68, 0.2)'
        
        fig.add_trace(go.Scatter(
            x=list(range(len(st.session_state.profit_curve))),
            y=st.session_state.profit_curve,
            mode='lines',
            name='Cumulative Profit',
            line=dict(color=color, width=3),
            fill='tozeroy',
            fillcolor=fill_color
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
        
        fig.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=450,
            margin=dict(l=0, r=0, t=20, b=0),
            font=dict(color='#a1a1aa'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True, zeroline=False),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', showgrid=True, zeroline=False)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("💰 Start trading to see profit accumulation")

with tab3:
    col_p1, col_p2 = st.columns(2)
    
    with col_p1:
        st.markdown("### Win/Loss Distribution")
        if len(st.session_state.trades) > 0:
            fig = go.Figure(data=[go.Pie(
                labels=['Wins', 'Losses'],
                values=[st.session_state.win_count, st.session_state.loss_count],
                marker=dict(colors=['#10b981', '#ef4444']),
                hole=0.6
            )])
            fig.update_layout(
                template='plotly_dark',
                height=300,
                margin=dict(l=20, r=20, t=20, b=20),
                paper_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No trades yet")
    
    with col_p2:
        st.markdown("### Risk Metrics")
        if len(st.session_state.trades) > 0:
            wins = [t['pnl'] for t in st.session_state.trades if t.get('pnl', 0) > 0]
            losses = [t['pnl'] for t in st.session_state.trades if t.get('pnl', 0) < 0]
            
            avg_win = np.mean(wins) if wins else 0
            avg_loss = np.mean(losses) if losses else 0
            pf = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
            
            metrics = [
                ("Avg Win", f"${avg_win:+.2f}", "#10b981"),
                ("Avg Loss", f"${avg_loss:,.2f}", "#ef4444"),
                ("Profit Factor", f"{pf:.2f}", "#6366f1"),
                ("Expectancy", f"${(avg_win * len(wins) - abs(avg_loss) * len(losses)) / len(st.session_state.trades):.2f}", "#f59e0b")
            ]
            
            for name, value, color in metrics:
                st.markdown(f"""
                <div class="glass-card" style="padding: 12px 16px; margin-bottom: 8px;">
                    <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">{name}</div>
                    <div style="color: {color}; font-size: 1.5rem; font-weight: 700;">{value}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No trades yet")

with tab4:
    if len(st.session_state.trades) > 0:
        trades_df = pd.DataFrame(st.session_state.trades)
        trades_df['Result'] = trades_df['pnl'].apply(lambda x: '✅ WIN' if x > 0 else '❌ LOSS')
        trades_df['P&L'] = trades_df['pnl'].apply(lambda x: f"${x:+,.2f}")
        
        display_cols = ['entry_time', 'direction', 'entry_price', 'exit_price', 'P&L', 'Result']
        available = [c for c in display_cols if c in trades_df.columns]
        
        st.dataframe(
            trades_df[available].tail(30).sort_index(ascending=False),
            use_container_width=True,
            height=400,
            hide_index=True
        )
        
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button("📥 Download CSV", trades_df.to_csv(index=False), "trades.csv", "text/csv", use_container_width=True)
        with col_dl2:
            if st.button("🗑️ Clear", use_container_width=True):
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
                name="EURUSD",
                increasing_line_color='#10b981',
                decreasing_line_color='#ef4444'
            ))
            
            fig.update_layout(
                template='plotly_dark',
                height=500,
                xaxis_rangeslider_visible=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a1a1aa'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)')
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            curr = eurusd['Close'].iloc[-1]
            prev = eurusd['Close'].iloc[-2] if len(eurusd) > 1 else curr
            chg = curr - prev
            pct = (chg / prev) * 100
            
            col_c1, col_c2 = st.columns(2)
            with col_c1:
                st.metric("Price", f"{curr:.5f}", delta=f"{chg:+.5f}")
            with col_c2:
                st.metric("Change", f"{pct:+.3f}%")
    except Exception as e:
        st.error(f"Could not load chart: {e}")

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
        days_backtest = (end_dt - start_dt).days
        periods = days_backtest * 24
        
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
        st.success(f"✅ Backtest complete! Balance: ${results['balance']:.2f} | ROI: {roi:+.2f}% | Win Rate: {results['win_rate']*100:.1f}%")
        
    except Exception as e:
        st.error(f"Backtest error: {e}")

if st.session_state.trading:
    if st.session_state.backtesting:
        run_backtest()
    else:
        if len(st.session_state.equity_curve) < 500:
            equity_change = np.random.normal(5, 25)
            st.session_state.equity_curve.append(st.session_state.equity_curve[-1] + equity_change)
            st.session_state.profit_curve.append(st.session_state.profit_curve[-1] + equity_change)
            
            if np.random.random() > 0.5:
                trade_pnl = np.random.uniform(-20, 40)
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

st.divider()
st.caption("EURUSD Trading Bot v2.0 | ⚠️ Trading involves risk | Paper trading results are simulated")