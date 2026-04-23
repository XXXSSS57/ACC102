"""
ACC102 Mini Assignment - DuPont Analysis Data Downloader
=========================================================
Companies: AAPL, MSFT, TSLA
Data: Income Statement, Balance Sheet, Stock Price (2014-2024)
Run: python download_data.py
Output: ./data/ folder with CSV files
"""

import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# ── Config ──────────────────────────────────────────────
TICKERS   = ["AAPL", "MSFT", "TSLA"]
START     = "2014-01-01"
END       = "2024-12-31"
DATA_DIR  = "./data"
ACCESS_DATE = datetime.today().strftime("%Y-%m-%d")   # for citation in reflection
# ────────────────────────────────────────────────────────

os.makedirs(DATA_DIR, exist_ok=True)


# ── Helper: flatten MultiIndex columns if present ───────
def flatten_cols(df):
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = ["_".join([str(c) for c in col if c]) for col in df.columns]
    return df


# ── 1. Annual Financials (Income Statement + Balance Sheet) ──
print("=" * 55)
print("Downloading annual financials …")
print("=" * 55)

all_income  = {}
all_balance = {}

for ticker in TICKERS:
    print(f"\n  [{ticker}]")
    stock = yf.Ticker(ticker)

    # --- Income Statement ---
    inc = stock.financials          # columns = fiscal year dates, rows = line items
    if inc is not None and not inc.empty:
        inc = inc.T                 # transpose → rows = years, columns = items
        inc.index = pd.to_datetime(inc.index)
        inc.index.name = "fiscal_year"
        inc["ticker"] = ticker
        all_income[ticker] = inc
        print(f"    Income Statement : {len(inc)} years, {len(inc.columns)} fields")
    else:
        print(f"    Income Statement : ⚠️  no data")

    # --- Balance Sheet ---
    bal = stock.balance_sheet
    if bal is not None and not bal.empty:
        bal = bal.T
        bal.index = pd.to_datetime(bal.index)
        bal.index.name = "fiscal_year"
        bal["ticker"] = ticker
        all_balance[ticker] = bal
        print(f"    Balance Sheet    : {len(bal)} years, {len(bal.columns)} fields")
    else:
        print(f"    Balance Sheet    : ⚠️  no data")

# Save combined financials
if all_income:
    df_inc = pd.concat(all_income.values())
    df_inc.to_csv(f"{DATA_DIR}/income_statement.csv")
    print(f"\n✅  Saved → {DATA_DIR}/income_statement.csv")

if all_balance:
    df_bal = pd.concat(all_balance.values())
    df_bal.to_csv(f"{DATA_DIR}/balance_sheet.csv")
    print(f"✅  Saved → {DATA_DIR}/balance_sheet.csv")


# ── 2. Annual Stock Price (year-end close) ───────────────
print("\n" + "=" * 55)
print("Downloading annual stock prices …")
print("=" * 55)

price_frames = []

for ticker in TICKERS:
    print(f"\n  [{ticker}]")
    raw = yf.download(ticker, start=START, end=END,
                      interval="1d", auto_adjust=True, progress=False)
    if raw.empty:
        print(f"    ⚠️  no price data")
        continue

    raw = flatten_cols(raw)

    # Pick the correct Close column (handles single or multi-ticker download)
    close_col = next((c for c in raw.columns
                      if "close" in c.lower() or "adj" in c.lower()), None)
    if close_col is None:
        print(f"    ⚠️  close column not found  (columns: {list(raw.columns)})")
        continue

    raw.index = pd.to_datetime(raw.index)

    # Resample to year-end
    annual = raw[[close_col]].resample("YE").last()
    annual.columns = ["close_year_end"]
    annual["ticker"] = ticker
    annual.index.name = "date"

    price_frames.append(annual)
    print(f"    Stock Price      : {len(annual)} year-end rows")

if price_frames:
    df_price = pd.concat(price_frames)
    df_price.to_csv(f"{DATA_DIR}/stock_price_annual.csv")
    print(f"\n✅  Saved → {DATA_DIR}/stock_price_annual.csv")


# ── 3. Print citation note ───────────────────────────────
print("\n" + "=" * 55)
print("DATA CITATION (copy into your reflection report):")
print("=" * 55)
print(f"""
  Source : Yahoo Finance via yfinance Python library
           (https://pypi.org/project/yfinance/)
  Tickers: {', '.join(TICKERS)}
  Period : {START} to {END}
  Accessed: {ACCESS_DATE}

  Note: Financial statement data reflects fiscal year
  end figures as reported. Stock prices are adjusted
  for splits and dividends (auto_adjust=True).
""")

print("All done! Files saved to:", os.path.abspath(DATA_DIR))
