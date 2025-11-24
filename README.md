# Dynamic SIP Optimizer

A modular version of the SIP backtester showcased in the notebook. The repo
separates research artifacts (SARIMAX experiment, HRP ideas) from the production
FIFO + exit-load engine so interviewers can see a clean, defensible story.

## Layout
- `src/backtester.py` – FIFO lot engine with exit loads, STT, txn costs, and optional verbose logs for walkthroughs.
- `src/metrics.py` – CAGR, Sharpe, Sortino, CVaR, and helper metrics.
- `src/strategies.py` – India VIX–gated weight adjustment to align with the resume claim.
- `src/data_engine.py` – Loader for external India VIX CSVs.
- `research/02_SARIMAX_Forecast.py` – Box-Jenkins + SARIMAX research script showing why forecasting was shelved.
- `tests/test_fifo_logic.py` – Unit test proving FIFO drains lots in order and records logs.

## Running the SARIMAX research script
```
python research/02_SARIMAX_Forecast.py --data finance.csv --output research/out
```
The script prints ADF results, SARIMAX summary AIC/BIC, forecast error, and
stores diagnostic plots in the output folder. It is intentionally scoped to a
single fund/series to keep forecasting experiments separate from the live
backtester.

## Quick readiness check
If you're unsure whether dependencies are installed or the CSVs are in place,
run:
```
python check_env.py
```
Missing packages and expected file locations will be reported.

## Simple NIFTY SIP demo (works with the uploaded finance.csv)
```
python main.py --nav-csv finance.csv --sip 1000 --sell-all
```
This tops up ₹1,000 each period, buys NIFTY units via the FIFO engine, liquidates
at the end to show the FIFO depletion log, and prints CAGR/Sharpe/Sortino/
drawdown metrics. Use this as a sanity check that the engine works with your
NIFTY data.

## VIX gating example
```
import pandas as pd
from src.strategies import regime_adjust_weights
from src.data_engine import load_india_vix_csv

vix = load_india_vix_csv("data/india_vix_sample.csv")
weights = pd.Series({"FundA": 0.5, "FundB": 0.5})
adjusted = regime_adjust_weights(weights, vix, pd.Timestamp("2023-10-10"), vix_threshold=25)
```

## FIFO debug walk-through
Pass `verbose=True` into `Portfolio.sell` to capture per-lot depletion logs that
mirror the notebook's `_apply_costs_on_sell` reasoning and make the exit-load
math transparent during interviews.

## How to validate the repo quickly
See `TESTING.md` for a full step-by-step checklist (venv setup, dependency
verification, unit test, SIP smoke test with your NIFTY CSV, VIX gating demo,
and SARIMAX research run). The short version:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # or install wheels if you're offline
python check_env.py
pytest -q
python main.py --nav-csv finance.csv --sip 1000 --sell-all --verbose-sell
```
