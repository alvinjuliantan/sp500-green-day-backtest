from pathlib import Path

# -----------------------------
# 1) Replace prepare_dashboard_data.py
# -----------------------------
prepare_path = Path("scripts/prepare_dashboard_data.py")

prepare_path.write_text('''"""Convert backtest CSV outputs to static JSON for the Next.js dashboard.

Also enriches strategy summaries with expected return / expectancy metrics.
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

FILES = {
    "rolling_1yr_summary.csv": "rolling_1yr_summary.json",
    "rolling_1yr_windows.csv": "rolling_1yr_windows.json",
    "full_period_summary.csv": "full_period_summary.json",
    "buy_and_hold_comparison.csv": "buy_and_hold_comparison.json",
}


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


def records_to_json(df: pd.DataFrame) -> list[dict]:
    df = df.where(pd.notnull(df), None)
    records = df.to_dict(orient="records")
    return [{k: safe_value(v) for k, v in row.items()} for row in records]


def load_trade_expectancy() -> dict[str, dict]:
    """Read results/trades_*.csv and calculate expectancy metrics per strategy."""
    metrics: dict[str, dict] = {}

    for path in RESULTS_DIR.glob("trades_*.csv"):
        strategy = path.stem.replace("trades_", "")
        df = pd.read_csv(path)

        if "net_profit" not in df.columns or df.empty:
            continue

        wins = df[df["net_profit"] > 0]["net_profit"]
        losses = df[df["net_profit"] < 0]["net_profit"]

        average_win = wins.mean() if len(wins) else None
        average_loss = losses.mean() if len(losses) else None
        payoff_ratio = None

        if average_win is not None and average_loss is not None and average_loss != 0:
            payoff_ratio = average_win / abs(average_loss)

        expected_profit_per_trade = df["net_profit"].mean()
        expected_return_per_trade_pct = expected_profit_per_trade / TRADE_SIZE

        metrics[strategy] = {
            "expected_profit_per_trade": expected_profit_per_trade,
            "expected_return_per_trade_pct": expected_return_per_trade_pct,
            "average_win": average_win,
            "average_loss": average_loss,
            "payoff_ratio": payoff_ratio,
        }

    return metrics


def enrich_full_period(df: pd.DataFrame, trade_metrics: dict[str, dict]) -> pd.DataFrame:
    df = df.copy()

    for col in [
        "expected_profit_per_trade",
        "expected_return_per_trade_pct",
        "average_win",
        "average_loss",
        "payoff_ratio",
    ]:
        if col not in df.columns:
            df[col] = None

    for idx, row in df.iterrows():
        strategy = row.get("strategy")
        metrics = trade_metrics.get(strategy, {})

        expected_profit = metrics.get("expected_profit_per_trade")

        if expected_profit is None:
            trades = row.get("number_of_trades")
            net_profit = row.get("net_profit")
            if pd.notna(trades) and pd.notna(net_profit) and trades:
                expected_profit = net_profit / trades

        df.at[idx, "expected_profit_per_trade"] = expected_profit
        df.at[idx, "expected_return_per_trade_pct"] = (
            expected_profit / TRADE_SIZE if expected_profit is not None else None
        )
        df.at[idx, "average_win"] = metrics.get("average_win")
        df.at[idx, "average_loss"] = metrics.get("average_loss")
        df.at[idx, "payoff_ratio"] = metrics.get("payoff_ratio")

    return df


def enrich_rolling_windows(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "average_net_profit_per_trade" in df.columns:
        df["expected_profit_per_trade"] = df["average_net_profit_per_trade"]
    else:
        df["expected_profit_per_trade"] = df.apply(
            lambda r: r["net_profit"] / r["number_of_trades"]
            if r.get("number_of_trades", 0) else None,
            axis=1,
        )

    df["expected_return_per_trade_pct"] = df["expected_profit_per_trade"] / TRADE_SIZE
    return df


def enrich_rolling_summary(
    summary_df: pd.DataFrame,
    windows_df: pd.DataFrame,
    trade_metrics: dict[str, dict],
) -> pd.DataFrame:
    summary_df = summary_df.copy()

    if not windows_df.empty:
        grouped = windows_df.groupby("strategy").agg(
            expected_profit_per_trade=("expected_profit_per_trade", "mean"),
            expected_return_per_trade_pct=("expected_return_per_trade_pct", "mean"),
        ).reset_index()

        summary_df = summary_df.merge(grouped, on="strategy", how="left")

    for col in ["average_win", "average_loss", "payoff_ratio"]:
        if col not in summary_df.columns:
            summary_df[col] = None

    for idx, row in summary_df.iterrows():
        strategy = row.get("strategy")
        metrics = trade_metrics.get(strategy, {})

        for col in ["average_win", "average_loss", "payoff_ratio"]:
            summary_df.at[idx, col] = metrics.get(col)

        if pd.isna(summary_df.at[idx, "expected_profit_per_trade"]):
            avg_profit = row.get("average_1yr_net_profit")
            avg_trades = row.get("average_trades_per_year")
            if pd.notna(avg_profit) and pd.notna(avg_trades) and avg_trades:
                summary_df.at[idx, "expected_profit_per_trade"] = avg_profit / avg_trades
                summary_df.at[idx, "expected_return_per_trade_pct"] = (
                    summary_df.at[idx, "expected_profit_per_trade"] / TRADE_SIZE
                )

    return summary_df


def write_json(df: pd.DataFrame, out_path: Path) -> None:
    records = records_to_json(df)
    out_path.write_text(
        json.dumps(records, indent=2, allow_nan=False),
        encoding="utf-8",
    )
    print(f"Wrote {out_path.relative_to(ROOT)} ({len(records)} rows)")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    trade_metrics = load_trade_expectancy()

    rolling_windows = pd.read_csv(RESULTS_DIR / "rolling_1yr_windows.csv")
    rolling_windows = enrich_rolling_windows(rolling_windows)

    rolling_summary = pd.read_csv(RESULTS_DIR / "rolling_1yr_summary.csv")
    rolling_summary = enrich_rolling_summary(rolling_summary, rolling_windows, trade_metrics)

    full_period = pd.read_csv(RESULTS_DIR / "full_period_summary.csv")
    full_period = enrich_full_period(full_period, trade_metrics)

    buy_hold = pd.read_csv(RESULTS_DIR / "buy_and_hold_comparison.csv")

    write_json(rolling_summary, OUTPUT_DIR / "rolling_1yr_summary.json")
    write_json(rolling_windows, OUTPUT_DIR / "rolling_1yr_windows.json")
    write_json(full_period, OUTPUT_DIR / "full_period_summary.json")
    write_json(buy_hold, OUTPUT_DIR / "buy_and_hold_comparison.json")


if __name__ == "__main__":
    main()
''', encoding="utf-8")

