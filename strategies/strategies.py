import pandas as pd
import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from models import TradeDirection, TradingSignal, OHLC
from indicators import technical as ti


class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name
        self.signals: List[TradingSignal] = []

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, idx: int) -> Optional[TradingSignal]:
        pass

    def analyze(self, data: pd.DataFrame) -> List[TradingSignal]:
        signals = []
        for i in range(len(data)):
            signal = self.generate_signal(data, i)
            if signal:
                signals.append(signal)
        return signals


class TrendFollowerStrategy(BaseStrategy):
    def __init__(self, 
                 fast_ema: int = 9,
                 slow_ema: int = 21,
                 rsi_period: int = 14,
                 rsi_overbought: float = 70,
                 rsi_oversold: float = 30):
        super().__init__("TrendFollower")
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold

    def prepare_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['ema_fast'] = ti.ema(df['close'], self.fast_ema)
        df['ema_slow'] = ti.ema(df['close'], self.slow_ema)
        df['rsi'] = ti.rsi(df['close'], self.rsi_period)
        df['atr'] = ti.atr(df['high'], df['low'], df['close'])
        df['adx'], df['plus_di'], df['minus_di'] = ti.adx(df['high'], df['low'], df['close'])
        return df

    def generate_signal(self, data: pd.DataFrame, idx: int) -> Optional[TradingSignal]:
        if idx < max(self.slow_ema, self.rsi_period):
            return None

        row = data.iloc[idx]
        prev_row = data.iloc[idx - 1]

        ema_fast_prev = prev_row['ema_fast']
        ema_slow_prev = prev_row['ema_slow']
        ema_fast_curr = row['ema_fast']
        ema_slow_curr = row['ema_slow']
        rsi = row['rsi']
        adx = row['adx']

        if pd.isna(ema_fast_curr) or pd.isna(ema_slow_curr) or pd.isna(rsi) or pd.isna(adx):
            return None

        strength = 0.0
        signal_direction = TradeDirection.FLAT

        if ema_fast_prev < ema_slow_prev and ema_fast_curr > ema_slow_curr:
            if rsi < self.rsi_overbought and adx > 20:
                signal_direction = TradeDirection.LONG
                strength = min(1.0, adx / 50)
        elif ema_fast_prev > ema_slow_prev and ema_fast_curr < ema_slow_curr:
            if rsi > self.rsi_oversold and adx > 20:
                signal_direction = TradeDirection.SHORT
                strength = min(1.0, adx / 50)

        if signal_direction == TradeDirection.FLAT:
            return None

        atr = row['atr']
        entry_price = row['close']
        
        if signal_direction == TradeDirection.LONG:
            stop_loss = entry_price - (atr * 1.5)
            take_profit = entry_price + (atr * 2.5)
        else:
            stop_loss = entry_price + (atr * 1.5)
            take_profit = entry_price - (atr * 2.5)

        return TradingSignal(
            timestamp=row['timestamp'],
            direction=signal_direction,
            strength=strength,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=self.name
        )


class MeanReversionStrategy(BaseStrategy):
    def __init__(self,
                 bollinger_period: int = 20,
                 bollinger_std: float = 2.0,
                 rsi_period: int = 14,
                 rsi_upper: float = 70,
                 rsi_lower: float = 30,
                 confirmation_bars: int = 2):
        super().__init__("MeanReversion")
        self.bollinger_period = bollinger_period
        self.bollinger_std = bollinger_std
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.confirmation_bars = confirmation_bars

    def prepare_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = ti.bollinger_bands(
            df['close'], self.bollinger_period, self.bollinger_std
        )
        df['rsi'] = ti.rsi(df['close'], self.rsi_period)
        df['atr'] = ti.atr(df['high'], df['low'], df['close'])
        return df

    def generate_signal(self, data: pd.DataFrame, idx: int) -> Optional[TradingSignal]:
        if idx < self.bollinger_period + self.confirmation_bars:
            return None

        row = data.iloc[idx]
        
        if pd.isna(row['bb_upper']) or pd.isna(row['rsi']):
            return None

        signal_direction = TradeDirection.FLAT
        strength = 0.0

        if row['close'] < row['bb_lower']:
            if row['rsi'] < self.rsi_lower:
                signal_direction = TradeDirection.LONG
                strength = 0.7
        elif row['close'] > row['bb_upper']:
            if row['rsi'] > self.rsi_upper:
                signal_direction = TradeDirection.SHORT
                strength = 0.7

        if signal_direction == TradeDirection.FLAT:
            return None

        atr = row['atr']
        entry_price = row['close']
        
        if signal_direction == TradeDirection.LONG:
            stop_loss = entry_price - (atr * 1.5)
            take_profit = entry_price + (atr * 2.0)
        else:
            stop_loss = entry_price + (atr * 1.5)
            take_profit = entry_price - (atr * 2.0)

        return TradingSignal(
            timestamp=row['timestamp'],
            direction=signal_direction,
            strength=strength,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=self.name
        )


