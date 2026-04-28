"""Convert backtest CSV outputs to static JSON for the Next.js dashboard."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
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


def sanitize_json_value(value):
    """Convert unsupported JSON numeric values (NaN/Infinity) to None."""
    if isinstance(value, (np.floating, float)):
        if not math.isfinite(float(value)):
            return None
        return float(value)

    if isinstance(value, (np.integer, int)):
        return int(value)

    if isinstance(value, (np.bool_, bool)):
        return bool(value)

    return value


def sanitize_records(df: pd.DataFrame) -> list[dict]:
    clean_df = df.replace([np.inf, -np.inf], np.nan)
    records = clean_df.where(pd.notnull(clean_df), None).to_dict(orient="records")
    return [
        {key: sanitize_json_value(value) for key, value in row.items()}
        for row in records
    ]


def expectancy_from_pf(
    avg_net: float | None,
    win_rate: float | None,
    profit_factor: float | None,
) -> tuple[float | None, float | None]:
    if avg_net is None or win_rate is None or profit_factor is None:
        return None, None

    loss_rate = 1 - win_rate
    if win_rate <= 0 or loss_rate <= 0 or abs(profit_factor - 1) < 1e-12:
        return None, None

    avg_loss_abs = avg_net / (loss_rate * (profit_factor - 1))
    avg_win = (profit_factor * loss_rate * avg_loss_abs) / win_rate
    avg_loss = -abs(avg_loss_abs)
    return avg_win, avg_loss


def enrich_rolling_windows(df: pd.DataFrame) -> pd.DataFrame:
    if {"net_profit", "number_of_trades"}.issubset(df.columns):
        df["expected_profit_per_trade"] = (
            df["net_profit"] / df["number_of_trades"].replace({0: np.nan})
        )
    else:
        df["expected_profit_per_trade"] = np.nan

    if "average_net_profit_per_trade" not in df.columns:
        df["average_net_profit_per_trade"] = df["expected_profit_per_trade"]

    df["expected_return_per_trade_pct"] = df["expected_profit_per_trade"] / 100.0

    avg_wins: list[float | None] = []
    avg_losses: list[float | None] = []
    for _, row in df.iterrows():
        average_win, average_loss = expectancy_from_pf(
            avg_net=row.get("expected_profit_per_trade"),
            win_rate=row.get("win_rate"),
            profit_factor=row.get("profit_factor"),
        )
        avg_wins.append(average_win)
        avg_losses.append(average_loss)

    df["average_win"] = avg_wins
    df["average_loss"] = avg_losses
    df["payoff_ratio"] = df["average_win"] / df["average_loss"].abs()
    return df


def enrich_full_period(df: pd.DataFrame) -> pd.DataFrame:
    df["expected_profit_per_trade"] = (
        df["net_profit"] / df["number_of_trades"].replace({0: np.nan})
    )
    if "average_net_profit_per_trade" not in df.columns:
        df["average_net_profit_per_trade"] = df["expected_profit_per_trade"]
    df["expected_return_per_trade_pct"] = df["expected_profit_per_trade"] / 100.0

    avg_wins = []
    avg_losses = []

    for _, row in df.iterrows():
        strategy = row.get("strategy")
        trades_path = RESULTS_DIR / f"trades_{strategy}.csv"
        if trades_path.exists():
            trades = pd.read_csv(trades_path)
            wins = trades.loc[trades["net_profit"] > 0, "net_profit"]
            losses = trades.loc[trades["net_profit"] < 0, "net_profit"]
            avg_wins.append(wins.mean() if not wins.empty else np.nan)
            avg_losses.append(losses.mean() if not losses.empty else np.nan)
        else:
            average_win, average_loss = expectancy_from_pf(
                avg_net=row.get("expected_profit_per_trade"),
                win_rate=row.get("win_rate"),
                profit_factor=row.get("profit_factor"),
            )
            avg_wins.append(average_win)
            avg_losses.append(average_loss)

    df["average_win"] = avg_wins
    df["average_loss"] = avg_losses
    df["payoff_ratio"] = df["average_win"] / df["average_loss"].abs()
    return df


def enrich_rolling_summary(summary_df: pd.DataFrame, windows_df: pd.DataFrame) -> pd.DataFrame:
    expectancy_summary = (
        windows_df.groupby("strategy", dropna=False)
        .agg(
            expected_profit_per_trade=("expected_profit_per_trade", "mean"),
            expected_return_per_trade_pct=("expected_return_per_trade_pct", "mean"),
            average_win=("average_win", "mean"),
            average_loss=("average_loss", "mean"),
            payoff_ratio=("payoff_ratio", "mean"),
        )
        .reset_index()
    )
    return summary_df.merge(expectancy_summary, on="strategy", how="left")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    loaded_frames: dict[str, pd.DataFrame] = {}
    for csv_name in FILES:
        csv_path = RESULTS_DIR / csv_name
        if not csv_path.exists():
            raise FileNotFoundError(f"Required CSV not found: {csv_path}")
        loaded_frames[csv_name] = pd.read_csv(csv_path)

    loaded_frames["rolling_1yr_windows.csv"] = enrich_rolling_windows(
        loaded_frames["rolling_1yr_windows.csv"].copy()
    )
    loaded_frames["full_period_summary.csv"] = enrich_full_period(
        loaded_frames["full_period_summary.csv"].copy()
    )
    loaded_frames["rolling_1yr_summary.csv"] = enrich_rolling_summary(
        loaded_frames["rolling_1yr_summary.csv"].copy(),
        loaded_frames["rolling_1yr_windows.csv"],
    )

    for csv_name, json_name in FILES.items():
        df = loaded_frames[csv_name]
        records = sanitize_records(df)
        out_path = OUTPUT_DIR / json_name
        out_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
        print(f"Wrote {out_path.relative_to(ROOT)} ({len(records)} rows)")


if __name__ == "__main__":
    main()