# -----------------------------
# 2) Patch app/dashboard-client.tsx
# -----------------------------
path = Path("app/dashboard-client.tsx")
text = path.read_text()

text = text.replace(
'''type SummaryRow = {
  strategy: string;
  probability_profitable_1yr: number;
  median_1yr_net_profit: number;
  worst_1yr_net_profit: number;
  average_1yr_net_profit: number;
  profitable_windows: number;
  number_of_windows: number;
};''',
'''type SummaryRow = {
  strategy: string;
  probability_profitable_1yr: number;
  median_1yr_net_profit: number;
  worst_1yr_net_profit: number;
  average_1yr_net_profit: number;
  profitable_windows: number;
  number_of_windows: number;
  expected_profit_per_trade?: number | null;
  expected_return_per_trade_pct?: number | null;
  average_win?: number | null;
  average_loss?: number | null;
  payoff_ratio?: number | null;
};'''
)

text = text.replace(
'''type FullPeriodRow = {
  strategy: string;
  number_of_trades: number;
  total_deployed: number;
  gross_profit: number;
  net_profit: number;
  return_on_deployed_capital: number;
  win_rate?: number;
  profit_factor?: number;
  max_drawdown?: number;
};''',
'''type FullPeriodRow = {
  strategy: string;
  number_of_trades: number;
  total_deployed: number;
  gross_profit: number;
  net_profit: number;
  return_on_deployed_capital: number;
  win_rate?: number | null;
  profit_factor?: number | null;
  max_drawdown?: number | null;
  expected_profit_per_trade?: number | null;
  expected_return_per_trade_pct?: number | null;
  average_win?: number | null;
  average_loss?: number | null;
  payoff_ratio?: number | null;
};'''
)

text = text.replace(
'''const formatPct = (value: number) => `${(value * 100).toFixed(1)}%`;
const formatPnL = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;''',
'''const isNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const formatPct = (value?: number | null) =>
  isNumber(value) ? `${(value * 100).toFixed(2)}%` : "—";

const formatPnL = (value?: number | null) =>
  isNumber(value) ? `${value >= 0 ? "+" : ""}${value.toFixed(2)}` : "—";

const formatRatio = (value?: number | null) =>
  isNumber(value) ? value.toFixed(2) : "—";'''
)

text = text.replace(
'''  const red = ranked.find((r) => r.strategy === "buy_after_red");
  const every = ranked.find((r) => r.strategy === "buy_every_session");''',
'''  const red = ranked.find((r) => r.strategy === "buy_after_red");
  const every = ranked.find((r) => r.strategy === "buy_every_session");

  const expectancyRanked = [...ranked].sort(
    (a, b) => (b.expected_profit_per_trade ?? -Infinity) - (a.expected_profit_per_trade ?? -Infinity)
  );
  const bestExpectancy = expectancyRanked[0];'''
)

text = text.replace(
'''    medianNet: row.median_1yr_net_profit
  }));''',
'''    medianNet: row.median_1yr_net_profit,
    expectedReturn: row.expected_profit_per_trade ?? 0
  }));'''
)

