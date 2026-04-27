import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="KNNBCCB™ S&P Futures Edge Dashboard",
    page_icon="📈",
    layout="wide",
)


# ============================================================
# STYLE
# ============================================================

st.markdown(
    """
    <style>
    /* Overall app */
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(37, 99, 235, 0.18), transparent 28%),
            radial-gradient(circle at top right, rgba(16, 185, 129, 0.12), transparent 28%),
            #080b12;
        color: #f9fafb;
    }

    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 4rem;
        max-width: 1500px;
    }

    /* Headings */
    h1 {
        font-size: 2.7rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.055em !important;
        color: #f9fafb !important;
        margin-bottom: 0.2rem !important;
    }

    h2 {
        font-size: 1.75rem !important;
        font-weight: 750 !important;
        letter-spacing: -0.04em !important;
        color: #f9fafb !important;
        margin-top: 2rem !important;
    }

    h3 {
        font-weight: 700 !important;
        letter-spacing: -0.03em !important;
        color: #f9fafb !important;
    }

    p, li, span, label {
        color: #d1d5db;
    }

    /* Caption */
    .stCaptionContainer {
        color: #9ca3af !important;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: linear-gradient(145deg, rgba(17, 24, 39, 0.96), rgba(31, 41, 55, 0.88));
        border: 1px solid rgba(148, 163, 184, 0.22);
        padding: 22px 22px;
        border-radius: 22px;
        box-shadow:
            0 16px 35px rgba(0, 0, 0, 0.28),
            inset 0 1px 0 rgba(255, 255, 255, 0.04);
        min-height: 132px;
    }

    div[data-testid="stMetric"] label {
        color: #9ca3af !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.05rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.045em;
        line-height: 1.15;
    }

    div[data-testid="stMetricDelta"] {
        color: #a7f3d0 !important;
    }

    /* Info/success/warning boxes */
    div[data-testid="stAlert"] {
        border-radius: 18px;
        border: 1px solid rgba(148, 163, 184, 0.18);
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.20);
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid rgba(148, 163, 184, 0.22);
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.22);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb, #10b981);
        color: white;
        border: none;
        border-radius: 14px;
        padding: 0.75rem 1.15rem;
        font-weight: 700;
        box-shadow: 0 12px 24px rgba(37, 99, 235, 0.25);
    }

    .stButton > button:hover {
        border: none;
        filter: brightness(1.08);
        transform: translateY(-1px);
    }

    /* Download buttons */
    .stDownloadButton > button {
        background: rgba(31, 41, 55, 0.95);
        color: #f9fafb;
        border: 1px solid rgba(148, 163, 184, 0.28);
        border-radius: 14px;
        padding: 0.7rem 1rem;
        font-weight: 650;
    }

    .stDownloadButton > button:hover {
        border-color: rgba(96, 165, 250, 0.8);
        color: #ffffff;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1020 0%, #080b12 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.18);
    }

    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f9fafb !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        background: rgba(17, 24, 39, 0.75);
        border-radius: 14px 14px 0 0;
        margin-right: 6px;
        padding: 10px 16px;
        color: #d1d5db;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        background: rgba(37, 99, 235, 0.22);
        color: #ffffff;
        border-bottom: 2px solid #60a5fa;
    }

    /* Horizontal rule */
    hr {
        border-color: rgba(148, 163, 184, 0.18);
        margin-top: 2rem;
        margin-bottom: 2rem;
    }

    /* Select boxes / inputs */
    div[data-baseweb="select"] > div,
    div[data-baseweb="input"] > div {
        background-color: rgba(17, 24, 39, 0.92);
        border-color: rgba(148, 163, 184, 0.24);
        color: #f9fafb;
        border-radius: 12px;
    }

    /* Expander */
    details {
        background: rgba(17, 24, 39, 0.75);
        border: 1px solid rgba(148, 163, 184, 0.18);
        border-radius: 18px;
        padding: 0.5rem 0.75rem;
    }

    /* Plotly chart container */
    div[data-testid="stPlotlyChart"] {
        background: rgba(17, 24, 39, 0.50);
        border: 1px solid rgba(148, 163, 184, 0.16);
        border-radius: 20px;
        padding: 14px;
        box-shadow: 0 14px 30px rgba(0, 0, 0, 0.18);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CONFIG
# ============================================================

TICKER = "ES=F"
RESULTS_DIR = "results"

DEFAULT_YEARS_OF_DATA = 12
DEFAULT_TRADE_SIZE = 100.00
DEFAULT_COST_RATE = 0.0002
DEFAULT_WINDOW_MONTHS = 12


# ============================================================
# DATA
# ============================================================

@st.cache_data(show_spinner=False)
def download_data(ticker, years_of_data):
    fallback_path = "data/es_f_yahoo_daily.csv"

    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=int(365.25 * years_of_data))

        data = yf.download(
            ticker,
            start=start_date.strftime("%Y-%m-%d"),
            end=end_date.strftime("%Y-%m-%d"),
            auto_adjust=True,
            progress=False,
        )

        if data.empty:
            raise ValueError("Yahoo returned empty data.")

        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        data = data[["Open", "High", "Low", "Close"]].dropna()
        return data

    except Exception as e:
        st.warning(
            f"Live Yahoo download failed, so the app is using saved fallback data instead. Error: {e}"
        )

        if not os.path.exists(fallback_path):
            st.error("Fallback CSV not found. Please add data/es_f_yahoo_daily.csv to the repo.")
            return pd.DataFrame()

        data = pd.read_csv(fallback_path, index_col=0, parse_dates=True)
        data = data[["Open", "High", "Low", "Close"]].dropna()
        return data


def prepare_signals(data):
    df = data.copy()

    df["green"] = df["Close"] > df["Open"]
    df["red"] = df["Close"] < df["Open"]
    df["flat"] = df["Close"] == df["Open"]
    df["intraday_return"] = df["Close"] / df["Open"] - 1
    df["sma_200"] = df["Close"].rolling(200).mean()

    signals = {}

    signals["buy_after_first_green_after_red"] = (
        df["green"] & df["red"].shift(1)
    ).shift(1)

    signals["buy_after_every_green"] = (
        df["green"]
    ).shift(1)

    signals["buy_after_red"] = (
        df["red"]
    ).shift(1)

    signals["buy_after_first_green_after_two_reds"] = (
        df["green"] & df["red"].shift(1) & df["red"].shift(2)
    ).shift(1)

    signals["buy_after_first_green_after_red_above_200dma"] = (
        df["green"]
        & df["red"].shift(1)
        & (df["Close"] > df["sma_200"])
    ).shift(1)

    signals["buy_after_first_green_after_red_below_200dma"] = (
        df["green"]
        & df["red"].shift(1)
        & (df["Close"] < df["sma_200"])
    ).shift(1)

    signals["buy_every_session"] = pd.Series(True, index=df.index)

    return df, signals


def calculate_trades(df, signal, strategy_name, trade_size, cost_rate):
    result = df.copy()

    result["signal"] = signal.fillna(False).astype(bool)
    trades = result[result["signal"]].copy()

    trades["strategy"] = strategy_name
    trades["trade_date"] = trades.index
    trades["gross_profit"] = trade_size * trades["intraday_return"]
    trades["cost"] = trade_size * cost_rate
    trades["net_profit"] = trades["gross_profit"] - trades["cost"]
    trades["cumulative_net_profit"] = trades["net_profit"].cumsum()

    return trades


def max_drawdown_from_pnl(pnl_series):
    if pnl_series.empty:
        return np.nan

    equity = pnl_series.cumsum()
    peak = equity.cummax()
    drawdown = equity - peak

    return drawdown.min()


def summarize_trades(trades, trade_size):
    number_of_trades = len(trades)
    total_deployed = number_of_trades * trade_size

    if number_of_trades == 0:
        return {
            "number_of_trades": 0,
            "total_deployed": 0.0,
            "gross_profit": 0.0,
            "net_profit": 0.0,
            "return_on_deployed_capital": np.nan,
            "average_net_profit_per_trade": np.nan,
            "median_net_profit_per_trade": np.nan,
            "win_rate": np.nan,
            "best_trade": np.nan,
            "worst_trade": np.nan,
            "profit_factor": np.nan,
            "max_drawdown": np.nan,
        }

    gross_profit = trades["gross_profit"].sum()
    net_profit = trades["net_profit"].sum()

    wins = trades.loc[trades["net_profit"] > 0, "net_profit"]
    losses = trades.loc[trades["net_profit"] < 0, "net_profit"]

    gross_wins = wins.sum()
    gross_losses = losses.sum()

    profit_factor = gross_wins / abs(gross_losses) if gross_losses != 0 else np.nan

    return {
        "number_of_trades": number_of_trades,
        "total_deployed": total_deployed,
        "gross_profit": gross_profit,
        "net_profit": net_profit,
        "return_on_deployed_capital": net_profit / total_deployed if total_deployed > 0 else np.nan,
        "average_net_profit_per_trade": trades["net_profit"].mean(),
        "median_net_profit_per_trade": trades["net_profit"].median(),
        "win_rate": (trades["net_profit"] > 0).mean(),
        "best_trade": trades["net_profit"].max(),
        "worst_trade": trades["net_profit"].min(),
        "profit_factor": profit_factor,
        "max_drawdown": max_drawdown_from_pnl(trades["net_profit"]),
    }


def generate_monthly_windows(data, window_months):
    first_date = data.index.min().normalize()
    last_date = data.index.max().normalize()

    start = pd.Timestamp(first_date.year, first_date.month, 1)

    if start < first_date:
        start = start + pd.DateOffset(months=1)

    windows = []
    current_start = start

    while True:
        current_end = (
            current_start
            + pd.DateOffset(months=window_months)
            - pd.DateOffset(days=1)
        )

        if current_end > last_date:
            break

        windows.append((current_start, current_end))
        current_start = current_start + pd.DateOffset(months=1)

    return windows


def run_rolling_backtest(df, all_trades, trade_size, window_months):
    windows = generate_monthly_windows(df, window_months)
    rolling_results = []

    for strategy_name, trades in all_trades.items():
        for window_start, window_end in windows:
            window_trades = trades[
                (trades.index >= window_start)
                & (trades.index <= window_end)
            ].copy()

            summary = summarize_trades(window_trades, trade_size)

            rolling_results.append({
                "strategy": strategy_name,
                "window_start": window_start.date(),
                "window_end": window_end.date(),
                "profitable": summary["net_profit"] > 0,
                **summary,
            })

    return pd.DataFrame(rolling_results)


def summarize_rolling_results(rolling_df):
    summary_rows = []

    for strategy_name, group in rolling_df.groupby("strategy"):
        number_of_windows = len(group)
        profitable_windows = group["profitable"].sum()

        summary_rows.append({
            "strategy": strategy_name,
            "number_of_windows": number_of_windows,
            "profitable_windows": profitable_windows,
            "probability_profitable_1yr": profitable_windows / number_of_windows if number_of_windows > 0 else np.nan,
            "average_1yr_net_profit": group["net_profit"].mean(),
            "median_1yr_net_profit": group["net_profit"].median(),
            "best_1yr_net_profit": group["net_profit"].max(),
            "worst_1yr_net_profit": group["net_profit"].min(),
            "average_trades_per_year": group["number_of_trades"].mean(),
            "median_trades_per_year": group["number_of_trades"].median(),
            "average_win_rate": group["win_rate"].mean(),
            "average_profit_factor": group["profit_factor"].replace([np.inf, -np.inf], np.nan).mean(),
            "average_max_drawdown": group["max_drawdown"].mean(),
            "median_return_on_deployed_capital": group["return_on_deployed_capital"].median(),
        })

    summary_df = pd.DataFrame(summary_rows)

    summary_df = summary_df.sort_values(
        by=["probability_profitable_1yr", "median_1yr_net_profit"],
        ascending=[False, False],
    )

    return summary_df


def buy_and_hold_comparison(df, trade_size):
    buy_hold_return = df["Close"].iloc[-1] / df["Open"].iloc[0] - 1
    buy_hold_profit = trade_size * buy_hold_return

    return {
        "strategy": "buy_and_hold_100",
        "gross_profit": buy_hold_profit,
        "net_profit": buy_hold_profit,
        "return_on_deployed_capital": buy_hold_return,
    }


@st.cache_data(show_spinner=False)
def run_all_backtests(ticker, years_of_data, trade_size, cost_rate, window_months):
    data = download_data(ticker, years_of_data)

    if data.empty:
        return None

    df, signals = prepare_signals(data)

    all_trades = {}

    for strategy_name, signal in signals.items():
        all_trades[strategy_name] = calculate_trades(
            df=df,
            signal=signal,
            strategy_name=strategy_name,
            trade_size=trade_size,
            cost_rate=cost_rate,
        )

    rolling_df = run_rolling_backtest(df, all_trades, trade_size, window_months)
    rolling_summary = summarize_rolling_results(rolling_df)

    full_rows = []
    for strategy_name, trades in all_trades.items():
        full_rows.append({
            "strategy": strategy_name,
            **summarize_trades(trades, trade_size),
        })

    full_summary = pd.DataFrame(full_rows).sort_values(
        by=["net_profit", "profit_factor"],
        ascending=[False, False],
    )

    buy_hold = pd.DataFrame([buy_and_hold_comparison(df, trade_size)])

    return {
        "data": df,
        "all_trades": all_trades,
        "rolling_df": rolling_df,
        "rolling_summary": rolling_summary,
        "full_summary": full_summary,
        "buy_hold": buy_hold,
    }


def format_currency(x):
    if pd.isna(x):
        return ""
    return f"${x:,.2f}"


def format_pct(x):
    if pd.isna(x):
        return ""
    return f"{x:.2%}"


def clean_strategy_name(name):
    return name.replace("_", " ")


# ============================================================
# UI
# ============================================================

st.markdown(
    """
    <div style="
        padding: 30px 34px;
        border-radius: 28px;
        background: linear-gradient(135deg, rgba(37,99,235,0.26), rgba(16,185,129,0.16));
        border: 1px solid rgba(148,163,184,0.22);
        box-shadow: 0 18px 45px rgba(0,0,0,0.28);
        margin-bottom: 26px;
    ">
        <div style="font-size: 0.86rem; color: #93c5fd; font-weight: 800; letter-spacing: 0.11em; text-transform: uppercase;">
            KNNBCCB™ Research Lab
        </div>
        <div style="font-size: 3rem; line-height: 1.05; font-weight: 850; letter-spacing: -0.065em; color: #ffffff; margin-top: 8px;">
            KNNBCCB™ S&amp;P Futures Edge Dashboard
        </div>
        <div style="font-size: 1.05rem; color: #cbd5e1; margin-top: 12px; max-width: 950px;">
            Rolling one-year backtest for ES=F using Yahoo Finance daily data. Compare signal strategies, consistency, drawdown, and probability of profitable one-year windows.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("Data limitation and research warning", expanded=True):
    st.markdown(
    """
    This dashboard uses **Yahoo Finance daily `ES=F` data**, so it is a useful first approximation, not a trading-grade futures backtest.

    The key limitation is that Yahoo's daily candle may not perfectly match the exact CME Globex session from **6:00pm ET to 5:00pm ET**.

    Use this dashboard to identify whether a strategy is worth deeper study. Before trading real money, validate the result with proper CME session data.
    """
)

with st.sidebar:
    st.header("Settings")

    ticker = st.text_input("Ticker", value=TICKER)

    years_of_data = st.slider(
        "Years of data",
        min_value=5,
        max_value=20,
        value=DEFAULT_YEARS_OF_DATA,
        step=1,
    )

    trade_size = st.number_input(
        "Trade size per trade ($)",
        min_value=10.0,
        max_value=100000.0,
        value=DEFAULT_TRADE_SIZE,
        step=10.0,
    )

    cost_rate = st.number_input(
        "Round-trip cost rate",
        min_value=0.0,
        max_value=0.01,
        value=DEFAULT_COST_RATE,
        step=0.0001,
        format="%.4f",
    )

    window_months = st.slider(
        "Rolling window months",
        min_value=3,
        max_value=36,
        value=DEFAULT_WINDOW_MONTHS,
        step=1,
    )

    st.divider()

    st.write("Strategies shown")

    available_strategy_names = [
        "buy_after_first_green_after_red",
        "buy_after_every_green",
        "buy_after_red",
        "buy_after_first_green_after_two_reds",
        "buy_after_first_green_after_red_above_200dma",
        "buy_after_first_green_after_red_below_200dma",
        "buy_every_session",
    ]

    selected_strategies = st.multiselect(
        "Select strategies",
        options=available_strategy_names,
        default=available_strategy_names,
        format_func=clean_strategy_name,
    )

run_button = st.button("Run / refresh backtest", type="primary")

with st.spinner("Running backtest..."):
    results = run_all_backtests(
        ticker=ticker,
        years_of_data=years_of_data,
        trade_size=trade_size,
        cost_rate=cost_rate,
        window_months=window_months,
    )

if results is None:
    st.error("No data downloaded. Check ticker or internet connection.")
    st.stop()

data = results["data"]
all_trades = results["all_trades"]
rolling_df = results["rolling_df"]
rolling_summary = results["rolling_summary"]
full_summary = results["full_summary"]
buy_hold = results["buy_hold"]

if selected_strategies:
    rolling_df = rolling_df[rolling_df["strategy"].isin(selected_strategies)]
    rolling_summary = rolling_summary[rolling_summary["strategy"].isin(selected_strategies)]
    full_summary = full_summary[full_summary["strategy"].isin(selected_strategies)]
    all_trades = {
        k: v for k, v in all_trades.items()
        if k in selected_strategies
    }

st.subheader("Latest data")
latest = data.iloc[-1]
previous = data.iloc[-2]

latest_green = latest["Close"] > latest["Open"]
latest_red = latest["Close"] < latest["Open"]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Data start", str(data.index[0].date()))
col2.metric("Data end", str(data.index[-1].date()))
col3.metric("Latest open", f"{latest['Open']:,.2f}")
col4.metric("Latest close", f"{latest['Close']:,.2f}")

signal_text = "GREEN" if latest_green else "RED" if latest_red else "FLAT"
st.info(f"Latest Yahoo daily ES=F candle is **{signal_text}**.")

# Signal for user's main strategy
df_signal, signal_dict = prepare_signals(data)
main_signal_today = bool(signal_dict["buy_after_first_green_after_red"].iloc[-1])

if main_signal_today:
    st.success("Main strategy signal: BUY this session open-to-close according to the available latest data.")
else:
    st.warning("Main strategy signal: No buy signal according to the available latest data.")

st.divider()

# ============================================================
# TOP KPI SECTION
# ============================================================

st.subheader("Strategy ranking: rolling window results")

if rolling_summary.empty:
    st.warning("No rolling summary available for selected strategies.")
    st.stop()

best = rolling_summary.iloc[0]

k1, k2, k3, k4 = st.columns(4)
k1.metric("Top strategy", clean_strategy_name(best["strategy"]))
k2.metric("Profitable windows", format_pct(best["probability_profitable_1yr"]))
k3.metric("Median window P/L", format_currency(best["median_1yr_net_profit"]))
k4.metric("Worst window P/L", format_currency(best["worst_1yr_net_profit"]))

# Styled summary table
summary_display = rolling_summary.copy()
summary_display["strategy"] = summary_display["strategy"].map(clean_strategy_name)
summary_display["probability_profitable_1yr"] = summary_display["probability_profitable_1yr"].map(format_pct)
summary_display["average_1yr_net_profit"] = summary_display["average_1yr_net_profit"].map(format_currency)
summary_display["median_1yr_net_profit"] = summary_display["median_1yr_net_profit"].map(format_currency)
summary_display["best_1yr_net_profit"] = summary_display["best_1yr_net_profit"].map(format_currency)
summary_display["worst_1yr_net_profit"] = summary_display["worst_1yr_net_profit"].map(format_currency)
summary_display["average_win_rate"] = summary_display["average_win_rate"].map(format_pct)
summary_display["average_max_drawdown"] = summary_display["average_max_drawdown"].map(format_currency)
summary_display["median_return_on_deployed_capital"] = summary_display["median_return_on_deployed_capital"].map(format_pct)

st.dataframe(
    summary_display,
    use_container_width=True,
    hide_index=True,
)

csv_summary = rolling_summary.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download rolling summary CSV",
    data=csv_summary,
    file_name="rolling_1yr_summary.csv",
    mime="text/csv",
)

