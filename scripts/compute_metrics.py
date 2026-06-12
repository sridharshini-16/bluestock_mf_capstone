import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

DATA_PATH = "../data/raw/"
OUTPUT_PATH = "../data/processed/"
CHARTS_PATH = "../notebooks/15_charts/"
RF = 0.065  # Risk-free rate 6.5%
TRADING_DAYS = 252

import os
os.makedirs(OUTPUT_PATH, exist_ok=True)
os.makedirs(CHARTS_PATH, exist_ok=True)

# ── Load data ────────────────────────────────────────────────────────────────
print("Loading data...")
fund_master = pd.read_csv(DATA_PATH + "01_fund_master.csv", parse_dates=["launch_date"])
nav_history  = pd.read_csv(DATA_PATH + "02_nav_history.csv", parse_dates=["date"])
benchmark    = pd.read_csv(DATA_PATH + "10_benchmark_indices.csv", parse_dates=["date"])

nav_history.sort_values(["amfi_code","date"], inplace=True)
print(f"NAV rows: {len(nav_history):,}  |  Funds: {nav_history['amfi_code'].nunique()}")

# ── STEP 1: Daily returns ─────────────────────────────────────────────────────
nav_history["daily_return"] = nav_history.groupby("amfi_code")["nav"].pct_change()
nav_history.dropna(subset=["daily_return"], inplace=True)

print("\n── Daily Return Distribution (sample) ──")
ret_desc = nav_history.groupby("amfi_code")["daily_return"].describe().round(6)
print(ret_desc.head(5).to_string())
print(f"\nMean of all daily returns : {nav_history['daily_return'].mean():.5f}")
print(f"Std  of all daily returns : {nav_history['daily_return'].std():.5f}")
print(f"Min  daily return         : {nav_history['daily_return'].min():.5f}")
print(f"Max  daily return         : {nav_history['daily_return'].max():.5f}")

# ── STEP 2: CAGR helper ───────────────────────────────────────────────────────
def cagr(nav_series, years):
    end_date = nav_series.index.max()
    start_date = end_date - pd.DateOffset(years=years)
    subset = nav_series[nav_series.index >= start_date]
    if len(subset) < 2:
        return np.nan
    nav_end   = subset.iloc[-1]
    nav_start = subset.iloc[0]
    actual_years = (subset.index[-1] - subset.index[0]).days / 365.25
    if actual_years <= 0 or nav_start <= 0:
        return np.nan
    return (nav_end / nav_start) ** (1 / actual_years) - 1

print("\n── Computing CAGR for all funds ──")
cagr_records = []
for code, grp in nav_history.groupby("amfi_code"):
    nav_ts = grp.set_index("date")["nav"]
    cagr_records.append({
        "amfi_code"  : code,
        "cagr_1yr"   : cagr(nav_ts, 1),
        "cagr_3yr"   : cagr(nav_ts, 3),
        "cagr_5yr"   : cagr(nav_ts, 5),
    })

cagr_df = pd.DataFrame(cagr_records).merge(
    fund_master[["amfi_code","scheme_name","fund_house","category","expense_ratio_pct"]], on="amfi_code")

# ── STEP 3: Sharpe Ratio ──────────────────────────────────────────────────────
print("── Computing Sharpe & Sortino ──")
risk_records = []
for code, grp in nav_history.groupby("amfi_code"):
    r = grp["daily_return"].dropna()
    if len(r) < 30:
        continue
    rf_daily     = RF / TRADING_DAYS
    excess       = r - rf_daily
    sharpe       = (excess.mean() / r.std()) * np.sqrt(TRADING_DAYS) if r.std() > 0 else np.nan
    downside     = r[r < 0]
    sortino_denom = downside.std() if len(downside) > 1 else np.nan
    sortino      = (excess.mean() / sortino_denom) * np.sqrt(TRADING_DAYS) if sortino_denom and sortino_denom > 0 else np.nan
    risk_records.append({"amfi_code": code, "sharpe_ratio": sharpe, "sortino_ratio": sortino, "ann_vol": r.std()*np.sqrt(TRADING_DAYS)})

risk_df = pd.DataFrame(risk_records)

# ── STEP 4: Alpha & Beta (OLS vs NIFTY 100) ──────────────────────────────────
print("── Computing Alpha & Beta ──")
nifty100 = benchmark[benchmark["index_name"]=="NIFTY100"].set_index("date")["close_value"].sort_index()
nifty100_ret = nifty100.pct_change().dropna()

