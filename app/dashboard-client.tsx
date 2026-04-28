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

type SummaryRow = {
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
};

type WindowRow = {
  strategy: string;
  window_end: string;
  net_profit: number;
};

type FullPeriodRow = {
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
};

type Props = {
  rollingSummary: SummaryRow[];
  rollingWindows: WindowRow[];
  fullPeriod: FullPeriodRow[];
  buyHold: FullPeriodRow[];
  displayNameMap: Record<string, string>;
};

const isNumber = (value: unknown): value is number =>
  typeof value === "number" && Number.isFinite(value);

const formatPct = (value?: number | null) =>
  isNumber(value) ? `${(value * 100).toFixed(2)}%` : "—";

const formatPctShort = (value?: number | null) =>
  isNumber(value) ? `${(value * 100).toFixed(1)}%` : "—";

const formatPnL = (value?: number | null) =>
  isNumber(value) ? `${value >= 0 ? "+" : ""}${value.toFixed(2)}` : "—";

const formatRatio = (value?: number | null) =>
  isNumber(value) ? value.toFixed(2) : "—";

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
    : main.probability_profitable_1yr >= 0.65 && main.median_1yr_net_profit > 0 && (main.expected_profit_per_trade ?? 0) > 0
      ? "Strong"
      : main.probability_profitable_1yr >= 0.55 && main.median_1yr_net_profit > 0 && (main.expected_profit_per_trade ?? 0) > 0
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
    expectedReturn: row.expected_profit_per_trade ?? 0
  }));

  return (
    <main className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-8 md:px-8">
      <section className="card bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/50">
        <p className="text-xs uppercase tracking-[0.2em] text-cyan-300">Quant Dashboard</p>
        <h1 className="mt-2 text-3xl font-semibold md:text-5xl">KNNBCCB™ S&amp;P Futures Edge Dashboard</h1>
        <p className="mt-3 text-slate-300">
          Rolling one-year backtest for ES futures signal strategies.
        </p>
        <div className="mt-4 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-200">
          This dashboard uses Yahoo Finance ES=F daily data as an approximation. It may not perfectly match exact
          CME Globex 6:00pm ET to 5:00pm ET sessions.
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Top strategy</p>
          <p className="text-lg font-medium text-emerald-300">{displayNameMap[top.strategy] ?? top.strategy}</p>
        </div>
        <div className="kpi">
          <p className="text-xs uppercase tracking-widest text-slate-400">Probability profitable</p>
          <p className="text-2xl font-semibold">{formatPctShort(top.probability_profitable_1yr)}</p>
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

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
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
            Expected P/L per trade is the average net result each time the strategy trades. This is the practical measure of whether the edge is positive.
          </p>
          <p>
            Main strategy: <span className="font-semibold text-cyan-300">Buy after first green after red</span>. Expected P/L per trade is{" "}
            <span className="font-semibold">{formatPnL(main?.expected_profit_per_trade)}</span>, or{" "}
            <span className="font-semibold">{formatPct(main?.expected_return_per_trade_pct)}</span> per $100 trade.
          </p>
          <p>
            Comparison: Buy after red has expectancy of {red ? formatPnL(red.expected_profit_per_trade) : "n/a"} per trade.
            Buy every session has expectancy of {every ? formatPnL(every.expected_profit_per_trade) : "n/a"} per trade.
          </p>
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
                <th className="px-3 py-2">Expected P/L / trade</th>
                <th className="px-3 py-2">Expected return / trade</th>
                <th className="px-3 py-2">Payoff ratio</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/70">
              {ranked.map((row) => (
                <tr key={row.strategy}>
                  <td className="px-3 py-2">{displayNameMap[row.strategy] ?? row.strategy}</td>
                  <td className="px-3 py-2">
                    {row.profitable_windows} / {row.number_of_windows}
                  </td>
                  <td className="px-3 py-2">{formatPctShort(row.probability_profitable_1yr)}</td>
                  <td className="px-3 py-2">{formatPnL(row.median_1yr_net_profit)}</td>
                  <td className="px-3 py-2">{formatPnL(row.worst_1yr_net_profit)}</td>
                  <td className="px-3 py-2">{formatPnL(row.expected_profit_per_trade)}</td>
                  <td className="px-3 py-2">{formatPct(row.expected_return_per_trade_pct)}</td>
                  <td className="px-3 py-2">{formatRatio(row.payoff_ratio)}</td>
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
              <Tooltip formatter={(value: number) => formatPctShort(value)} />
              <Bar dataKey="probability" fill="#22d3ee" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="card h-[360px]">
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
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
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

        <div className="card h-[360px]">
          <h2 className="mb-4 text-lg font-semibold">Full-period expectancy</h2>
          <ResponsiveContainer>
            <BarChart
              data={fullPeriod.map((row) => ({
                strategy: displayNameMap[row.strategy] ?? row.strategy,
                expectedReturn: row.expected_profit_per_trade ?? 0
              }))}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="strategy" hide />
              <YAxis />
              <Tooltip formatter={(value: number) => formatPnL(value)} />
              <Bar dataKey="expectedReturn" fill="#f59e0b" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
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
                  <th className="px-3 py-2">Expected P/L / trade</th>
                  <th className="px-3 py-2">Payoff ratio</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/70">
                {fullPeriod.map((row) => (
                  <tr key={row.strategy}>
                    <td className="px-3 py-2">{displayNameMap[row.strategy] ?? row.strategy}</td>
                    <td className="px-3 py-2">{formatPnL(row.net_profit)}</td>
                    <td className="px-3 py-2">{formatPctShort(row.win_rate)}</td>
                    <td className="px-3 py-2">{formatRatio(row.profit_factor)}</td>
                    <td className="px-3 py-2">{formatPnL(row.expected_profit_per_trade)}</td>
                    <td className="px-3 py-2">{formatRatio(row.payoff_ratio)}</td>
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
                    <td className="px-3 py-2">{formatPctShort(row.return_on_deployed_capital)}</td>
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
            <span className="font-semibold text-cyan-300">Best strategy by probability:</span>{" "}
            {displayNameMap[top.strategy] ?? top.strategy} ({formatPctShort(top.probability_profitable_1yr)} profitable windows).
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Best strategy by expectancy:</span>{" "}
            {displayNameMap[bestExpectancy.strategy] ?? bestExpectancy.strategy} with {formatPnL(bestExpectancy.expected_profit_per_trade)} expected P/L per trade.
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Main strategy:</span> Buy after first green after red.
            {main
              ? ` It shows ${formatPctShort(main.probability_profitable_1yr)} profitable windows, ${formatPnL(
                  main.median_1yr_net_profit
                )} median one-year P/L, and ${formatPnL(main.expected_profit_per_trade)} expected P/L per trade.`
              : " Data unavailable."}
          </p>
          <p>
            <span className="font-semibold text-cyan-300">Plain-English verdict:</span> {verdict}
            {verdict === "Strong"
              ? " — the strategy appears robust across rolling windows with positive expectancy."
              : verdict === "Mild / inconclusive"
                ? " — results are positive but not dominant, so confidence should be moderate."
                : " — the edge does not appear consistent enough under this test setup."}
          </p>
        </div>
      </section>
    </main>
  );
}
