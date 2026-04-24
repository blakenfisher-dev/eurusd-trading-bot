import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List


class DataGenerator:
    @staticmethod
    def generate_synthetic_ohlc(
        start_date: datetime,
        periods: int,
        timeframe_hours: int = 1,
        base_price: float = 1.1000,
        volatility: float = 0.0005,
        trend: float = 0.0,
        noise_level: float = 0.3
    ) -> pd.DataFrame:
        
        np.random.seed(42)
        
        timestamps = [start_date + timedelta(hours=i * timeframe_hours) for i in range(periods)]
        
        close_prices = [base_price]
        for i in range(1, periods):
            random_walk = np.random.randn() * volatility * noise_level
            trend_component = trend * volatility
            price_change = random_walk + trend_component
            new_price = close_prices[-1] * (1 + price_change)
            close_prices.append(new_price)
        
        data = []
        for i, ts in enumerate(timestamps):
            close = close_prices[i]
            
            intrabar_volatility = np.random.uniform(0.3, 1.0) * volatility
            
            high_offset = np.random.uniform(0, 1) * intrabar_volatility * close
            low_offset = np.random.uniform(0, 1) * intrabar_volatility * close
            
            high = close + high_offset
            low = close - low_offset
            
            open_price = close + np.random.uniform(-0.5, 0.5) * intrabar_volatility * close
            open_price = min(open_price, high)
            open_price = max(open_price, low)
            
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'timestamp': ts,
                'open': round(open_price, 5),
                'high': round(high, 5),
                'low': round(low, 5),
                'close': round(close, 5),
                'volume': volume
            })
        
        df = pd.DataFrame(data)
        return df

    @staticmethod
    def add_trend_events(df: pd.DataFrame, 
                         num_events: int = 10,
                         event_strength: float = 0.002) -> pd.DataFrame:
        
        np.random.seed(42)
        
        for _ in range(num_events):
            event_idx = np.random.randint(20, len(df) - 20)
            direction = np.random.choice([1, -1])
            
            for i in range(event_idx, min(event_idx + 20, len(df))):
                trend_contribution = direction * event_strength * (1 - (i - event_idx) / 20)
                df.iloc[i, df.columns.get_loc('close')] *= (1 + trend_contribution)
                
                df.iloc[i, df.columns.get_loc('high')] = max(df.iloc[i]['high'], df.iloc[i]['close'])
                df.iloc[i, df.columns.get_loc('low')] = min(df.iloc[i]['low'], df.iloc[i]['close'])
        
        return df

    @staticmethod
    def add_volatility_clusters(df: pd.DataFrame,
                                num_clusters: int = 5,
                                cluster_duration: int = 50) -> pd.DataFrame:
        
        np.random.seed(42)
        
        for _ in range(num_clusters):
            cluster_start = np.random.randint(30, len(df) - cluster_duration)
            volatility_multiplier = np.random.uniform(2, 4)
            
            for i in range(cluster_start, min(cluster_start + cluster_duration, len(df))):
                current_volatility = df.iloc[i]['high'] - df.iloc[i]['low']
                new_range = current_volatility * volatility_multiplier
                
                close = df.iloc[i]['close']
                df.iloc[i, df.columns.get_loc('high')] = close + new_range / 2
                df.iloc[i, df.columns.get_loc('low')] = close - new_range / 2
        
        return df


class DataDownloader:
    @staticmethod
    def download_from_investing(start_date: str, end_date: str, symbol: str = "EURUSD") -> Optional[pd.DataFrame]:
        try:
            import requests
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            return None
            
        except Exception as e:
            print(f"Failed to download data: {e}")
            return None
    
    @staticmethod
    def download_from_yahoo(start_date: str, end_date: str, symbol: str = "EURUSD=X") -> Optional[pd.DataFrame]:
        try:
            import yfinance
            
            ticker = yfinance.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date)
            
            if df.empty:
                return None
            
            df = df.reset_index()
            df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            
            return df
            
        except Exception as e:
            print(f"Failed to download data: {e}")
            return None


def load_historical_data(source: str = "synthetic",
                         **kwargs) -> pd.DataFrame:
    
    if source == "synthetic":
        start = kwargs.get('start_date', datetime(2024, 1, 1))
        periods = kwargs.get('periods', 5000)
        
        df = DataGenerator.generate_synthetic_ohlc(
            start_date=start,
            periods=periods,
            timeframe_hours=kwargs.get('timeframe', 1),
            base_price=kwargs.get('base_price', 1.1000),
            volatility=kwargs.get('volatility', 0.0005),
            trend=kwargs.get('trend', 0.0),
            noise_level=kwargs.get('noise', 0.5)
        )
        
        if kwargs.get('add_trends', True):
            df = DataGenerator.add_trend_events(df)
        
        if kwargs.get('add_clusters', True):
            df = DataGenerator.add_volatility_clusters(df)
        
        return df
    
    elif source == "investing":
        return DataDownloader.download_from_investing(**kwargs)
    
    elif source == "yahoo":
        return DataDownloader.download_from_yahoo(**kwargs)
    
    else:
        raise ValueError(f"Unknown source: {source}")