"""Performance metric helpers separated from the notebook."""
from __future__ import annotations

import math
import pandas as pd
import numpy as np


def daily_returns(prices: pd.Series) -> pd.Series:
    return prices.pct_change().fillna(0.0)


def cagr(equity: pd.Series) -> float:
    if equity.empty:
        return np.nan
    start_v, end_v = float(equity.iloc[0]), float(equity.iloc[-1])
    if start_v <= 0 or end_v <= 0:
        return np.nan
    days = (equity.index[-1] - equity.index[0]).days
    years = days / 365.25
    if years <= 0:
        return np.nan
    return (end_v / start_v) ** (1 / years) - 1


def max_drawdown(equity: pd.Series) -> float:
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    return dd.min()


def annualized_vol(returns: pd.Series, scale: int = 252) -> float:
    return returns.std(ddof=0) * math.sqrt(scale)


def sharpe(returns: pd.Series, rf: float = 0.0, scale: int = 252) -> float:
    excess = returns - rf
    std = excess.std(ddof=0)
    if std == 0:
        return np.nan
    return (excess.mean() / std) * math.sqrt(scale)


def sortino(returns: pd.Series, rf: float = 0.0, scale: int = 252) -> float:
    downside = returns[returns < rf] - rf
    denom = downside.pow(2).mean() ** 0.5
    if denom == 0 or np.isnan(denom):
        return np.nan
    return ((returns.mean() - rf) / denom) * math.sqrt(scale)


def cvar(returns: pd.Series, alpha: float = 0.95) -> float:
    if returns.empty:
        return np.nan
    cutoff = returns.quantile(1 - alpha)
    tail = returns[returns <= cutoff]
    if tail.empty:
        return np.nan
    return tail.mean()


def rolling_volatility(series: pd.Series, window: int) -> pd.Series:
    return series.pct_change().rolling(window).std(ddof=0) * np.sqrt(252)


def summarize_metrics(equity: pd.Series, rf_daily: float = 0.0) -> dict:
    rets = daily_returns(equity)
    return {
        "CAGR": cagr(equity),
        "AnnVol": annualized_vol(rets),
        "Sharpe": sharpe(rets, rf_daily),
        "Sortino": sortino(rets, rf_daily),
        "MaxDD": max_drawdown(equity),
        "CVaR95": cvar(rets, 0.95),
        "Days": (equity.index[-1] - equity.index[0]).days if not equity.empty else 0,
    }


def as_bps(x: float) -> float:
    return 1e4 * x if pd.notnull(x) else np.nan
