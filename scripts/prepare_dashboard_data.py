"""Convert backtest CSV outputs to static JSON for the Next.js dashboard.

Adds expected return / expectancy metrics.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
OUTPUT_DIR = ROOT / "public" / "data"
TRADE_SIZE = 100.0


def safe_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except TypeError:
        pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


def write_json(df: pd.DataFrame, out_path: Path) -> None:
    df = df.where(pd.notnull(df), None)
    records = []
    for row in df.to_dict(orient="records"):
        records.append({k: safe_value(v) for k, v in row.items()})

    out_path.write_text(
        json.dumps(records, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"Wrote {out_path.relative_to(ROOT)} ({len(records)} rows)")


def trade_expectancy_metrics() -> dict[str, dict]:
    metrics: dict[str, dict] = {}

    for path in RESULTS_DIR.glob("trades_*.csv"):
        strategy = path.stem.replace("trades_", "")
        df = pd.read_csv(path)

        if df.empty or "net_profit" not in df.columns:
            continue

        wins = df[df["net_profit"] > 0]["net_profit"]
        losses = df[df["net_profit"] < 0]["net_profit"]

        expected_profit = df["net_profit"].mean()
        average_win = wins.mean() if len(wins) else None
        average_loss = losses.mean() if len(losses) else None

        payoff_ratio = None
        if average_win is not None and average_loss is not None and average_loss != 0:
            payoff_ratio = average_win / abs(average_loss)

        metrics[strategy] = {
            "expected_profit_per_trade": expected_profit,
            "expected_return_per_trade_pct": expected_profit / TRADE_SIZE,
            "average_win": average_win,
            "average_loss": average_loss,
            "payoff_ratio": payoff_ratio,
        }

    return metrics


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    metrics = trade_expectancy_metrics()

    rolling_windows = pd.read_csv(RESULTS_DIR / "rolling_1yr_windows.csv")
    if "average_net_profit_per_trade" in rolling_windows.columns:
        rolling_windows["expected_profit_per_trade"] = rolling_windows["average_net_profit_per_trade"]
    else:
        rolling_windows["expected_profit_per_trade"] = rolling_windows.apply(
            lambda r: r["net_profit"] / r["number_of_trades"] if r["number_of_trades"] else None,
            axis=1,
        )
    rolling_windows["expected_return_per_trade_pct"] = rolling_windows["expected_profit_per_trade"] / TRADE_SIZE

    rolling_summary = pd.read_csv(RESULTS_DIR / "rolling_1yr_summary.csv")

    grouped = (
        rolling_windows.groupby("strategy")
        .agg(
            expected_profit_per_trade=("expected_profit_per_trade", "mean"),
            expected_return_per_trade_pct=("expected_return_per_trade_pct", "mean"),
        )
        .reset_index()
    )

    rolling_summary = rolling_summary.merge(grouped, on="strategy", how="left")

    rolling_summary["average_win"] = rolling_summary["strategy"].map(
        lambda s: metrics.get(s, {}).get("average_win")
    )
    rolling_summary["average_loss"] = rolling_summary["strategy"].map(
        lambda s: metrics.get(s, {}).get("average_loss")
    )
    rolling_summary["payoff_ratio"] = rolling_summary["strategy"].map(
        lambda s: metrics.get(s, {}).get("payoff_ratio")
    )

    full_period = pd.read_csv(RESULTS_DIR / "full_period_summary.csv")

    full_period["expected_profit_per_trade"] = full_period.apply(
        lambda r: metrics.get(r["strategy"], {}).get("expected_profit_per_trade")
        if r["strategy"] in metrics
        else (r["net_profit"] / r["number_of_trades"] if r["number_of_trades"] else None),
        axis=1,
    )
    full_period["expected_return_per_trade_pct"] = full_period["expected_profit_per_trade"] / TRADE_SIZE
    full_period["average_win"] = full_period["strategy"].map(
        lambda s: metrics.get(s, {}).get("average_win")
    )
    full_period["average_loss"] = full_period["strategy"].map(
        lambda s: metrics.get(s, {}).get("average_loss")
    )
    full_period["payoff_ratio"] = full_period["strategy"].map(
        lambda s: metrics.get(s, {}).get("payoff_ratio")
    )

    buy_hold = pd.read_csv(RESULTS_DIR / "buy_and_hold_comparison.csv")

    write_json(rolling_summary, OUTPUT_DIR / "rolling_1yr_summary.json")
    write_json(rolling_windows, OUTPUT_DIR / "rolling_1yr_windows.json")
    write_json(full_period, OUTPUT_DIR / "full_period_summary.json")
    write_json(buy_hold, OUTPUT_DIR / "buy_and_hold_comparison.json")


if __name__ == "__main__":
    main()
