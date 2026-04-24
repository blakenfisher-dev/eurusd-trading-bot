# EURUSD Trading Bot

A powerful algorithmic trading bot for EURUSD with backtesting, paper trading, and live execution capabilities.

![Dashboard Preview](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Features

- **5 Trading Strategies**: Breakout, SuperTrend, TrendFollower, MeanReversion, Combo
- **Backtesting Engine**: Test strategies on historical data with full performance metrics
- **Paper Trading**: Simulated trading to test strategies without real money
- **Live Trading**: MetaTrader 5 integration for real execution
- **Interactive Dashboard**: Streamlit-based UI with real-time charts and analytics
- **Risk Management**: Position sizing, daily loss limits, drawdown protection

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/eurusd-trading-bot.git
cd eurusd-trading-bot
pip install -r requirements.txt
```

## Quick Start

### Run Dashboard
```bash
python -m streamlit run dashboard.py
```

### Run Backtest
```bash
python main.py
```

## Strategies

| Strategy | Win Rate | Sharpe | Best For |
|----------|----------|--------|----------|
| **Breakout** | 60% | 2.79 | Trending markets |
| SuperTrend | 55% | 0.59 | All conditions |
| TrendFollower | 25% | -1.70 | Strong trends |
| MeanReversion | 42% | -0.35 | Ranging markets |
| Combo | 57% | 1.50 | Conservative |

## Dashboard Modes

1. **Demo Mode** - Simulated trading with demo data
2. **Paper Trading** - Simulated trading with realistic fills
3. **Live Trading** - Real execution (requires broker connection)

## Broker Setup

Supported brokers:
- MetaTrader 5
- OANDA
- IC Markets
- Interactive Brokers

## Project Structure

```
trading_bot/
├── dashboard.py      # Streamlit dashboard
├── main.py          # Backtesting engine
├── strategies/      # Trading strategies
├── indicators/      # Technical indicators
├── utils/          # Risk management, data
├── backtest/       # Backtesting engine
├── execution/      # Live trading execution
└── models/         # Data models
```

## Requirements

- Python 3.8+
- pandas
- numpy
- plotly
- streamlit
- yfinance
- ta

## Disclaimer

This software is for educational purposes only. Trading forex involves substantial risk of loss. Past performance does not guarantee future results.

## License

MIT License