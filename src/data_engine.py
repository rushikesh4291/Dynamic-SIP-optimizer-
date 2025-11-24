"""Data ingestion helpers for NAV series and India VIX."""
from __future__ import annotations

from pathlib import Path
import pandas as pd


def load_india_vix_csv(path: str | Path) -> pd.DataFrame:
    """Load India VIX history from a CSV with columns [Date, Close]."""
    df = pd.read_csv(path)
    date_col = "Date" if "Date" in df.columns else df.columns[0]
    price_col = "Close" if "Close" in df.columns else df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df[[date_col, price_col]].rename(columns={date_col: "date", price_col: "vix"})
    df = df.dropna().sort_values("date").set_index("date")
    return df


def latest_vix(vix_df: pd.DataFrame, date: pd.Timestamp) -> float:
    """Return the most recent VIX value up to the given date."""
    return float(vix_df.loc[:date]["vix"].ffill().iloc[-1])
