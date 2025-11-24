"""Lightweight environment + data readiness check.

Use this before running the SARIMAX research or SIP demo to confirm required
libraries are installed and input CSVs exist.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

REQUIRED = ["pandas", "numpy", "matplotlib", "statsmodels", "scipy"]

def main() -> None:
    missing = [m for m in REQUIRED if importlib.util.find_spec(m) is None]
    if missing:
        print("Missing packages: " + ", ".join(missing))
        print("Install with: pip install -r requirements.txt")
    else:
        print("All required packages are available.")

    finance = Path("finance.csv")
    if finance.exists():
        print(f"Found sample price data: {finance.resolve()}")
    else:
        print("finance.csv not found; place your NIFTY price CSV at repo root or pass --data to scripts.")

    vix = Path("data/india_vix_sample.csv")
    print("Found India VIX sample:" if vix.exists() else "India VIX sample missing:", vix.resolve())


if __name__ == "__main__":
    main()