ab_records = []
for code, grp in nav_history.groupby("amfi_code"):
    fund_ret = grp.set_index("date")["daily_return"].dropna()
    aligned = pd.concat([fund_ret.rename("fund"), nifty100_ret.rename("bench")], axis=1).dropna()
    if len(aligned) < 30:
        continue
    slope, intercept, r_val, p_val, se = stats.linregress(aligned["bench"], aligned["fund"])
    ab_records.append({
        "amfi_code": code,
        "beta"      : round(slope, 4),
        "alpha_daily": round(intercept, 6),
        "alpha_ann" : round(intercept * TRADING_DAYS, 4),
        "r_squared" : round(r_val**2, 4),
        "p_value"   : round(p_val, 6),
    })

ab_df = pd.DataFrame(ab_records)
ab_df = ab_df.merge(fund_master[["amfi_code","scheme_name","fund_house","category"]], on="amfi_code")

print(f"Alpha-Beta computed for {len(ab_df)} funds")
print(ab_df[["scheme_name","alpha_ann","beta","r_squared"]].to_string())

# ── STEP 5: Maximum Drawdown ──────────────────────────────────────────────────
print("\n── Computing Maximum Drawdown ──")
dd_records = []
for code, grp in nav_history.groupby("amfi_code"):
    nav_ts  = grp.set_index("date")["nav"].sort_index()
    running_max = nav_ts.cummax()
    drawdown    = nav_ts / running_max - 1
    max_dd      = drawdown.min()
    dd_end      = drawdown.idxmin()
    # Find where the peak occurred before the trough
    peak_idx = nav_ts[:dd_end].idxmax()
    recovery_candidates = nav_ts[dd_end:][nav_ts[dd_end:] >= nav_ts[peak_idx]]
    recovery_date = recovery_candidates.index[0] if len(recovery_candidates) > 0 else None
    dd_records.append({
        "amfi_code"   : code,
        "max_drawdown": round(max_dd*100, 4),
        "peak_date"   : peak_idx,
        "trough_date" : dd_end,
        "recovery_date": recovery_date,
    })

dd_df = pd.DataFrame(dd_records).merge(fund_master[["amfi_code","scheme_name","fund_house"]], on="amfi_code")
print(dd_df[["scheme_name","max_drawdown","peak_date","trough_date"]].to_string())

# ── STEP 6: Fund Scorecard ────────────────────────────────────────────────────
print("\n── Building Fund Scorecard ──")
# Merge all metrics
scorecard = cagr_df[["amfi_code","scheme_name","fund_house","category","cagr_3yr","expense_ratio_pct"]].merge(
    risk_df[["amfi_code","sharpe_ratio"]], on="amfi_code").merge(
    ab_df[["amfi_code","alpha_ann"]], on="amfi_code").merge(
    dd_df[["amfi_code","max_drawdown"]], on="amfi_code")

def rank_col(s, ascending=False):
    """Rank 1=best; ascending=False means higher value = better rank"""
    return s.rank(ascending=ascending, method='min')

n = len(scorecard)
scorecard["rank_3yr"]     = rank_col(scorecard["cagr_3yr"],       ascending=False)  # higher better
scorecard["rank_sharpe"]  = rank_col(scorecard["sharpe_ratio"],    ascending=False)  # higher better
scorecard["rank_alpha"]   = rank_col(scorecard["alpha_ann"],       ascending=False)  # higher better
scorecard["rank_expense"] = rank_col(scorecard["expense_ratio_pct"], ascending=True) # lower better (inverse)
scorecard["rank_mdd"]     = rank_col(scorecard["max_drawdown"],    ascending=False)  # less negative = higher value = better rank

# Normalize ranks 0-100 (1 = 100, n = 0)
def norm_rank(rank_series, n):
    return (n - rank_series) / (n - 1) * 100

scorecard["norm_3yr"]     = norm_rank(scorecard["rank_3yr"],     n)
scorecard["norm_sharpe"]  = norm_rank(scorecard["rank_sharpe"],  n)
scorecard["norm_alpha"]   = norm_rank(scorecard["rank_alpha"],   n)
scorecard["norm_expense"] = norm_rank(scorecard["rank_expense"], n)
scorecard["norm_mdd"]     = norm_rank(scorecard["rank_mdd"],     n)

scorecard["composite_score"] = (
    0.30 * scorecard["norm_3yr"] +
    0.25 * scorecard["norm_sharpe"] +
    0.20 * scorecard["norm_alpha"] +
    0.15 * scorecard["norm_expense"] +
    0.10 * scorecard["norm_mdd"]
).round(2)

scorecard.sort_values("composite_score", ascending=False, inplace=True)
scorecard["scorecard_rank"] = range(1, len(scorecard)+1)

print("\nTop 10 funds by scorecard:")
print(scorecard[["scorecard_rank","scheme_name","composite_score","cagr_3yr","sharpe_ratio","alpha_ann","max_drawdown"]].head(10).to_string())

