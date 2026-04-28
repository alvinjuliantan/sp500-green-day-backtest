"""Convert backtest CSV outputs to static JSON for the Next.js dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = ROOT / "public" / "data"

FILES = {
    "rolling_1yr_summary.csv": "rolling_1yr_summary.json",
    "rolling_1yr_windows.csv": "rolling_1yr_windows.json",
    "full_period_summary.csv": "full_period_summary.json",
    "buy_and_hold_comparison.csv": "buy_and_hold_comparison.json",
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for csv_name, json_name in FILES.items():
        csv_path = RESULTS_DIR / csv_name
        if not csv_path.exists():
            raise FileNotFoundError(f"Required CSV not found: {csv_path}")

        df = pd.read_csv(csv_path)
        records = df.where(pd.notnull(df), None).to_dict(orient="records")

        out_path = OUTPUT_DIR / json_name
        out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        print(f"Wrote {out_path.relative_to(ROOT)} ({len(records)} rows)")


if __name__ == "__main__":
    main()
