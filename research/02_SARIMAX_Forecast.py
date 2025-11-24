"""Lightweight SARIMAX research script.

It runs a Box-Jenkins style analysis on a single price series, fits a SARIMAX
model, and visualizes why the approach was not productionized (forecast error
is reported explicitly).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.statespace.sarimax import SARIMAX


def load_series(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    close_col = "close" if "close" in df.columns else df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    series = pd.to_numeric(df[close_col].str.replace(",", ""), errors="coerce") if df[close_col].dtype == object else df[close_col]
    return pd.Series(series.values, index=pd.to_datetime(df[date_col]), name="close").dropna()


def run_adf(series: pd.Series) -> dict:
    stat, pvalue, _, _, crit, _ = adfuller(series)
    return {"statistic": stat, "pvalue": pvalue, "crit": crit}


def main(data_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    series = load_series(data_path)
    print(f"Loaded {len(series)} observations from {data_path}")

    adf = run_adf(series)
    print(f"ADF statistic={adf['statistic']:.3f}, p-value={adf['pvalue']:.4f}")
    print(f"Critical values: {adf['crit']}")

    fig, axes = plt.subplots(3, 1, figsize=(8, 10))
    axes[0].plot(series.index, series.values)
    axes[0].set_title("Price series")
    plot_acf(series.dropna(), ax=axes[1], lags=20)
    plot_pacf(series.dropna(), ax=axes[2], lags=20)
    fig.tight_layout()
    fig_path = output_dir / "acf_pacf.png"
    fig.savefig(fig_path)
    plt.close(fig)

    model = SARIMAX(series, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0))
    fit = model.fit(disp=False)
    print(fit.summary())

    horizon = min(30, len(series) // 5)
    forecast = fit.get_forecast(steps=horizon)
    pred = forecast.predicted_mean
    actual = series.iloc[-horizon:]
    aligned = pd.concat([actual, pred], axis=1)
    aligned.columns = ["actual", "predicted"]
    mape = (np.abs(aligned["actual"] - aligned["predicted"]) / aligned["actual"]).mean() * 100
    print(f"MAPE over last {horizon} points: {mape:.2f}% -> too high to deploy")

    fig2, ax2 = plt.subplots(figsize=(10, 5))
    ax2.plot(aligned.index, aligned["actual"], label="Actual")
    ax2.plot(aligned.index, aligned["predicted"], label="Predicted", linestyle="--")
    ax2.set_title("SARIMAX forecast (research only)")
    ax2.legend()
    ax2.grid(True)
    fig2.tight_layout()
    pred_path = output_dir / "sarimax_pred_vs_actual.png"
    fig2.savefig(pred_path)
    plt.close(fig2)

    print(f"Saved diagnostics to {fig_path} and {pred_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run SARIMAX research forecast")
    parser.add_argument("--data", type=Path, default=Path("finance.csv"))
    parser.add_argument("--output", type=Path, default=Path("research/out"))
    args = parser.parse_args()
    main(args.data, args.output)
