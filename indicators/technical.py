import numpy as np
import pandas as pd
from typing import Union


def sma(data: pd.Series, period: int) -> pd.Series:
    return data.rolling(window=period).mean()


def ema(data: pd.Series, period: int) -> pd.Series:
    return data.ewm(span=period, adjust=False).mean()


def rsi(data: pd.Series, period: int = 14) -> pd.Series:
    delta = data.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def bollinger_bands(data: pd.Series, period: int = 20, std_dev: float = 2.0):
    middle = sma(data, period)
    std = data.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower


def macd(data: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast = ema(data, fast)
    ema_slow = ema(data, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr


def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(window=d_period).mean()
    return k, d


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr_val = tr.rolling(window=period).mean()
    
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_val)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_val)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    
    return adx, plus_di, minus_di


def supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0):
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr_val = tr.rolling(window=period).mean()
    
    hl2 = (high + low) / 2
    upper = hl2 + (multiplier * atr_val)
    lower = hl2 - (multiplier * atr_val)
    
    supertrend = pd.Series(0, index=close.index)
    direction = pd.Series(1, index=close.index)
    
    for i in range(1, len(close)):
        if close.iloc[i] > upper.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]
            if direction.iloc[i] == 1 and lower.iloc[i] < lower.iloc[i-1]:
                lower.iloc[i] = lower.iloc[i-1]
            if direction.iloc[i] == -1 and upper.iloc[i] > upper.iloc[i-1]:
                upper.iloc[i] = upper.iloc[i-1]
        
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower.iloc[i]
        else:
            supertrend.iloc[i] = upper.iloc[i]
    
    return supertrend, direction


def volume_weighted_price(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20):
    typical_price = (high + low + close) / 3
    vp = typical_price * volume
    vwap = vp.rolling(window=period).sum() / volume.rolling(window=period).sum()
    return vwap


def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
             tenkan_period: int = 9, kijun_period: int = 26, senkou_b_period: int = 52):
    tenkan = (high.rolling(window=tenkan_period).max() + low.rolling(window=tenkan_period).min()) / 2
    kijun = (high.rolling(window=kijun_period).max() + low.rolling(window=kijun_period).min()) / 2
    senkou_a = (tenkan + kijun) / 2
    senkou_b = (high.rolling(window=senkou_b_period).max() + low.rolling(window=senkou_b_period).min()) / 2
    chikou = close.shift(-kijun_period)
    
    return tenkan, kijun, senkou_a, senkou_b, chikou


def fibonacci_retracement(high: float, low: float) -> dict:
    diff = high - low
    levels = {
        '0.0': low,
        '23.6': low + diff * 0.236,
        '38.2': low + diff * 0.382,
        '50.0': low + diff * 0.5,
        '61.8': low + diff * 0.618,
        '78.6': low + diff * 0.786,
        '100.0': high
    }
    return levels


def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20):
    typical_price = (high + low + close) / 3
    sma_tp = typical_price.rolling(window=period).mean()
    mean_deviation = typical_price.rolling(window=period).apply(lambda x: abs(x - x.mean()).mean())
    cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
    return cci


def vwap_bands(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series, period: int = 20):
    typical_price = (high + low + close) / 3
    vwap = (typical_price * volume).cumsum() / volume.cumsum()
    std = typical_price.rolling(window=period).std()
    return vwap + std, vwap, vwap - std