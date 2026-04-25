# Axiom FX - Forex Trading Bot

A professional forex trading bot with Backtest, Demo, and Live trading modes.

## Trading Modes

### 1. Backtest Mode
Test strategies on historical data. No real money, no broker connection.

### 2. Demo Trading Mode
Connect to MT5 demo accounts only. Uses live market data with fake money.

### 3. Live Trading Mode
**DISABLED BY DEFAULT** until explicitly enabled. Requires approval file, config flag, and all safety gates.

## Setup (Windows PowerShell)

```powershell
# Clone or download the repo
cd Axiom-FX

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

## Commands

### Run Tests
```powershell
python -m pytest -q
```

### Run Backtest
```powershell
python -m forex_bot_platform.main --mode backtest --pair EURUSD --strategy Breakout --timeframe 1h
```

### Demo Dry Run
```powershell
python -m forex_bot_platform.main --mode demo-dry-run --login YOUR_LOGIN --server YOUR_SERVER
```

### Live Readiness Check
```powershell
python -m forex_bot_platform.main --mode live-readiness
```

## Supported Strategies

- **Breakout** - Trades breakouts of support/resistance levels
- **SuperTrend** - Trend-following indicator strategy
- **TrendFollower** - Moving average crossover strategy
- **MeanReversion** - Trades when price deviates from average
- **Combo** - Combines multiple strategy signals

## Supported Pairs

EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD

## Safety Warnings

- **No profit is guaranteed**
- Trading forex involves significant risk of loss
- Past backtest results do not guarantee future profits
- Live trading requires explicit approval and is disabled by default
- All live orders require stop-loss and take-profit
- Martingale, grid, and averaging strategies are forbidden
- Emergency stop is available to block all trading

## Project Structure

```
Axiom-FX/
  forex_bot_platform/
    main.py           # CLI entry point
    config/           # Configuration
    data/            # Market data provider
    strategies/      # Trading strategies
    backtesting/    # Backtest engine
    risk/            # Risk management
    execution/       # MT5 execution
    logs/            # Logging
  tests/            # Test suite
  README.md
  requirements.txt
  .gitignore
```

## License

MIT - Use at your own risk.