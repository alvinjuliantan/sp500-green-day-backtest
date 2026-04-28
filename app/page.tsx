import { promises as fs } from "node:fs";
import path from "node:path";
import DashboardClient, { type FullPeriodRow, type SummaryRow, type WindowRow } from "./dashboard-client";

const displayNameMap: Record<string, string> = {
  buy_after_first_green_after_red: "Buy after first green after red",
  buy_after_every_green: "Buy after every green",
  buy_after_red: "Buy after red",
  buy_after_first_green_after_two_reds: "Buy after first green after two reds",
  buy_after_first_green_after_red_above_200dma: "Buy after first green after red above 200DMA",
  buy_after_first_green_after_red_below_200dma: "Buy after first green after red below 200DMA",
  buy_every_session: "Buy every session",
  buy_and_hold_100: "Buy and hold (100 units)"
};

async function loadJson(fileName: string) {
  const filePath = path.join(process.cwd(), "public", "data", fileName);
  const text = await fs.readFile(filePath, "utf8");
  return JSON.parse(text);
}

export default async function Page() {
  const [rollingSummary, rollingWindows, fullPeriod, buyHold] = await Promise.all([
    loadJson("rolling_1yr_summary.json") as Promise<SummaryRow[]>,
    loadJson("rolling_1yr_windows.json") as Promise<WindowRow[]>,
    loadJson("full_period_summary.json") as Promise<FullPeriodRow[]>,
    loadJson("buy_and_hold_comparison.json") as Promise<FullPeriodRow[]>
  ]);

  return (
    <DashboardClient
      rollingSummary={rollingSummary}
      rollingWindows={rollingWindows}
      fullPeriod={fullPeriod}
      buyHold={buyHold}
      displayNameMap={displayNameMap}
    />
  );
}