text = text.replace(
'''        <th className="px-3 py-2">Worst 1Y net P/L</th>
              </tr>''',
'''        <th className="px-3 py-2">Worst 1Y net P/L</th>
                <th className="px-3 py-2">Expected P/L / trade</th>
                <th className="px-3 py-2">Expected return / trade</th>
                <th className="px-3 py-2">Payoff ratio</th>
              </tr>'''
)

text = text.replace(
'''                  <td className="px-3 py-2">{formatPnL(row.worst_1yr_net_profit)}</td>
                </tr>''',
'''                  <td className="px-3 py-2">{formatPnL(row.worst_1yr_net_profit)}</td>
                  <td className="px-3 py-2">{formatPnL(row.expected_profit_per_trade)}</td>
                  <td className="px-3 py-2">{formatPct(row.expected_return_per_trade_pct)}</td>
                  <td className="px-3 py-2">{formatRatio(row.payoff_ratio)}</td>
                </tr>'''
)

text = text.replace(
'''      <section className="card">
        <h2 className="text-xl font-semibold">Strategy ranking table</h2>''',
'''      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Best expectancy</p>
          <p className="text-lg font-medium text-emerald-300">
            {displayNameMap[bestExpectancy.strategy] ?? bestExpectancy.strategy}
          </p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Expected P/L / trade</p>
          <p className="text-2xl font-semibold">{formatPnL(bestExpectancy.expected_profit_per_trade)}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Expected return / trade</p>
          <p className="text-2xl font-semibold">{formatPct(bestExpectancy.expected_return_per_trade_pct)}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Average win</p>
          <p className="text-2xl font-semibold text-emerald-300">{formatPnL(bestExpectancy.average_win)}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Average loss</p>
          <p className="text-2xl font-semibold text-rose-300">{formatPnL(bestExpectancy.average_loss)}</p>
        </div>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold">Expected Return Analysis</h2>
        <div className="mt-4 space-y-3 text-slate-200">
          <p>
            Winning percentage alone is incomplete. A strategy can win often and still lose money if its average loss is larger than its average win.
          </p>
          <p>
            The key measure is <span className="font-semibold text-cyan-300">expected P/L per trade</span>, which is the average net result each time the strategy trades.
          </p>
          <p>
            For the main strategy, <span className="font-semibold text-cyan-300">Buy after first green after red</span>, expected P/L per trade is{" "}
            <span className="font-semibold">{formatPnL(main?.expected_profit_per_trade)}</span>, or{" "}
            <span className="font-semibold">{formatPct(main?.expected_return_per_trade_pct)}</span> per $100 trade.
          </p>
        </div>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold">Strategy ranking table</h2>'''
)

text = text.replace(
'''      <section className="card h-[420px]">
        <h2 className="mb-4 text-lg font-semibold">Rolling one-year net P/L over time</h2>''',
'''      <section className="card h-[360px]">
        <h2 className="mb-4 text-lg font-semibold">Expected P/L per trade by strategy</h2>
        <ResponsiveContainer>
          <BarChart data={chartRanking}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="strategy" hide />
            <YAxis />
            <Tooltip formatter={(value: number) => formatPnL(value)} />
            <Bar dataKey="expectedReturn" fill="#34d399" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="card h-[420px]">
        <h2 className="mb-4 text-lg font-semibold">Rolling one-year net P/L over time</h2>'''
)

text = text.replace(
'''                  <th className="px-3 py-2">Profit factor</th>
                </tr>''',
'''                  <th className="px-3 py-2">Profit factor</th>
                  <th className="px-3 py-2">Expected P/L / trade</th>
                  <th className="px-3 py-2">Payoff ratio</th>
                </tr>'''
)

text = text.replace(
'''                    <td className="px-3 py-2">{row.profit_factor ? row.profit_factor.toFixed(2) : "—"}</td>
                  </tr>''',
'''                    <td className="px-3 py-2">{row.profit_factor ? row.profit_factor.toFixed(2) : "—"}</td>
                    <td className="px-3 py-2">{formatPnL(row.expected_profit_per_trade)}</td>
                    <td className="px-3 py-2">{formatRatio(row.payoff_ratio)}</td>
                  </tr>'''
)

text = text.replace(
'''          <p>
            <span className="font-semibold text-cyan-300">Plain-English verdict:</span> {verdict}''',
'''          <p>
            <span className="font-semibold text-cyan-300">Expected return:</span>{" "}
            The main strategy expectancy is {formatPnL(main?.expected_profit_per_trade)} per trade.
            Compared with Buy after red ({red ? formatPnL(red.expected_profit_per_trade) : "n/a"}) and
            Buy every session ({every ? formatPnL(every.expected_profit_per_trade) : "n/a"}), this shows whether the edge is actually positive after trade outcomes are averaged.
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Plain-English verdict:</span> {verdict}'''
)

path.write_text(text)
print("Patched expected return metrics into dashboard and data prep script.")
