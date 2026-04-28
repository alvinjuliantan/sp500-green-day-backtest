"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export type SummaryRow = {
  strategy: string;
  probability_profitable_1yr: number;
  median_1yr_net_profit: number;
  worst_1yr_net_profit: number;
  average_1yr_net_profit: number;
  profitable_windows: number;
  number_of_windows: number;
  expected_profit_per_trade: number | null;
  expected_return_per_trade_pct: number | null;
  average_win: number | null;
  average_loss: number | null;
  payoff_ratio: number | null;
};

export type WindowRow = {
  strategy: string;
  window_end: string;
  net_profit: number;
};

export type FullPeriodRow = {
  strategy: string;
  number_of_trades: number;
  total_deployed: number;
  gross_profit: number;
  net_profit: number;
  return_on_deployed_capital: number;
  win_rate?: number;
  profit_factor?: number;
  expected_profit_per_trade?: number | null;
  expected_return_per_trade_pct?: number | null;
  average_win?: number | null;
  average_loss?: number | null;
  payoff_ratio?: number | null;
};

type Props = {
  rollingSummary: SummaryRow[];
  rollingWindows: WindowRow[];
  fullPeriod: FullPeriodRow[];
  buyHold: FullPeriodRow[];
  displayNameMap: Record<string, string>;
};

const formatPct = (value: number) => `${(value * 100).toFixed(2)}%`;
const formatPnL = (value: number) => `${value >= 0 ? "+" : ""}${value.toFixed(2)}`;
const formatNullablePnL = (value: number | null | undefined) => (value == null ? "—" : formatPnL(value));
const formatNullablePct = (value: number | null | undefined) => (value == null ? "—" : formatPct(value));
const formatNullableNum = (value: number | null | undefined) => (value == null ? "—" : value.toFixed(2));

