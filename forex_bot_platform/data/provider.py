"""Data provider with real (yfinance) and synthetic fallbacks."""
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
try:
    import yfinance as yf
except Exception:
    yf = None

class DataProvider:
    def __init__(self, use_real: bool = True):
        self.use_real = use_real

    def _symbol_for_pair(self, pair: str) -> str:
        # Best-effort Yahoo Finance symbol for FX pairs
        # Example: EURUSD -> EURUSD=X
        if pair.endswith("=X"):
            return pair
        return f"{pair}=X"

    def _to_df(self, data: pd.DataFrame) -> pd.DataFrame:
        if data is None:
            return None
        df = data.reset_index()
        df = df.rename(columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        # Ensure required columns
        for c in ["date", "open", "high", "low", "close", "volume"]:
            if c not in df.columns:
                return None
        # Ensure chronological order
        df = df.sort_values("date").reset_index(drop=True)
        return df[["date", "open", "high", "low", "close", "volume"]]

    def fetch_real(self, pair: str, timeframe: str, start: str | None = None, end: str | None = None) -> pd.DataFrame | None:
        if yf is None:
            return None
        symbol = self._symbol_for_pair(pair)
        interval = timeframe if timeframe in {"1m","1d","5m","15m","1h","1wk"} else "1d"
        try:
            data = yf.download(symbol, interval=interval, start=start, end=end, auto_adjust=True)
            df = self._to_df(data)
            return df
        except Exception:
            return None

    def fetch(self, pair: str, timeframe: str = "1h", periods: int = 365, start: str | None = None, end: str | None = None) -> pd.DataFrame:
        if self.use_real:
            df = self.fetch_real(pair, timeframe, start, end)
            if df is not None and not df.empty:
                return df
        # Fallback to synthetic data
        from forex_bot_platform.data.synthetic import generate_synthetic_data
        df = generate_synthetic_data(days=periods, pair=pair)
        return df
