# How to validate the Dynamic SIP Optimizer

Follow this checklist to prove the code runs end-to-end with your uploaded NIFTY data (`finance.csv`).

## 1) Create an isolated environment
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```
> If you are offline or behind a proxy, install wheels manually (e.g., `pip install pandas‑*.whl numpy‑*.whl matplotlib‑*.whl statsmodels‑*.whl scipy‑*.whl`) or mirror PyPI inside your network.

## 2) Sanity-check dependencies and data
```bash
python check_env.py
```
You should see all required packages marked **OK** and the expected CSVs listed (e.g., `finance.csv`, `data/india_vix_sample.csv`).

## 3) Run the unit test for FIFO logging
```bash
pytest -q
```
Expected: `1 passed` (it was previously skipped only when `pandas` was missing). This asserts that sells drain older lots first, record exit-load costs, and attach the verbose FIFO log.

## 4) Smoke-test the SIP engine on NIFTY data
```bash
python main.py --nav-csv finance.csv --sip 1000 --sell-all --verbose-sell
```
What you should see:
- Periodic buys until the end of `finance.csv`.
- A final sell log showing lots consumed in order (timestamps should match the earliest buys first).
- Portfolio metrics (CAGR, Sharpe, Sortino, max drawdown) printed at the end.

## 5) Verify VIX gating logic
If you want to confirm the India VIX wiring with the sample CSV:
```bash
python - <<'PY'
import pandas as pd
from src.strategies import regime_adjust_weights
from src.data_engine import load_india_vix_csv

vix = load_india_vix_csv("data/india_vix_sample.csv")
weights = pd.Series({"FundA": 0.5, "FundB": 0.5})
adjusted = regime_adjust_weights(weights, vix, pd.Timestamp("2020-03-18"), vix_threshold=25)
print("Original weights:\n", weights)
print("Adjusted weights:\n", adjusted)
PY
```
You should see the weights scaled down on the chosen high-VIX date and unchanged on calmer dates if you change the timestamp.

## 6) Run the SARIMAX research script (optional)
```bash
python research/02_SARIMAX_Forecast.py --data finance.csv --output research/out
```
Expected artifacts inside `research/out`:
- `adf_result.txt` (stationarity test)
- `acf_pacf.png`
- `pred_vs_actual.png` (to visualize forecast error)
- Console output will show AIC/BIC and MAPE so you can explain why SARIMAX was not promoted to production.

## 7) When something fails
- Re-run `python check_env.py` to spot missing packages or file paths.
- Ensure your terminal/IDE is using the `.venv` interpreter you created.
- If proxies block installs, download wheels on a machine with internet and copy them over, then `pip install *.whl` locally.
