import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KNNBCCB™ S&P Futures Edge Dashboard",
  description: "Rolling one-year backtest dashboard for ES futures signal strategies"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
