"""Synthetic data generators for tests/demo."""
import pandas as pd
import numpy as np
from datetime import datetime

def generate_synthetic_data(days: int = 365, pair: str = "EURUSD"):
    rng = pd.date_range(end=datetime.today(), periods=days, freq="D")
    price = 1.0 + np.cumsum(np.random.normal(0.0, 0.5, size=days))
    df = pd.DataFrame({
        "date": rng,
        "pair": pair,
        "open": price,
        "high": price * (1 + np.random.rand(days) * 0.01),
        "low": price * (1 - np.random.rand(days) * 0.01),
        "close": price * (1 + (np.random.rand(days) - 0.5) * 0.01),
        "volume": np.random.randint(1000, 10000, size=days),
    })
    return df
