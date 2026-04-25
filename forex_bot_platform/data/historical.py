"""Historical data loader (1-year default, synthetic by default)."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def _generate_series(pair: str, periods: int = 365, freq: str = "D"):
    # Simple synthetic OHLCV generator for demonstration purposes
    rng = pd.date_range(end=datetime.today(), periods=periods, freq=freq)
    price = 1.0 + np.cumsum(np.random.normal(loc=0.0, scale=0.5, size=periods))
    open_ = price
    high = price * (1 + np.random.rand(periods) * 0.01)
    low = price * (1 - np.random.rand(periods) * 0.01)
    close = price * (1 + (np.random.rand(periods) - 0.5) * 0.01)
    volume = np.random.randint(1000, 10000, size=periods)
    df = pd.DataFrame({
        "date": rng,
        "pair": pair,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })
    return df

def load_one_year(pairs=None, periods: int = 365, freq: str = "D"):
    if pairs is None:
        pairs = ["EURUSD"]
    frames = [
        _generate_series(pair, periods=periods, freq=freq) for pair in pairs
    ]
    data = pd.concat(frames, ignore_index=True)
    return data
