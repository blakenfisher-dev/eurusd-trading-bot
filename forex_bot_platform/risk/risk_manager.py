"""Simple risk management scaffolding."""
import math

def is_jpy_pair(pair: str) -> bool:
    return "JPY" in pair

def pip_size_for_pair(pair: str) -> float:
    return 0.01 if is_jpy_pair(pair) else 0.0001

def calculate_position_size(pair: str, account_balance: float, risk_per_trade: float, stop_loss_pips: float,
                           max_position_size: int | None = None, max_exposure_per_currency: float | None = None) -> int:
    """Compute the number of units to trade for a given pair using risk-based sizing.

    - account_balance: available account balance in USD (approximate)
    - risk_per_trade: fraction of balance to risk (e.g., 0.01 for 1%)
    - stop_loss_pips: distance to stop loss in pips
    - max_position_size: hard cap on units
    - max_exposure_per_currency: soft cap on exposure in USD
    Returns integer units; 0 means no position.
    """
    if account_balance <= 0:
        return 0
    pip = pip_size_for_pair(pair)
    distance = (stop_loss_pips or 50) * pip
    if distance <= 0:
        distance = pip
    risk_amount = account_balance * (risk_per_trade or 0.0)
    units = int(risk_amount / distance)
    if max_position_size is not None:
        units = min(units, int(max_position_size))
    # Soft max exposure per currency (basic safeguard)
    if max_exposure_per_currency is not None and units > 0:
        exposure = units * (1.0)  # coarse exposure proxy; real exposure depends on price
        if exposure > max_exposure_per_currency:
            units = int(max_exposure_per_currency / max(1.0, exposure))
    return max(0, units)
