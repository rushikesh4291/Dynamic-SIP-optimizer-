"""Simple SIP demo using the FIFO portfolio on a single price series.

This is intentionally lightweight so it can run directly on the uploaded NIFTY
CSV (`finance.csv` by default). It tops up cash by the SIP amount each period,
buys units, optionally liquidates at the end, and reports summary metrics.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.backtester import Portfolio
from src.metrics import summarize_metrics


def load_prices(path: Path) -> pd.Series:
    df = pd.read_csv(path)
    date_col = "date" if "date" in df.columns else df.columns[0]
    price_col = "close" if "close" in df.columns else df.columns[-1]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col)
    prices = pd.to_numeric(df[price_col].astype(str).str.replace(",", ""), errors="coerce")
    series = pd.Series(prices.values, index=pd.to_datetime(df[date_col]), name="close")
    return series.dropna()


def run_sip(series: pd.Series, sip_amount: float, sell_all: bool) -> Portfolio:
    pf = Portfolio(["NIFTY"], cash=0.0)
    equity = []
    for dt, price in series.items():
        pf.cash += sip_amount
        pf.buy(dt, "NIFTY", sip_amount, float(price))
        equity.append(pf.total_value(dt, pd.Series({"NIFTY": float(price)})))

    if sell_all and not series.empty:
        last_date = series.index[-1]
        last_nav = float(series.iloc[-1])
        units = pf.position_units("NIFTY")
        pf.sell(last_date, "NIFTY", units, last_nav, verbose=True)

    equity_curve = pd.Series(equity, index=series.index)
    metrics = summarize_metrics(equity_curve)

    print("\nSIP summary")
    print(f"Periods: {len(series)}")
    print(f"Total invested: {sip_amount * len(series):,.2f}")
    print(f"Units held: {pf.position_units('NIFTY'):.2f}")
    if sell_all:
        print(f"Cash after liquidation: {pf.cash:,.2f}")
    print("Metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v:.4f}" if pd.notnull(v) else f"  {k}: nan")

    if pf.trade_log and pf.trade_log[-1].fifo_log:
        print("\nFIFO depletion log from final sale:")
        for line in pf.trade_log[-1].fifo_log:
            print(" -", line)

    return pf


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a simple NIFTY SIP demo using finance.csv")
    parser.add_argument("--nav-csv", type=Path, default=Path("finance.csv"), help="Path to price CSV with date + close columns")
    parser.add_argument("--sip", type=float, default=1000.0, help="Amount invested each period")
    parser.add_argument("--sell-all", action="store_true", help="Liquidate all units at the final date to show FIFO logs")
    args = parser.parse_args()

    series = load_prices(args.nav_csv)
    if series.empty:
        raise SystemExit("Price series is empty after parsing. Check the CSV format.")

    run_sip(series, args.sip, args.sell_all)


if __name__ == "__main__":
    main()