# ── STEP 7: Benchmark Comparison Chart ───────────────────────────────────────
print("\n── Generating Benchmark Comparison Chart ──")

# Get top 5 funds from scorecard (direct plans preferred)
top5_codes = scorecard.head(5)["amfi_code"].tolist()
top5_names = scorecard.head(5).set_index("amfi_code")["scheme_name"].to_dict()

# 3-year window
end_dt   = nav_history["date"].max()
start_dt = end_dt - pd.DateOffset(years=3)

fig, axes = plt.subplots(2, 1, figsize=(14, 12))
plt.suptitle("Top 5 Funds vs Nifty 50 & Nifty 100 – 3-Year Performance", fontsize=15, fontweight='bold')

ax = axes[0]
colors = plt.cm.tab10(np.linspace(0, 1, 7))

te_records = []
for i, code in enumerate(top5_codes):
    fund_nav = nav_history[(nav_history["amfi_code"]==code) & (nav_history["date"]>=start_dt)].set_index("date")["nav"]
    if len(fund_nav) < 2:
        continue
    normalized = fund_nav / fund_nav.iloc[0] * 100
    short_name = top5_names[code].split(" - ")[0][:30]
    ax.plot(normalized.index, normalized.values, label=short_name, color=colors[i], linewidth=1.8)

    # Tracking error vs Nifty 100
    fund_ret = fund_nav.pct_change().dropna()
    bench_ret= nifty100.pct_change().dropna()
    aligned  = pd.concat([fund_ret.rename("f"), bench_ret.rename("b")], axis=1).dropna()
    te = (aligned["f"] - aligned["b"]).std() * np.sqrt(TRADING_DAYS) * 100
    te_records.append({"amfi_code": code, "scheme_name": top5_names[code], "tracking_error_vs_nifty100_pct": round(te, 4)})

# Benchmark lines
for idx_name, label, color in [("NIFTY50","Nifty 50","black"),("NIFTY100","Nifty 100","grey")]:
    idx_ts = benchmark[(benchmark["index_name"]==idx_name) & (benchmark["date"]>=start_dt)].set_index("date")["close_value"]
    if len(idx_ts) > 0:
        normalized = idx_ts / idx_ts.iloc[0] * 100
        ax.plot(normalized.index, normalized.values, label=label, color=color, linewidth=2.5, linestyle='--')

ax.set_title("Indexed Returns (Base = 100)", fontsize=12)
ax.set_ylabel("Indexed Value")
ax.legend(fontsize=8, loc='upper left')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
ax.grid(True, alpha=0.3)

# Tracking error bar chart
ax2 = axes[1]
te_df = pd.DataFrame(te_records)
te_df["short_name"] = te_df["scheme_name"].str.split(" - ").str[0].str[:30]
ax2.barh(te_df["short_name"], te_df["tracking_error_vs_nifty100_pct"], color=colors[:len(te_df)])
ax2.set_xlabel("Tracking Error vs Nifty 100 (%, Annualised)")
ax2.set_title("Tracking Error vs Nifty 100 – Top 5 Funds", fontsize=12)
ax2.grid(True, alpha=0.3, axis='x')
for bar, val in zip(ax2.patches, te_df["tracking_error_vs_nifty100_pct"]):
    ax2.text(bar.get_width()+0.05, bar.get_y()+bar.get_height()/2, f"{val:.2f}%", va='center', fontsize=9)

plt.tight_layout()
chart_path = CHARTS_PATH + "benchmark_comparison.png"
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"Chart saved → {chart_path}")

# ── Save CSVs ─────────────────────────────────────────────────────────────────
cols_scorecard = ["scorecard_rank","amfi_code","scheme_name","fund_house","category",
                  "composite_score","cagr_3yr",
                  "sharpe_ratio","alpha_ann","expense_ratio_pct","max_drawdown"]
scorecard[cols_scorecard].to_csv(OUTPUT_PATH+"fund_scorecard.csv", index=False)
print(f"Saved fund_scorecard.csv ({len(scorecard)} rows)")

ab_df.to_csv(OUTPUT_PATH+"alpha_beta.csv", index=False)
print(f"Saved alpha_beta.csv ({len(ab_df)} rows)")

pd.DataFrame(te_records).to_csv(OUTPUT_PATH+"tracking_error.csv", index=False)
print(f"Saved tracking_error.csv ({len(te_records)} rows)")

cagr_df.to_csv(OUTPUT_PATH+"cagr_comparison.csv", index=False)
print("Saved cagr_comparison.csv")

dd_df.to_csv(OUTPUT_PATH+"max_drawdown.csv", index=False)
print("Saved max_drawdown.csv")

print("\n✅ All outputs generated successfully!")