st.divider()

# ============================================================
# CHARTS
# ============================================================

c1, c2 = st.columns(2)

with c1:
    st.subheader("Probability of profitable rolling window")
    prob_chart_df = rolling_summary.copy()
    prob_chart_df["strategy_clean"] = prob_chart_df["strategy"].map(clean_strategy_name)

    fig_prob = px.bar(
        prob_chart_df.sort_values("probability_profitable_1yr"),
        x="probability_profitable_1yr",
        y="strategy_clean",
        orientation="h",
        text="probability_profitable_1yr",
        labels={
            "probability_profitable_1yr": "Probability profitable",
            "strategy_clean": "Strategy",
        },
    )
    fig_prob.update_traces(texttemplate="%{text:.1%}", textposition="outside")
    fig_prob.update_layout(height=500, xaxis_tickformat=".0%")
    st.plotly_chart(fig_prob, use_container_width=True)

with c2:
    st.subheader("Median 1-year net P/L")
    median_chart_df = rolling_summary.copy()
    median_chart_df["strategy_clean"] = median_chart_df["strategy"].map(clean_strategy_name)

    fig_median = px.bar(
        median_chart_df.sort_values("median_1yr_net_profit"),
        x="median_1yr_net_profit",
        y="strategy_clean",
        orientation="h",
        labels={
            "median_1yr_net_profit": "Median 1-year net P/L",
            "strategy_clean": "Strategy",
        },
    )
    fig_median.update_layout(height=500)
    st.plotly_chart(fig_median, use_container_width=True)

