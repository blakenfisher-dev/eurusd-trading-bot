"""Data quality checks for backtests."""
import pandas as pd

SUPPORTED_TIMEFRAMES = {"1m", "5m", "15m", "1h", "1d", "1w"}

def validate_data(data: pd.DataFrame, timeframe: str | None = None) -> dict:
    warnings = []
    details = {}
    if data is None or data.empty:
        warnings.append("missing_data")
        details['missing'] = True
        return {"warnings": warnings, "details": details}
    if 'date' not in data.columns:
        warnings.append("missing_date_column")
        details['missing_date'] = True
    # Detect duplicates in date column
    if 'date' in data.columns and data['date'].duplicated().any():
        warnings.append("duplicate_timestamps")
        details['duplicates'] = True
    # Simple gap check for daily data
    if 'date' in data.columns:
        sorted_dates = data['date'].sort_values()
        diffs = sorted_dates.diff().dt.days.dropna()
        if (diffs > 1).any():
            warnings.append("missing_candles")
            details['gaps'] = bool((diffs > 1).any())
    # Validate OHLC values
    for col in ["open", "high", "low", "close"]:
        if col in data.columns:
            vals = data[col]
            if not pd.api.types.is_numeric_dtype(vals):
                warnings.append(f"invalid_{col}")
            else:
                if vals.isna().any():
                    warnings.append(f"missing_{col}")
                if (vals < 0).any():
                    warnings.append(f"negative_{col}")
    # Timeframe support check (optional)
    if timeframe is not None and timeframe not in SUPPORTED_TIMEFRAMES:
        warnings.append("unsupported_timeframe")
        details['unsupported_timeframe'] = timeframe
    return {"warnings": warnings, "details": details}