class BreakoutStrategy(BaseStrategy):
    def __init__(self,
                 lookback_period: int = 20,
                 atr_period: int = 14,
                 volume_confirm: bool = True,
                 volume_multiplier: float = 1.5):
        super().__init__("Breakout")
        self.lookback_period = lookback_period
        self.atr_period = atr_period
        self.volume_confirm = volume_confirm
        self.volume_multiplier = volume_multiplier

    def prepare_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['atr'] = ti.atr(df['high'], df['low'], df['close'], self.atr_period)
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        return df

    def generate_signal(self, data: pd.DataFrame, idx: int) -> Optional[TradingSignal]:
        if idx < self.lookback_period + 2:
            return None

        row = data.iloc[idx]
        prev_row = data.iloc[idx - 1]
        
        lookback_data = data.iloc[idx - self.lookback_period:idx]
        
        if pd.isna(row['atr']) or len(lookback_data) < self.lookback_period:
            return None

        resistance = lookback_data['high'].max()
        support = lookback_data['low'].min()
        
        signal_direction = TradeDirection.FLAT
        strength = 0.0
        
        prev_close = prev_row['close']
        curr_close = row['close']
        prev_high = prev_row['high']
        prev_low = prev_row['low']
        
        if self.volume_confirm:
            volume_ratio = row['volume'] / row['volume_sma'] if row['volume_sma'] > 0 else 1
            if volume_ratio < self.volume_multiplier:
                return None
            strength = min(1.0, volume_ratio / 2)

        if prev_close < resistance and curr_close > resistance:
            signal_direction = TradeDirection.LONG
            strength = max(strength, 0.8)
        elif prev_close > support and curr_close < support:
            signal_direction = TradeDirection.SHORT
            strength = max(strength, 0.8)

        if signal_direction == TradeDirection.FLAT:
            return None

        atr = row['atr']
        entry_price = row['close']
        
        if signal_direction == TradeDirection.LONG:
            stop_loss = support
            take_profit = entry_price + (entry_price - support) * 2
        else:
            stop_loss = resistance
            take_profit = entry_price - (resistance - entry_price) * 2

        return TradingSignal(
            timestamp=row['timestamp'],
            direction=signal_direction,
            strength=strength,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=self.name
        )


class SuperTrendStrategy(BaseStrategy):
    def __init__(self,
                 period: int = 10,
                 multiplier: float = 3.0,
                 confirmation_lookback: int = 2):
        super().__init__("SuperTrend")
        self.period = period
        self.multiplier = multiplier
        self.confirmation_lookback = confirmation_lookback

    def prepare_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['supertrend'], df['supertrend_dir'] = ti.supertrend(
            df['high'], df['low'], df['close'], self.period, self.multiplier
        )
        df['atr'] = ti.atr(df['high'], df['low'], df['close'])
        df['volume_sma'] = df['volume'].rolling(window=20).mean()
        return df

    def generate_signal(self, data: pd.DataFrame, idx: int) -> Optional[TradingSignal]:
        if idx < self.period + 2:
            return None

        row = data.iloc[idx]
        prev_rows = data.iloc[idx - self.confirmation_lookback:idx]

        if pd.isna(row['supertrend']) or pd.isna(row['supertrend_dir']):
            return None

        current_dir = row['supertrend_dir']
        
        dirs_same = prev_rows['supertrend_dir'].nunique() == 1
        dirs_all_same = dirs_same and (prev_rows['supertrend_dir'].iloc[0] == current_dir)

        if not dirs_all_same:
            return None

        signal_direction = TradeDirection.FLAT
        strength = 0.7

        if current_dir == 1:
            signal_direction = TradeDirection.LONG
        elif current_dir == -1:
            signal_direction = TradeDirection.SHORT

        atr = row['atr']
        entry_price = row['close']

        if signal_direction == TradeDirection.LONG:
            stop_loss = row['supertrend']
            take_profit = entry_price + (atr * 2.5)
        else:
            stop_loss = row['supertrend']
            take_profit = entry_price - (atr * 2.5)

        return TradingSignal(
            timestamp=row['timestamp'],
            direction=signal_direction,
            strength=strength,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=self.name
        )