st.subheader("Rolling 1-year net P/L over time")
rolling_plot_df = rolling_df.copy()
rolling_plot_df["window_start"] = pd.to_datetime(rolling_plot_df["window_start"])
rolling_plot_df["strategy_clean"] = rolling_plot_df["strategy"].map(clean_strategy_name)

fig_roll = px.line(
    rolling_plot_df,
    x="window_start",
    y="net_profit",
    color="strategy_clean",
    labels={
        "window_start": "Window start",
        "net_profit": "1-year net P/L",
        "strategy_clean": "Strategy",
    },
)
fig_roll.add_hline(y=0, line_dash="dash")
fig_roll.update_layout(height=600)
st.plotly_chart(fig_roll, use_container_width=True)

st.subheader("Full-period cumulative net P/L")
fig_equity = go.Figure()

for strategy_name, trades in all_trades.items():
    if trades.empty:
        continue

    fig_equity.add_trace(
        go.Scatter(
            x=trades.index,
            y=trades["net_profit"].cumsum(),
            mode="lines",
            name=clean_strategy_name(strategy_name),
        )
    )

fig_equity.update_layout(
    height=600,
    xaxis_title="Date",
    yaxis_title="Cumulative net P/L",
)
st.plotly_chart(fig_equity, use_container_width=True)

