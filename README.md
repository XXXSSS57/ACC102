# Five-Factor DuPont Analysis Tool

**ACC102 Mini Assignment — Track 4: Interactive Data Analysis Tool**  
Xi'an Jiaotong-Liverpool University · Semester 2 2025-2026

---

## Overview

This project is an interactive Streamlit application that decomposes **Return on Equity (ROE)** into five financial drivers using the DuPont framework. It analyses three major technology companies — Apple (AAPL), Microsoft (MSFT), and Tesla (TSLA) — and helps users understand not just *how much* ROE a company earns, but *why*.

**Analytical Question:**
> Among AAPL, MSFT, and TSLA, what drives ROE differences — and how have those drivers changed over time?

**Target Audience:** Undergraduate finance and accounting students, retail investors, and equity analysts who want to move beyond headline ROE figures.

🔗Live App: https://acc102.streamlit.app
---

## Five-Factor DuPont Formula

```
ROE = Tax Burden × Interest Burden × EBIT Margin × Asset Turnover × Equity Multiplier

    = (Net Income / EBT) × (EBT / EBIT) × (EBIT / Revenue) × (Revenue / Assets) × (Assets / Equity)
```

---

## App Features

The app contains six interactive tabs:

| Tab | Description |
|-----|-------------|
| 📈 ROE Trend | Historical ROE trend with industry benchmark line |
| 🔍 Factor Breakdown | Five-factor bar chart per company; highlight any factor; benchmark overlay |
| 🏆 ROE Quality Scorecard | Scores ROE quality 0–100 based on what drives it; red/amber/green grading |
| 📊 Industry Benchmark | Side-by-side comparison against S&P 500 IT sector averages; deviation heatmap |
| ⚙️ What-If Simulator | Adjust any factor with sliders to see real-time ROE impact; sensitivity curves; cross-company comparison |
| 🌊 Attribution Waterfall | Select two years; waterfall chart showing each factor's contribution to ROE change |

**Sidebar controls:** filter by company and year range. Top metric cards show latest ROE with year-on-year delta.

---

## Data Sources

| Data | Source | Period | Accessed |
|------|--------|--------|----------|
| Income Statement | Yahoo Finance via `yfinance` | FY 2021–2025 | April 2026 |
| Balance Sheet | Yahoo Finance via `yfinance` | FY 2021–2025 | April 2026 |
| Stock Price (year-end) | Yahoo Finance via `yfinance` | 2014–2024 | April 2026 |

Industry benchmark figures are approximate 5-year averages for the S&P 500 Information Technology sector, used for educational comparison purposes.

---

## Project Structure

```
/  (repository root)
├── app.py                      # Streamlit interactive application
├── notebook.ipynb    # Python notebook (full analytical workflow)
├── download_data.py            # Script to download and save CSV data
└── README.md                   # This file

```

---

## Setup & Installation

### Requirements

- Python 3.8 or above
- pip

### Install dependencies

```bash
pip install streamlit pandas numpy matplotlib yfinance
```

### Step 1 — Download the data

```bash
python download_data.py
```

This creates the `data/` folder with three CSV files. An internet connection is required for this step only.

### Step 2 — Run the app

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501` in your browser.

> **Note:** The app reads from local CSV files and does not require an internet connection after the data download step.

---

## Python Notebook

The file `notebook.ipynb` contains the complete analytical workflow:

| Section | Content |
|---------|---------|
| 1 | Problem definition and target audience |
| 2 | Data loading and preview |
| 3 | Data cleaning and preparation |
| 4 | Five-factor DuPont calculation and verification |
| 4b | Industry benchmark definition and ROE quality scoring |
| 5 | Visualisations (ROE trend, factor breakdown, radar chart, ROE vs price) |
| 5b | Industry benchmark comparison chart |
| 5c | Sensitivity analysis — factor impact curves and cross-company comparison |
| 6 | Insights and interpretation |
| 7 | Limitations and responsible use |

Run all cells top to bottom in Jupyter Notebook or JupyterLab.

---

## Limitations

- `yfinance` provides approximately 4–5 years of financial statement history. A longer time series would reveal more structural trends.
- Apple's fiscal year ends in September; Microsoft and Tesla use December. Direct year-on-year comparisons should account for this timing difference.
- All figures are GAAP as reported. Adjusted/non-GAAP metrics used by analysts may differ.
- Industry benchmark figures are approximate and for educational reference only.
- DuPont decomposition is backward-looking and does not forecast future performance.

---

*Module: ACC102 · Xi'an Jiaotong-Liverpool University · Semester 2 2025-2026*