export default function DashboardClient({
  rollingSummary,
  rollingWindows,
  fullPeriod,
  buyHold,
  displayNameMap
}: Props) {
  const ranked = [...rollingSummary].sort(
    (a, b) => b.probability_profitable_1yr - a.probability_profitable_1yr
  );

  const expectancyRanked = [...rollingSummary].sort(
    (a, b) => (b.expected_profit_per_trade ?? -Infinity) - (a.expected_profit_per_trade ?? -Infinity)
  );

  const top = ranked[0];
  const bestExpectancy = expectancyRanked[0];
  const mainStrategyKey = "buy_after_first_green_after_red";
  const main = ranked.find((r) => r.strategy === mainStrategyKey);
  const red = ranked.find((r) => r.strategy === "buy_after_red");
  const every = ranked.find((r) => r.strategy === "buy_every_session");

  const verdict = !main
    ? "Not available"
    : main.probability_profitable_1yr >= 0.65 && main.median_1yr_net_profit > 0
      ? "Strong"
      : main.probability_profitable_1yr >= 0.55 && main.median_1yr_net_profit > 0
        ? "Mild / inconclusive"
        : "Weak";

  const pnlTimeline = rollingWindows.reduce<Record<string, Record<string, number | string>>>((acc, row) => {
    if (!acc[row.window_end]) {
      acc[row.window_end] = { window_end: row.window_end };
    }
    acc[row.window_end][row.strategy] = row.net_profit;
    return acc;
  }, {});

  const lineData = Object.values(pnlTimeline).sort((a, b) => {
    const first = String(a.window_end);
    const second = String(b.window_end);
    return first.localeCompare(second);
  });

  const chartRanking = ranked.map((row) => ({
    strategy: displayNameMap[row.strategy] ?? row.strategy,
    probability: row.probability_profitable_1yr,
    medianNet: row.median_1yr_net_profit,
    expectedReturnPct: row.expected_return_per_trade_pct ?? 0
  }));

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 md:px-8">
      <section className="card bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/50">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Quant Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold md:text-5xl">KNNBCCB™ S&amp;P Futures Edge Dashboard</h1>
        <p className="mt-3 text-slate-300">Rolling one-year backtest for ES futures signal strategies.</p>
        <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
          This dashboard uses Yahoo Finance ES=F daily data as an approximation. It may not perfectly match exact CME
          Globex 6:00pm ET to 5:00pm ET sessions.
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Top strategy</p>
          <p className="text-lg font-medium text-emerald-300">{displayNameMap[top.strategy] ?? top.strategy}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Probability profitable</p>
          <p className="text-2xl font-semibold">{formatPct(top.probability_profitable_1yr)}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Median one-year P/L</p>
          <p className="text-2xl font-semibold">{formatPnL(top.median_1yr_net_profit)}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Worst one-year P/L</p>
          <p className="text-2xl font-semibold text-rose-300">{formatPnL(top.worst_1yr_net_profit)}</p>
        </div>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold">Expected Return Analysis</h2>
        <p className="mt-2 text-sm text-slate-300">
          Win rate alone can mislead. A strategy may win often yet still lose money if losses are larger than wins.
          Expected return per trade is the core edge metric.
        </p>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          <div className="kpi">
            <p className="text-xs uppercase tracking-widest text-slate-400">Best expected return per trade</p>
            <p className="text-sm text-emerald-300">{displayNameMap[bestExpectancy.strategy] ?? bestExpectancy.strategy}</p>
            <p className="text-2xl font-semibold">{formatNullablePnL(bestExpectancy.expected_profit_per_trade)}</p>
          </div>
          <div className="kpi">
            <p className="text-xs uppercase tracking-widest text-slate-400">Expected return per trade %</p>
            <p className="text-2xl font-semibold">{formatNullablePct(bestExpectancy.expected_return_per_trade_pct)}</p>
          </div>
          <div className="kpi">
            <p className="text-xs uppercase tracking-widest text-slate-400">Average win</p>
            <p className="text-2xl font-semibold text-emerald-300">{formatNullablePnL(bestExpectancy.average_win)}</p>
          </div>
          <div className="kpi">
            <p className="text-xs uppercase tracking-widest text-slate-400">Average loss</p>
            <p className="text-2xl font-semibold text-rose-300">{formatNullablePnL(bestExpectancy.average_loss)}</p>
          </div>
          <div className="kpi">
            <p className="text-xs uppercase tracking-widest text-slate-400">Payoff ratio</p>
            <p className="text-2xl font-semibold">{formatNullableNum(bestExpectancy.payoff_ratio)}</p>
          </div>
        </div>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold">Strategy ranking table</h2>
        <div className="table-wrap mt-4">
          <table className="min-w-full divide-y divide-slate-800 text-sm">
            <thead className="bg-slate-900/70 text-left text-slate-300">
              <tr>
                <th className="px-3 py-2">Strategy</th>
                <th className="px-3 py-2">Profitable windows</th>
                <th className="px-3 py-2">Probability profitable</th>
                <th className="px-3 py-2">Median 1Y net P/L</th>
                <th className="px-3 py-2">Worst 1Y net P/L</th>
                <th className="px-3 py-2">Expected P/L per trade</th>
                <th className="px-3 py-2">Expected return per trade %</th>
                <th className="px-3 py-2">Average win</th>
                <th className="px-3 py-2">Average loss</th>
                <th className="px-3 py-2">Payoff ratio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {ranked.map((row) => (
                <tr key={row.strategy}>
                  <td className="px-3 py-2">{displayNameMap[row.strategy] ?? row.strategy}</td>
                  <td className="px-3 py-2">{row.profitable_windows} / {row.number_of_windows}</td>
                  <td className="px-3 py-2">{formatPct(row.probability_profitable_1yr)}</td>
                  <td className="px-3 py-2">{formatPnL(row.median_1yr_net_profit)}</td>
                  <td className="px-3 py-2">{formatPnL(row.worst_1yr_net_profit)}</td>
                  <td className="px-3 py-2">{formatNullablePnL(row.expected_profit_per_trade)}</td>
                  <td className="px-3 py-2">{formatNullablePct(row.expected_return_per_trade_pct)}</td>
                  <td className="px-3 py-2">{formatNullablePnL(row.average_win)}</td>
                  <td className="px-3 py-2">{formatNullablePnL(row.average_loss)}</td>
                  <td className="px-3 py-2">{formatNullableNum(row.payoff_ratio)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="card h-[360px]">
          <h2 className="mb-4 text-lg font-semibold">Probability profitable by strategy</h2>
          <ResponsiveContainer>
            <BarChart data={chartRanking}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="strategy" hide />
              <YAxis tickFormatter={(v) => `${(v * 100).toFixed(0)}%`} />
              <Tooltip formatter={(value: number) => formatPct(value)} />
              <Bar dataKey="probability" fill="#22d3ee" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card h-[360px]">
          <h2 className="mb-4 text-lg font-semibold">Median one-year net P/L by strategy</h2>
          <ResponsiveContainer>
            <BarChart data={chartRanking}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="strategy" hide />
              <YAxis />
              <Tooltip formatter={(value: number) => formatPnL(value)} />
              <Bar dataKey="medianNet" fill="#818cf8" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="card h-[360px]">
        <h2 className="mb-4 text-lg font-semibold">Expected return per trade by strategy</h2>
        <ResponsiveContainer>
          <BarChart data={chartRanking}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="strategy" hide />
            <YAxis tickFormatter={(v) => `${(v * 100).toFixed(2)}%`} />
            <Tooltip formatter={(value: number) => formatPct(value)} />
            <Bar dataKey="expectedReturnPct" fill="#34d399" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </section>

      <section className="card h-[420px]">
        <h2 className="mb-4 text-lg font-semibold">Rolling one-year net P/L over time</h2>
        <ResponsiveContainer>
          <LineChart data={lineData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="window_end" tick={{ fontSize: 12 }} />
            <YAxis />
            <Tooltip />
            <Legend />
            {ranked.map((row, idx) => (
              <Line
                key={row.strategy}
                dataKey={row.strategy}
                name={displayNameMap[row.strategy] ?? row.strategy}
                stroke={["#22d3ee", "#818cf8", "#34d399", "#f59e0b", "#f472b6", "#60a5fa", "#f87171"][idx % 7]}
                dot={false}
                strokeWidth={2}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="card">
          <h2 className="text-lg font-semibold">Full-period summary</h2>
          <div className="table-wrap mt-4">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-900/70 text-left text-slate-300">
                <tr>
                  <th className="px-3 py-2">Strategy</th>
                  <th className="px-3 py-2">Net P/L</th>
                  <th className="px-3 py-2">Win rate</th>
                  <th className="px-3 py-2">Profit factor</th>
                  <th className="px-3 py-2">Expected P/L per trade</th>
                  <th className="px-3 py-2">Payoff ratio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {fullPeriod.map((row) => (
                  <tr key={row.strategy}>
                    <td className="px-3 py-2">{displayNameMap[row.strategy] ?? row.strategy}</td>
                    <td className="px-3 py-2">{formatPnL(row.net_profit)}</td>
                    <td className="px-3 py-2">{row.win_rate ? formatPct(row.win_rate) : "—"}</td>
                    <td className="px-3 py-2">{row.profit_factor ? row.profit_factor.toFixed(2) : "—"}</td>
                    <td className="px-3 py-2">{formatNullablePnL(row.expected_profit_per_trade)}</td>
                    <td className="px-3 py-2">{formatNullableNum(row.payoff_ratio)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold">Buy-and-hold comparison</h2>
          <div className="table-wrap mt-4">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-900/70 text-left text-slate-300">
                <tr>
                  <th className="px-3 py-2">Strategy</th>
                  <th className="px-3 py-2">Net P/L</th>
                  <th className="px-3 py-2">Return on deployed capital</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {buyHold.map((row) => (
                  <tr key={row.strategy}>
                    <td className="px-3 py-2">{displayNameMap[row.strategy] ?? row.strategy}</td>
                    <td className="px-3 py-2">{formatPnL(row.net_profit)}</td>
                    <td className="px-3 py-2">{formatPct(row.return_on_deployed_capital)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="card">
        <h2 className="text-xl font-semibold">Analysis and interpretation</h2>
        <div className="mt-4 space-y-3 text-slate-200">
          <p>
            Winning percentage alone is insufficient: a strategy can win often but still lose money if average losses
            are larger than average wins. Expected return per trade is the key measure of whether the edge is real.
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Best strategy by probability:</span>{" "}
            {displayNameMap[top.strategy] ?? top.strategy} ({formatPct(top.probability_profitable_1yr)} profitable windows).
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Main strategy expectancy:</span>{" "}
            {main
              ? `${formatNullablePnL(main.expected_profit_per_trade)} per trade (${formatNullablePct(main.expected_return_per_trade_pct)}).`
              : "Data unavailable."}{" "}
            {main && (main.expected_profit_per_trade ?? 0) > 0
              ? "This indicates positive expectancy."
              : "This indicates negative/weak expectancy."}
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Comparison:</span> Buy after first green after red
            ({main ? `${formatNullablePnL(main.expected_profit_per_trade)}` : "n/a"}) vs Buy after red
            ({red ? `${formatNullablePnL(red.expected_profit_per_trade)}` : "n/a"}) vs Buy every session
            ({every ? `${formatNullablePnL(every.expected_profit_per_trade)}` : "n/a"}).
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Plain-English verdict:</span> {verdict}
            {verdict === "Strong"
              ? " — the strategy appears robust across rolling windows with positive median outcomes."
              : verdict === "Mild / inconclusive"
                ? " — results are positive but not dominant, so confidence should be moderate."
                : " — the edge does not appear consistent enough under this test setup."}
          </p>
        </div>
      </section>
    </main>
  );
}
