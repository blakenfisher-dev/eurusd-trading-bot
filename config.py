import os
from dataclasses import dataclass


@dataclass
class TradingConfig:
    INITIAL_BALANCE: float = 10000.0
    
    SYMBOL: str = "EURUSD"
    TIMEFRAME: str = "H1"
    
    MAX_RISK_PER_TRADE: float = 0.02
    MAX_DAILY_LOSS: float = 0.05
    MAX_DRAWDOWN: float = 0.15
    MAX_OPEN_POSITIONS: int = 1
    MAX_LEVERAGE: float = 30.0
    
    SPREAD: float = 0.00015
    COMMISSION: float = 0.0
    SLIPPAGE: float = 0.00005
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "trading_bot.log"
    
    @classmethod
    def from_env(cls):
        return cls(
            INITIAL_BALANCE=float(os.getenv("INITIAL_BALANCE", "10000")),
            MAX_RISK_PER_TRADE=float(os.getenv("MAX_RISK_PER_TRADE", "0.02")),
            MAX_DAILY_LOSS=float(os.getenv("MAX_DAILY_LOSS", "0.05")),
            SYMBOL=os.getenv("SYMBOL", "EURUSD"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO")
        )


@dataclass 
class StrategyConfig:
    TREND_FASTER_EMA: int = 9
    TREND_SLOW_EMA: int = 21
    TREND_RSI_PERIOD: int = 14
    TREND_RSI_OVERBOUGHT: float = 70
    TREND_RSI_OVERSOLD: float = 30
    
    MEAN_REVERSION_BB_PERIOD: int = 20
    MEAN_REVERSION_BB_STD: float = 2.0
    MEAN_REVERSION_RSI_PERIOD: int = 14
    
    BREAKOUT_LOOKBACK: int = 20
    BREAKOUT_ATR_PERIOD: int = 14
    
    SUPERTREND_PERIOD: int = 10
    SUPERTREND_MULTIPLIER: float = 3.0
    
    @classmethod
    def from_env(cls):
        return cls(
            TREND_FASTER_EMA=int(os.getenv("TREND_FASTER_EMA", "9")),
            TREND_SLOW_EMA=int(os.getenv("TREND_SLOW_EMA", "21")),
        )