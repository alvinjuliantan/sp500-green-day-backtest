import os
from datetime import datetime, timedelta

import yfinance as yf
import pandas as pd

TICKER = "ES=F"
YEARS_OF_DATA = 12

os.makedirs("data", exist_ok=True)

end_date = datetime.today()
start_date = end_date - timedelta(days=int(365.25 * YEARS_OF_DATA))

data = yf.download(
    TICKER,
    start=start_date.strftime("%Y-%m-%d"),
    end=end_date.strftime("%Y-%m-%d"),
    auto_adjust=True,
    progress=False,
)

if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

data = data[["Open", "High", "Low", "Close"]].dropna()
data.to_csv("data/es_f_yahoo_daily.csv")

print("Saved data/es_f_yahoo_daily.csv")
print(data.tail())
