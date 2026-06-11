"""
day6_analytics.py  — Generates all Day 6 deliverables
  • reports/var_cvar_report.csv
  • reports/rolling_sharpe_chart.png
Bluestock MF Capstone
"""

import os, sqlite3, warnings
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

warnings.filterwarnings("ignore")

BASE   = os.path.dirname(os.path.abspath(__file__))
DB     = os.path.join(BASE, "bluestock_mf.db")
RDIR   = os.path.join(BASE, "reports")
os.makedirs(RDIR, exist_ok=True)

db = sqlite3.connect(DB)

# ── Load data ────────────────────────────────────────────────
nav  = pd.read_sql("SELECT amfi_code, date, nav FROM nav_history", db, parse_dates=["date"])
perf = pd.read_sql("SELECT amfi_code, scheme_name, sharpe_ratio, risk_grade, category FROM scheme_performance", db)
ph   = pd.read_sql("SELECT amfi_code, sector, weight_pct FROM portfolio_holdings", db)
db.close()

nav.sort_values(["amfi_code", "date"], inplace=True)

# ═══════════════════════════════════════════════════════════════
# 1  VAR & CVAR (95%) for all 40 schemes
# ═══════════════════════════════════════════════════════════════
print("Computing VaR / CVaR ...")

records = []
for code, grp in nav.groupby("amfi_code"):
    r = grp["nav"].pct_change().dropna().values
    if len(r) < 10:
        continue
    var_95   = float(np.percentile(r, 5))          # 5th percentile → VaR 95%
    cvar_95  = float(r[r <= var_95].mean())         # mean of tail losses
    ann_ret  = float(np.mean(r) * 252)
    ann_vol  = float(np.std(r, ddof=1) * np.sqrt(252))
    records.append({
        "amfi_code":          code,
        "n_obs":              len(r),
        "ann_return_pct":     round(ann_ret * 100, 3),
        "ann_volatility_pct": round(ann_vol * 100, 3),
        "VaR_95_pct":         round(var_95  * 100, 4),
        "CVaR_95_pct":        round(cvar_95 * 100, 4),
    })

var_df = pd.DataFrame(records).merge(
    perf[["amfi_code", "scheme_name", "risk_grade", "category"]],
    on="amfi_code", how="left"
).sort_values("VaR_95_pct")          # worst VaR first (most negative at top)

out_var = os.path.join(RDIR, "var_cvar_report.csv")
var_df.to_csv(out_var, index=False)
print(f"  → {out_var}  ({len(var_df)} schemes)")
print(var_df[["scheme_name","VaR_95_pct","CVaR_95_pct"]].head(5).to_string(index=False))

# ═══════════════════════════════════════════════════════════════
# 2  Rolling 90-day Sharpe — 5 key funds
# ═══════════════════════════════════════════════════════════════
print("\nPlotting rolling Sharpe ...")

KEY_FUNDS = [100016, 120504, 148567, 148569, 119552]
LABELS = {
    100016: "HDFC Top 100",
    120504: "ICICI Pru Bluechip (D)",
    148567: "Mirae Large Cap",
    148569: "Mirae Flexi Cap",
    119552: "SBI Bluechip (D)",
}

fig, axes = plt.subplots(5, 1, figsize=(14, 18), sharex=False)
fig.patch.set_facecolor("#0d1117")

PALETTE = ["#58a6ff", "#3fb950", "#f78166", "#d2a8ff", "#ffa657"]

for ax, code, color in zip(axes, KEY_FUNDS, PALETTE):
    grp = nav[nav["amfi_code"] == code].set_index("date")["nav"].sort_index()
    ret = grp.pct_change().dropna()

    roll_mean = ret.rolling(90).mean()
    roll_std  = ret.rolling(90).std()
    roll_sharpe = (roll_mean / roll_std) * np.sqrt(252)
    roll_sharpe = roll_sharpe.dropna()

    ax.set_facecolor("#161b22")
    ax.plot(roll_sharpe.index, roll_sharpe.values, color=color, lw=1.6, alpha=0.9)
    ax.axhline(0, color="#8b949e", lw=0.8, linestyle="--", alpha=0.6)
    ax.fill_between(roll_sharpe.index, 0, roll_sharpe.values,
                    where=roll_sharpe.values >= 0, alpha=0.18, color=color)
    ax.fill_between(roll_sharpe.index, 0, roll_sharpe.values,
                    where=roll_sharpe.values < 0, alpha=0.18, color="#f85149")

    label = LABELS.get(code, str(code))
    ax.set_title(f"{label}  (AMFI {code})", color="#e6edf3", fontsize=11, pad=6, loc="left")
    ax.set_ylabel("Sharpe", color="#8b949e", fontsize=9)
    ax.tick_params(colors="#8b949e", labelsize=8)
    ax.spines[["top","right"]].set_visible(False)
    for spine in ["bottom","left"]:
        ax.spines[spine].set_color("#30363d")
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f"))
    ax.grid(axis="y", color="#21262d", linewidth=0.6)

fig.suptitle("Rolling 90-Day Sharpe Ratio — 5 Key Equity Funds\n(Annualised · √252 scaling)",
             color="#e6edf3", fontsize=14, fontweight="bold", y=1.002)
plt.tight_layout(h_pad=1.8)

out_chart = os.path.join(RDIR, "rolling_sharpe_chart.png")
fig.savefig(out_chart, dpi=150, bbox_inches="tight", facecolor="#0d1117")
plt.close()
print(f"  → {out_chart}")

print("\nDay 6 analytics outputs done.")