st.divider()

# ============================================================
# DETAIL TABS
# ============================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Full-period summary",
        "Rolling window details",
        "Recent trades",
        "Buy & hold",
    ]
)

with tab1:
    st.subheader("Full-period strategy summary")
    full_display = full_summary.copy()
    full_display["strategy"] = full_display["strategy"].map(clean_strategy_name)
    st.dataframe(full_display, use_container_width=True, hide_index=True)

    st.download_button(
        "Download full-period summary CSV",
        data=full_summary.to_csv(index=False).encode("utf-8"),
        file_name="full_period_summary.csv",
        mime="text/csv",
    )

with tab2:
    st.subheader("All rolling windows")
    rolling_display = rolling_df.copy()
    rolling_display["strategy"] = rolling_display["strategy"].map(clean_strategy_name)
    st.dataframe(rolling_display, use_container_width=True, hide_index=True)

    st.download_button(
        "Download rolling window details CSV",
        data=rolling_df.to_csv(index=False).encode("utf-8"),
        file_name="rolling_1yr_windows.csv",
        mime="text/csv",
    )

with tab3:
    st.subheader("Recent trades by selected strategy")
    selected_for_trades = st.selectbox(
        "Choose strategy",
        options=list(all_trades.keys()),
        format_func=clean_strategy_name,
    )

    recent_trades = all_trades[selected_for_trades].tail(30).copy()
    st.dataframe(recent_trades, use_container_width=True)

    st.download_button(
        "Download selected strategy trades CSV",
        data=all_trades[selected_for_trades].to_csv(index=True).encode("utf-8"),
        file_name=f"trades_{selected_for_trades}.csv",
        mime="text/csv",
    )

with tab4:
    st.subheader("Buy-and-hold comparison")
    st.dataframe(buy_hold, use_container_width=True, hide_index=True)

st.caption(
    "This is research code, not financial advice. Validate the strategy with proper CME session data before trading real money."
)