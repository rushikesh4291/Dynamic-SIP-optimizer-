"""Strategy utilities including VIX-gated weight adjustments."""
from __future__ import annotations

import pandas as pd

from .backtester import normalize_weights
from .data_engine import latest_vix


def regime_adjust_weights(
    target_weights: pd.Series,
    vix_history: pd.DataFrame,
    date: pd.Timestamp,
    *,
    vix_threshold: float = 25.0,
    risk_off_scale: float = 0.5,
) -> pd.Series:
    """Scale weights when India VIX breaches a threshold.

    The notebook previously gated allocations using realized portfolio
    volatility. This helper switches the logic to external India VIX data so
    the resume claim aligns with the implementation.
    """
    if vix_history.empty:
        return target_weights

    current_vix = latest_vix(vix_history, date)
    if current_vix > vix_threshold:
        scaled = target_weights * risk_off_scale
        return normalize_weights(scaled)
    return target_weights
