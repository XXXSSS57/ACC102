"""
ACC102 Mini Assignment — Track 4
DuPont Analysis Interactive Tool  v2
Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.patches as mpatches
import warnings
warnings.filterwarnings("ignore")

# ── Page Config ─────────────────────────────────────────
st.set_page_config(
    page_title="DuPont Analyser",
    page_icon="📊",
    layout="wide"
)

COLORS = {"AAPL": "#555555", "MSFT": "#00A4EF", "TSLA": "#E31937"}
FACTOR_COLS   = ["TaxBurden","InterestBurden","EBITMargin","AssetTurnover","EquityMultiplier"]
FACTOR_LABELS = ["Tax Burden","Interest Burden","EBIT Margin","Asset Turnover","Equity Multiplier"]
FACTOR_DESC   = {
    "TaxBurden":        "Net Income / EBT — how much profit survives after tax.",
    "InterestBurden":   "EBT / EBIT — impact of interest payments on profit.",
    "EBITMargin":       "EBIT / Revenue — core operating profitability.",
    "AssetTurnover":    "Revenue / Total Assets — efficiency of asset use.",
    "EquityMultiplier": "Total Assets / Equity — degree of financial leverage.",
}

# ── Industry benchmarks (S&P 500 Tech sector approx. 5-yr avg) ──
INDUSTRY_BENCH = {
    "TaxBurden":        0.83,
    "InterestBurden":   0.94,
    "EBITMargin":       0.22,
    "AssetTurnover":    0.55,
    "EquityMultiplier": 2.80,
    "ROE":              0.28,
}

# ── Load & Cache Data ────────────────────────────────────
@st.cache_data
def load_data():
    inc   = pd.read_csv("data/income_statement.csv",   index_col="fiscal_year", parse_dates=True)
    bal   = pd.read_csv("data/balance_sheet.csv",      index_col="fiscal_year", parse_dates=True)
    price = pd.read_csv("data/stock_price_annual.csv", index_col="date",        parse_dates=True)

    inc_c = inc[["Total Revenue","EBIT","Pretax Income","Net Income","ticker"]].copy()
    inc_c.columns = ["Revenue","EBIT","EBT","NetIncome","ticker"]
    inc_c["year"] = inc_c.index.year

    bal_c = bal[["Total Assets","Common Stock Equity","ticker"]].copy()
    bal_c.columns = ["TotalAssets","Equity","ticker"]
    bal_c["year"] = bal_c.index.year

    df = pd.merge(inc_c.reset_index(drop=True),
                  bal_c.reset_index(drop=True),
                  on=["ticker","year"])
    df.dropna(subset=["Revenue","EBIT","EBT","NetIncome","TotalAssets","Equity"], inplace=True)
    df = df[df["Equity"] > 0].copy()

    df["TaxBurden"]        = df["NetIncome"]  / df["EBT"]
    df["InterestBurden"]   = df["EBT"]        / df["EBIT"]
    df["EBITMargin"]       = df["EBIT"]        / df["Revenue"]
    df["AssetTurnover"]    = df["Revenue"]     / df["TotalAssets"]
    df["EquityMultiplier"] = df["TotalAssets"] / df["Equity"]
    df["ROE"]              = df["NetIncome"]   / df["Equity"]

    df.sort_values(["ticker","year"], inplace=True)
    df.reset_index(drop=True, inplace=True)
    price["year"] = price.index.year
    return df, price

df, price = load_data()
all_tickers = sorted(df["ticker"].unique().tolist())
all_years   = sorted(df["year"].unique().tolist())

# ── ROE Quality Scoring ──────────────────────────────────
def roe_quality_score(row):
    """
    Score ROE quality 0-100 based on WHERE the ROE comes from.
    Higher weight on margin & turnover (operational), lower on leverage.
    Returns score, grade, colour, and one-line narrative.
    """
    # Normalise each factor vs industry benchmark
    margin_score   = min(row["EBITMargin"]       / INDUSTRY_BENCH["EBITMargin"],       2.0)
    turnover_score = min(row["AssetTurnover"]     / INDUSTRY_BENCH["AssetTurnover"],    2.0)
    tax_score      = min(row["TaxBurden"]         / INDUSTRY_BENCH["TaxBurden"],        2.0)
    interest_score = min(row["InterestBurden"]    / INDUSTRY_BENCH["InterestBurden"],   2.0)
    leverage_score = max(2.0 - row["EquityMultiplier"] / INDUSTRY_BENCH["EquityMultiplier"], 0.0)

    # Weighted composite (operational quality matters most)
    composite = (
        margin_score   * 0.35 +
        turnover_score * 0.25 +
        tax_score      * 0.15 +
        interest_score * 0.15 +
        leverage_score * 0.10
    ) * 50  # scale to 100

    composite = min(max(composite, 0), 100)

    # Dominant driver
    operational = row["EBITMargin"] * row["AssetTurnover"]
    leverage    = row["EquityMultiplier"]
    tax_drag    = row["TaxBurden"] * row["InterestBurden"]

    if row["EBITMargin"] > INDUSTRY_BENCH["EBITMargin"] * 1.3:
        driver = "strong operating margins"
    elif row["AssetTurnover"] > INDUSTRY_BENCH["AssetTurnover"] * 1.3:
        driver = "high asset efficiency"
    elif row["EquityMultiplier"] > INDUSTRY_BENCH["EquityMultiplier"] * 1.5:
        driver = "financial leverage (buybacks/debt)"
    else:
        driver = "balanced operational performance"

    if composite >= 70:
        grade, colour = "A  High Quality", "#27AE60"
        note = f"ROE is driven by {driver} — genuinely earned."
    elif composite >= 45:
        grade, colour = "B  Moderate Quality", "#F39C12"
        note = f"ROE is partially driven by {driver} — monitor leverage trends."
    else:
        grade, colour = "C  Low Quality", "#E74C3C"
        note = f"ROE is largely driven by {driver} — headline figure may be misleading."

    return round(composite, 1), grade, colour, note


# ── Sidebar ──────────────────────────────────────────────
with st.sidebar:
    st.title("📊 DuPont Analyser")
    st.caption("ACC102 Mini Assignment · Track 4")
    st.divider()
    selected_tickers = st.multiselect("Companies", all_tickers, default=all_tickers)
    year_range = st.slider(
        "Year Range",
        min_value=int(min(all_years)), max_value=int(max(all_years)),
        value=(int(min(all_years)), int(max(all_years)))
    )
    st.divider()
    st.caption("Data: Yahoo Finance via yfinance · Accessed April 2026")
    st.caption("Industry benchmark: S&P 500 Tech sector 5-yr average (approximate)")

if not selected_tickers:
    st.warning("Please select at least one company.")
    st.stop()

mask = (df["ticker"].isin(selected_tickers)) & \
       (df["year"] >= year_range[0]) & (df["year"] <= year_range[1])
dff  = df[mask].copy()

if dff.empty:
    st.warning("No data for selected filters.")
    st.stop()

# ── Header ───────────────────────────────────────────────
st.title("Five-Factor DuPont Analysis")
st.markdown(
    "Decompose **Return on Equity** into five drivers: "
    "*Tax Burden · Interest Burden · EBIT Margin · Asset Turnover · Equity Multiplier*"
)

# ── Metric Cards ─────────────────────────────────────────
latest = dff.sort_values("year").groupby("ticker").last().reset_index()
cols_m = st.columns(len(selected_tickers))
for col, (_, row) in zip(cols_m, latest.iterrows()):
    prev = dff[(dff["ticker"] == row["ticker"]) & (dff["year"] < row["year"])].sort_values("year")
    delta = f"{(row['ROE'] - prev.iloc[-1]['ROE']):.1%}" if not prev.empty else None
    col.metric(
        label=f"{row['ticker']}  ROE ({int(row['year'])})",
        value=f"{row['ROE']:.1%}",
        delta=delta
    )

st.divider()

# ── Tabs ─────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 ROE Trend",
    "🔍 Factor Breakdown",
    "🏆 ROE Quality Scorecard",
    "📊 Industry Benchmark",
    "⚙️ What-If Simulator",
    "🌊 Attribution Waterfall",
])

# ════════════════════════════════════════════════════════
# TAB 1 — ROE Trend + Radar
# ════════════════════════════════════════════════════════
with tab1:
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("ROE Over Time")
        fig, ax = plt.subplots(figsize=(8, 4))
        for ticker in selected_tickers:
            d = dff[dff["ticker"] == ticker].sort_values("year")
            ax.plot(d["year"], d["ROE"], marker="o", linewidth=2.5,
                    color=COLORS.get(ticker,"steelblue"), label=ticker)
            if not d.empty:
                last = d.iloc[-1]
                ax.annotate(f"{last['ROE']:.1%}",
                            xy=(last["year"], last["ROE"]),
                            xytext=(4,4), textcoords="offset points",
                            fontsize=9, color=COLORS.get(ticker,"steelblue"))
        # Industry benchmark line
        ax.axhline(INDUSTRY_BENCH["ROE"], color="orange", linewidth=1.2,
                   linestyle="--", label=f"Industry avg ({INDUSTRY_BENCH['ROE']:.0%})")
        ax.axhline(0, color="gray", linewidth=0.8, linestyle=":")
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax.set_xlabel("Fiscal Year")
        ax.set_ylabel("ROE")
        ax.spines[["top","right"]].set_visible(False)
        ax.legend(fontsize=9)
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    with col_right:
        st.subheader("Factor Radar (Latest Year)")
        latest_r = dff.sort_values("year").groupby("ticker").last().reset_index()
        norm = latest_r[FACTOR_COLS].copy()
        for col in FACTOR_COLS:
            mn, mx = norm[col].min(), norm[col].max()
            norm[col] = (norm[col] - mn) / (mx - mn + 1e-9)

        N      = len(FACTOR_COLS)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist()
        angles += angles[:1]

        fig2, ax2 = plt.subplots(figsize=(4.5,4.5), subplot_kw=dict(polar=True))
        for idx, row in norm.iterrows():
            ticker = latest_r.loc[idx,"ticker"]
            if ticker not in selected_tickers:
                continue
            vals = row[FACTOR_COLS].tolist() + [row[FACTOR_COLS[0]]]
            ax2.plot(angles, vals, linewidth=2,
                     color=COLORS.get(ticker,"steelblue"), label=ticker)
            ax2.fill(angles, vals, alpha=0.12, color=COLORS.get(ticker,"steelblue"))

        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(["Tax\nBurden","Interest\nBurden","EBIT\nMargin",
                              "Asset\nTurnover","Equity\nMultiplier"], fontsize=9)
        ax2.set_yticklabels([])
        ax2.legend(loc="upper right", bbox_to_anchor=(1.35,1.1), fontsize=9)
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close()
        st.caption("Normalised across selected companies. Shape reveals strategy, not absolute performance.")

# ════════════════════════════════════════════════════════
# TAB 2 — Factor Breakdown
# ════════════════════════════════════════════════════════
with tab2:
    st.subheader("Five-Factor Breakdown by Company")
    chosen     = st.selectbox("Highlight a factor", FACTOR_LABELS, key="factor_select")
    chosen_col = FACTOR_COLS[FACTOR_LABELS.index(chosen)]
    st.info(f"**{chosen}:** {FACTOR_DESC[chosen_col]}")

    fig3, axes = plt.subplots(1, len(selected_tickers),
                              figsize=(5*len(selected_tickers), 5), sharey=False)
    if len(selected_tickers) == 1:
        axes = [axes]

    fc = ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B2"]
    for ax, ticker in zip(axes, selected_tickers):
        d = dff[dff["ticker"]==ticker].sort_values("year")
        x = np.arange(len(d))
        w = 0.15
        for i, (fcol, flabel, color) in enumerate(zip(FACTOR_COLS, FACTOR_LABELS, fc)):
            alpha = 1.0 if fcol == chosen_col else 0.30
            ax.bar(x + i*w, d[fcol], w, label=flabel, color=color, alpha=alpha,
                   edgecolor="black" if fcol==chosen_col else "white",
                   linewidth=0.8 if fcol==chosen_col else 0)
        # Industry benchmark for chosen factor
        ax.axhline(INDUSTRY_BENCH[chosen_col], color="orange",
                   linewidth=1.2, linestyle="--", label="Industry avg")
        ax.set_title(ticker, fontweight="bold", color=COLORS.get(ticker,"black"))
        ax.set_xticks(x + w*2)
        ax.set_xticklabels(d["year"].tolist(), rotation=45, fontsize=8)
        ax.axhline(1, color="gray", linewidth=0.7, linestyle=":")
        ax.spines[["top","right"]].set_visible(False)
    axes[0].legend(fontsize=7, loc="upper left")
    fig3.suptitle(f"Five DuPont Factors  ·  Highlighted: {chosen}", fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close()

    st.divider()
    show_cols = ["ticker","year"] + FACTOR_COLS + ["ROE"]
    st.dataframe(dff[show_cols].set_index(["ticker","year"]).style.format("{:.3f}"),
                 use_container_width=True)
    st.download_button("⬇️ Download CSV", dff[show_cols].to_csv(index=False),
                       file_name="dupont_factors.csv", mime="text/csv")

# ════════════════════════════════════════════════════════
# TAB 3 — ROE Quality Scorecard
# ════════════════════════════════════════════════════════
with tab3:
    st.subheader("🏆 ROE Quality Scorecard")
    st.markdown(
        "Same ROE, different story. This scorecard measures **where** ROE comes from — "
        "operational excellence vs financial engineering. "
        "Higher score = more sustainably earned."
    )
    st.divider()

    latest_s = dff.sort_values("year").groupby("ticker").last().reset_index()

    for _, row in latest_s.iterrows():
        ticker = row["ticker"]
        score, grade, colour, note = roe_quality_score(row)

        with st.container():
            c1, c2, c3 = st.columns([1, 2, 3])

            with c1:
                st.markdown(f"### {ticker}")
                st.markdown(f"**ROE: {row['ROE']:.1%}**")
                st.markdown(f"**Year: {int(row['year'])}**")

            with c2:
                # Gauge-style score display
                fig_g, ax_g = plt.subplots(figsize=(3, 1.8))
                # Background bar
                ax_g.barh(0, 100, height=0.5, color="#ECECEC", zorder=1)
                ax_g.barh(0, score, height=0.5, color=colour, zorder=2)
                ax_g.set_xlim(0, 100)
                ax_g.set_ylim(-0.5, 0.8)
                ax_g.axis("off")
                ax_g.text(score/2, 0, f"{score:.0f}", ha="center", va="center",
                          fontsize=14, fontweight="bold", color="white", zorder=3)
                ax_g.text(50, 0.55, grade, ha="center", va="bottom",
                          fontsize=9, fontweight="bold", color=colour)
                ax_g.text(0,  -0.35, "0", ha="center", fontsize=7, color="gray")
                ax_g.text(50, -0.35, "50", ha="center", fontsize=7, color="gray")
                ax_g.text(100,-0.35, "100", ha="center", fontsize=7, color="gray")
                plt.tight_layout()
                st.pyplot(fig_g)
                plt.close()

            with c3:
                st.markdown(f"**Assessment:** {note}")
                # Mini factor table
                factor_vs = {
                    "Factor":    FACTOR_LABELS,
                    "Value":     [f"{row[f]:.3f}" for f in FACTOR_COLS],
                    "Industry":  [f"{INDUSTRY_BENCH[f]:.3f}" for f in FACTOR_COLS],
                    "vs Avg":    ["✅ Above" if row[f] >= INDUSTRY_BENCH[f] else "⚠️ Below"
                                  for f in FACTOR_COLS],
                }
                st.dataframe(pd.DataFrame(factor_vs).set_index("Factor"),
                             use_container_width=True, hide_index=False)
            st.divider()

# ════════════════════════════════════════════════════════
# TAB 4 — Industry Benchmark
# ════════════════════════════════════════════════════════
with tab4:
    st.subheader("📊 Industry Benchmark Comparison")
    st.markdown(
        "How do AAPL, MSFT, and TSLA compare against the **S&P 500 Tech sector average**? "
        "Orange dashed line = industry benchmark."
    )

    latest_b = dff.sort_values("year").groupby("ticker").last().reset_index()

    fig_b, axes_b = plt.subplots(2, 3, figsize=(13, 8))
    plot_items = FACTOR_COLS + ["ROE"]
    plot_names = FACTOR_LABELS + ["ROE"]

    for ax, fcol, fname in zip(axes_b.flat, plot_items, plot_names):
        vals    = [latest_b.loc[latest_b["ticker"]==t, fcol].values[0]
                   if t in latest_b["ticker"].values else 0
                   for t in selected_tickers]
        colors  = [COLORS.get(t,"steelblue") for t in selected_tickers]
        bars    = ax.bar(selected_tickers, vals, color=colors, alpha=0.85, width=0.5)
        bench   = INDUSTRY_BENCH[fcol]
        ax.axhline(bench, color="orange", linewidth=1.5, linestyle="--", label=f"Industry: {bench:.3f}")

        # Value labels on bars
        for bar, val in zip(bars, vals):
            fmt = f"{val:.1%}" if fcol == "ROE" else f"{val:.3f}"
            ax.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height() + max(vals)*0.02,
                    fmt, ha="center", fontsize=9, fontweight="bold")

        ax.set_title(fname, fontweight="bold")
        ax.spines[["top","right"]].set_visible(False)
        ax.legend(fontsize=8)
        if fcol == "ROE":
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

    fig_b.suptitle("Latest Year vs S&P 500 Tech Sector Benchmark",
                   fontweight="bold", fontsize=13)
    plt.tight_layout()
    st.pyplot(fig_b)
    plt.close()

    st.caption(
        "⚠️ Industry benchmark figures are approximate 5-year averages for the S&P 500 "
        "Information Technology sector. For professional use, cross-reference with "
        "Bloomberg or FactSet sector data."
    )

    # Heatmap: above/below benchmark
    st.divider()
    st.markdown("**Above / Below Industry Benchmark — All Years**")
    heat_data = []
    for ticker in selected_tickers:
        d = dff[dff["ticker"]==ticker].sort_values("year")
        for _, row in d.iterrows():
            entry = {"Ticker": ticker, "Year": int(row["year"])}
            for fcol, fname in zip(FACTOR_COLS, FACTOR_LABELS):
                entry[fname] = round((row[fcol] - INDUSTRY_BENCH[fcol]) / INDUSTRY_BENCH[fcol] * 100, 1)
            heat_data.append(entry)

    heat_df = pd.DataFrame(heat_data).set_index(["Ticker","Year"])
    st.dataframe(
        heat_df.style
            .format("{:+.1f}%")
            .background_gradient(cmap="RdYlGn", axis=None, vmin=-50, vmax=50),
        use_container_width=True
    )
    st.caption("Values show % deviation from industry benchmark. Green = above, Red = below.")

# ════════════════════════════════════════════════════════
# TAB 5 — What-If Simulator
# ════════════════════════════════════════════════════════
with tab5:
    st.subheader("⚙️ What-If Scenario Simulator")
    st.markdown(
        "Adjust any factor to see how ROE responds. "
        "The **sensitivity chart** below shows which factor has the most leverage on ROE."
    )

    sim_ticker = st.selectbox("Company", selected_tickers, key="sim_ticker")
    base_row   = dff[dff["ticker"]==sim_ticker].sort_values("year").iloc[-1]
    base_year  = int(base_row["year"])

    st.markdown(f"**Base year: {base_year}  ·  Actual ROE: {base_row['ROE']:.2%}**")
    st.divider()

    col1, col2 = st.columns(2)
    sliders = {}
    for i, (fcol, flabel) in enumerate(zip(FACTOR_COLS, FACTOR_LABELS)):
        base_val   = float(base_row[fcol])
        target_col = col1 if i % 2 == 0 else col2
        with target_col:
            sliders[fcol] = st.slider(
                f"{flabel}  (base: {base_val:.3f})",
                min_value=round(max(base_val*0.5, 0.01), 3),
                max_value=round(base_val*2.0+0.5,        3),
                value=round(base_val, 3),
                step=0.01,
                key=f"slider_{fcol}"
            )

    sim_roe   = 1.0
    for fcol in FACTOR_COLS:
        sim_roe *= sliders[fcol]
    delta_roe = sim_roe - float(base_row["ROE"])

    st.divider()
    r1, r2, r3 = st.columns(3)
    r1.metric("Actual ROE",    f"{base_row['ROE']:.2%}")
    r2.metric("Simulated ROE", f"{sim_roe:.2%}", delta=f"{delta_roe:+.2%}")
    r3.metric("Change", f"{'▲' if delta_roe>=0 else '▼'} {abs(delta_roe):.2%}",
              delta="Improvement" if delta_roe>=0 else "Decline")

    # Actual vs simulated bar chart
    st.divider()
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Factor comparison: Actual vs Simulated**")
        fig4, ax4 = plt.subplots(figsize=(6, 3.5))
        x4 = np.arange(len(FACTOR_COLS))
        ax4.bar(x4-0.2, [float(base_row[f]) for f in FACTOR_COLS], 0.35,
                label="Actual", color="#4C72B0", alpha=0.85)
        ax4.bar(x4+0.2, [sliders[f] for f in FACTOR_COLS], 0.35,
                label="Simulated", color="#DD8452", alpha=0.85)
        ax4.set_xticks(x4)
        ax4.set_xticklabels(FACTOR_LABELS, fontsize=8, rotation=15, ha="right")
        ax4.axhline(1, color="gray", linewidth=0.7, linestyle="--")
        ax4.spines[["top","right"]].set_visible(False)
        ax4.legend(fontsize=9)
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close()

    with col_b:
        # ── Sensitivity Analysis ──────────────────────────
        st.markdown("**Factor Sensitivity: Impact on ROE (±50% change)**")
        pct_range  = np.linspace(-0.5, 0.5, 50)
        fig_s, ax_s = plt.subplots(figsize=(6, 3.5))

        for fcol, flabel, color in zip(FACTOR_COLS, FACTOR_LABELS,
                                        ["#4C72B0","#DD8452","#55A868","#C44E52","#8172B2"]):
            roe_vals = []
            base_f   = float(base_row[fcol])
            for pct in pct_range:
                test = 1.0
                for other in FACTOR_COLS:
                    test *= (float(base_row[other]) * (1+pct) if other==fcol
                             else float(base_row[other]))
                roe_vals.append(test)
            ax_s.plot(pct_range*100, roe_vals, linewidth=2,
                      color=color, label=flabel)

        ax_s.axvline(0, color="gray", linewidth=0.8, linestyle="--")
        ax_s.axhline(float(base_row["ROE"]), color="black",
                     linewidth=0.8, linestyle=":", label="Base ROE")
        ax_s.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax_s.set_xlabel("Factor change (%)")
        ax_s.set_ylabel("Resulting ROE")
        ax_s.spines[["top","right"]].set_visible(False)
        ax_s.legend(fontsize=7, loc="upper left")
        ax_s.set_title(f"{sim_ticker} — ROE Sensitivity to Each Factor",
                       fontsize=10, fontweight="bold")
        plt.tight_layout()
        st.pyplot(fig_s)
        plt.close()

    st.caption(
        "💡 Steeper slope in the sensitivity chart = that factor has more leverage on ROE. "
        "Compare slopes across companies to see which business model is most sensitive to margin vs leverage changes."
    )

    # Cross-company sensitivity comparison
    st.divider()
    st.markdown("**Cross-Company Sensitivity Comparison** — which factor matters most for each company?")

    fig_cc, axes_cc = plt.subplots(1, len(selected_tickers),
                                    figsize=(5*len(selected_tickers), 4), sharey=False)
    if len(selected_tickers)==1:
        axes_cc = [axes_cc]

    for ax_cc, ticker in zip(axes_cc, selected_tickers):
        t_row = dff[dff["ticker"]==ticker].sort_values("year").iloc[-1]
        slopes = []
        for fcol in FACTOR_COLS:
            # Slope = ΔROE for +10% change in factor
            base_roe = float(t_row["ROE"])
            test_roe = 1.0
            for other in FACTOR_COLS:
                test_roe *= (float(t_row[other])*1.10 if other==fcol
                             else float(t_row[other]))
            slopes.append(test_roe - base_roe)

        colors_bar = ["#55A868" if s>=0 else "#C44E52" for s in slopes]
        ax_cc.barh(FACTOR_LABELS, slopes, color=colors_bar, alpha=0.85)
        ax_cc.axvline(0, color="gray", linewidth=0.8)
        ax_cc.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax_cc.set_title(ticker, fontweight="bold", color=COLORS.get(ticker,"black"))
        ax_cc.spines[["top","right"]].set_visible(False)

    fig_cc.suptitle("ROE Impact of +10% Change in Each Factor (Latest Year)",
                    fontweight="bold")
    plt.tight_layout()
    st.pyplot(fig_cc)
    plt.close()

# ════════════════════════════════════════════════════════
# TAB 6 — Attribution Waterfall
# ════════════════════════════════════════════════════════
with tab6:
    st.subheader("🌊 ROE Attribution — What Changed Between Two Years?")
    st.markdown(
        "Select a company and two years. The waterfall shows "
        "**how much each factor contributed** to the ROE change."
    )

    w1, w2, w3   = st.columns(3)
    wat_ticker   = w1.selectbox("Company", selected_tickers, key="wat_ticker")
    ticker_years = sorted(df[df["ticker"]==wat_ticker]["year"].unique().tolist())

    if len(ticker_years) < 2:
        st.warning("Need at least 2 years of data for this company.")
    else:
        year_a      = w2.selectbox("From Year", ticker_years[:-1], index=0, key="year_a")
        year_b_opts = [y for y in ticker_years if y > year_a]
        year_b      = w3.selectbox("To Year", year_b_opts,
                                   index=len(year_b_opts)-1, key="year_b")

        row_a = df[(df["ticker"]==wat_ticker)&(df["year"]==year_a)].iloc[0]
        row_b = df[(df["ticker"]==wat_ticker)&(df["year"]==year_b)].iloc[0]

        roe_a        = float(row_a["ROE"])
        roe_b        = float(row_b["ROE"])
        actual_delta = roe_b - roe_a

        # Additive attribution
        contribs = {}
        for fcol in FACTOR_COLS:
            others = 1.0
            for other in FACTOR_COLS:
                if other != fcol:
                    others *= float(row_a[other])
            contribs[fcol] = (float(row_b[fcol]) - float(row_a[fcol])) * others

        raw_sum  = sum(contribs.values())
        scale    = actual_delta / raw_sum if abs(raw_sum) > 1e-9 else 1.0
        contribs = {k: v*scale for k, v in contribs.items()}

        # Waterfall
        labels     = [f"ROE {year_a}"] + FACTOR_LABELS + [f"ROE {year_b}"]
        values     = [roe_a] + list(contribs.values()) + [roe_b]
        running    = roe_a
        bottoms    = [0]
        bar_colors = ["#4C72B0"]
        for v in contribs.values():
            bottoms.append(running if v>=0 else running+v)
            bar_colors.append("#55A868" if v>=0 else "#C44E52")
            running += v
        bottoms.append(0)
        bar_colors.append("#4C72B0")

        m1, m2, m3 = st.columns(3)
        m1.metric(f"ROE {year_a}", f"{roe_a:.2%}")
        m2.metric(f"ROE {year_b}", f"{roe_b:.2%}", delta=f"{actual_delta:+.2%}")
        biggest = max(contribs, key=lambda k: abs(contribs[k]))
        m3.metric("Biggest driver",
                  FACTOR_LABELS[FACTOR_COLS.index(biggest)],
                  delta=f"{contribs[biggest]:+.2%}")

        st.divider()

        fig5, ax5 = plt.subplots(figsize=(10, 5))
        for i, (lbl, val, bot, clr) in enumerate(zip(labels, values, bottoms, bar_colors)):
            ax5.bar(i, abs(val), bottom=bot, color=clr, alpha=0.85,
                    edgecolor="white", linewidth=0.5)
            sign = "+" if val >= 0 else ""
            fmt  = f"{sign}{val:.2%}" if i not in (0, len(labels)-1) else f"{val:.2%}"
            ax5.text(i, bot+abs(val)/2, fmt,
                     ha="center", va="center", fontsize=8.5,
                     fontweight="bold", color="white")

        run2 = roe_a
        for i in range(1, len(FACTOR_COLS)+1):
            ax5.plot([i-0.4, i+0.4], [run2, run2],
                     color="gray", linewidth=0.8, linestyle="--")
            run2 += list(contribs.values())[i-1]

        ax5.set_xticks(range(len(labels)))
        ax5.set_xticklabels(labels, rotation=20, ha="right", fontsize=9)
        ax5.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
        ax5.spines[["top","right"]].set_visible(False)
        ax5.set_title(
            f"{wat_ticker}  ROE Attribution: {year_a} → {year_b}  "
            f"({'▲' if actual_delta>=0 else '▼'} {actual_delta:+.2%})",
            fontweight="bold"
        )
        ax5.legend(handles=[
            mpatches.Patch(color="#55A868", alpha=0.85, label="Positive contribution"),
            mpatches.Patch(color="#C44E52", alpha=0.85, label="Negative contribution"),
            mpatches.Patch(color="#4C72B0", alpha=0.85, label="ROE level"),
        ], fontsize=8)
        plt.tight_layout()
        st.pyplot(fig5)
        plt.close()

        st.divider()
        st.markdown("**Factor values: comparison**")
        comp_data = {
            "Factor":    FACTOR_LABELS,
            str(year_a): [f"{float(row_a[f]):.3f}" for f in FACTOR_COLS],
            str(year_b): [f"{float(row_b[f]):.3f}" for f in FACTOR_COLS],
            "Change":    [f"{contribs[f]:+.2%}"    for f in FACTOR_COLS],
        }
        st.dataframe(pd.DataFrame(comp_data).set_index("Factor"), use_container_width=True)

# ── Footer ───────────────────────────────────────────────
st.divider()
st.caption(
    "ACC102 Mini Assignment · Xi'an Jiaotong-Liverpool University · "
    "Data: Yahoo Finance via yfinance · Accessed April 2026 · "
    "Industry benchmark: S&P 500 IT sector approximate 5-yr average"
)