class MultiTimeframeStrategy(BaseStrategy):
    def __init__(self,
                 trend_period: int = 50,
                 entry_period: int = 15,
                 confirmation_period: int = 5):
        super().__init__("MultiTimeframe")
        self.trend_period = trend_period
        self.entry_period = entry_period
        self.confirmation_period = confirmation_period

    def prepare_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['trend_ema'] = ti.ema(df['close'], self.trend_period)
        df['entry_ema'] = ti.ema(df['close'], self.entry_period)
        df['fast_ema'] = ti.ema(df['close'], self.confirmation_period)
        df['rsi'] = ti.rsi(df['close'], 14)
        df['atr'] = ti.atr(df['high'], df['low'], df['close'])
        return df

    def generate_signal(self, data: pd.DataFrame, idx: int) -> Optional[TradingSignal]:
        if idx < max(self.trend_period, self.entry_period):
            return None

        row = data.iloc[idx]

        if pd.isna(row['trend_ema']) or pd.isna(row['entry_ema']) or pd.isna(row['rsi']):
            return None

        trend_above = row['close'] > row['trend_ema']
        entry_above_trend = row['entry_ema'] > row['trend_ema']
        
        signal_direction = TradeDirection.FLAT
        strength = 0.0

        golden_cross = row['fast_ema'] > row['entry_ema'] and data.iloc[idx-1]['fast_ema'] <= data.iloc[idx-1]['entry_ema']
        death_cross = row['fast_ema'] < row['entry_ema'] and data.iloc[idx-1]['fast_ema'] >= data.iloc[idx-1]['entry_ema']

        if trend_above and entry_above_trend and golden_cross:
            if 40 < row['rsi'] < 60:
                signal_direction = TradeDirection.LONG
                strength = 0.85
        elif not trend_above and not entry_above_trend and death_cross:
            if 40 < row['rsi'] < 60:
                signal_direction = TradeDirection.SHORT
                strength = 0.85

        if signal_direction == TradeDirection.FLAT:
            return None

        atr = row['atr']
        entry_price = row['close']
        
        if signal_direction == TradeDirection.LONG:
            stop_loss = entry_price - (atr * 2)
            take_profit = entry_price + (atr * 3)
        else:
            stop_loss = entry_price + (atr * 2)
            take_profit = entry_price - (atr * 3)

        return TradingSignal(
            timestamp=row['timestamp'],
            direction=signal_direction,
            strength=strength,
            price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            strategy=self.name
        )


class ComboStrategy:
    def __init__(self, strategies: List[BaseStrategy], min_agreement: int = 2):
        self.strategies = strategies
        self.min_agreement = min_agreement
        self.name = "Combo"

    def prepare_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        for strategy in self.strategies:
            df = strategy.prepare_indicators(df)
        return df

    def analyze(self, data: pd.DataFrame) -> List[TradingSignal]:
        for strategy in self.strategies:
            strategy.prepare_indicators(data)

        signals = []
        for idx in range(len(data)):
            votes = []
            for strategy in self.strategies:
                signal = strategy.generate_signal(data, idx)
                if signal and signal.strength >= 0.6:
                    votes.append(signal)

            if len(votes) >= self.min_agreement:
                direction_votes = [v.direction for v in votes]
                long_count = direction_votes.count(TradeDirection.LONG)
                short_count = direction_votes.count(TradeDirection.SHORT)

                if long_count >= self.min_agreement:
                    avg_strength = sum(v.strength for v in votes if v.direction == TradeDirection.LONG) / long_count
                    final_signal = votes[0].__class__(
                        timestamp=votes[0].timestamp,
                        direction=TradeDirection.LONG,
                        strength=avg_strength,
                        price=votes[0].price,
                        stop_loss=votes[0].stop_loss,
                        take_profit=votes[0].take_profit,
                        strategy=self.name
                    )
                    signals.append(final_signal)
                elif short_count >= self.min_agreement:
                    avg_strength = sum(v.strength for v in votes if v.direction == TradeDirection.SHORT) / short_count
                    final_signal = votes[0].__class__(
                        timestamp=votes[0].timestamp,
                        direction=TradeDirection.SHORT,
                        strength=avg_strength,
                        price=votes[0].price,
                        stop_loss=votes[0].stop_loss,
                        take_profit=votes[0].take_profit,
                        strategy=self.name
                    )
                    signals.append(final_signal)

        return signals