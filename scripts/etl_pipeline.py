"""
Day 2 Pipeline: Data Cleaning + SQLite DB Load
Bluestock Mutual Fund Capstone
"""

import os
import logging
import pandas as pd
import numpy as np
import sqlite3
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s",
                     datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger(__name__)
import warnings
warnings.filterwarnings("ignore")

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bluestock_mf.db")

os.makedirs(PROCESSED_DIR, exist_ok=True)

logger.info("=" * 60)
logger.info("STEP 1: CLEANING DATA")
logger.info("=" * 60)

# ── 01 Fund Master ────────────────────────────────────────────
logger.info("\n[01] Cleaning fund_master.csv ...")
df_fund = pd.read_csv(f"{RAW_DIR}/01_fund_master.csv")
df_fund["launch_date"] = pd.to_datetime(df_fund["launch_date"], errors="coerce")
df_fund.drop_duplicates(subset=["amfi_code"], keep="first", inplace=True)
df_fund["expense_ratio_pct"] = pd.to_numeric(df_fund["expense_ratio_pct"], errors="coerce")
df_fund["exit_load_pct"] = pd.to_numeric(df_fund["exit_load_pct"], errors="coerce")
df_fund.to_csv(f"{PROCESSED_DIR}/01_fund_master.csv", index=False)
logger.info(f"  → {len(df_fund)} rows saved")

# ── 02 NAV History ────────────────────────────────────────────
logger.info("\n[02] Cleaning nav_history.csv ...")
df_nav = pd.read_csv(f"{RAW_DIR}/02_nav_history.csv")
df_nav["date"] = pd.to_datetime(df_nav["date"], errors="coerce")
df_nav["nav"] = pd.to_numeric(df_nav["nav"], errors="coerce")

# Remove invalid rows
before = len(df_nav)
df_nav.dropna(subset=["date", "amfi_code"], inplace=True)
df_nav = df_nav[df_nav["nav"] > 0]

# Sort by fund + date
df_nav.sort_values(["amfi_code", "date"], inplace=True)
df_nav.reset_index(drop=True, inplace=True)

# Remove duplicates
df_nav.drop_duplicates(subset=["amfi_code", "date"], keep="last", inplace=True)

# Forward-fill missing NAV for holidays/weekends within each fund
all_funds = df_nav["amfi_code"].unique()
frames = []
for code in all_funds:
    fund_df = df_nav[df_nav["amfi_code"] == code].copy()
    fund_df = fund_df.set_index("date")
    # Create complete date range (calendar days) and forward-fill
    full_idx = pd.date_range(fund_df.index.min(), fund_df.index.max(), freq="D")
    fund_df = fund_df.reindex(full_idx)
    fund_df["amfi_code"] = code
    fund_df["nav"] = fund_df["nav"].ffill()
    fund_df = fund_df.dropna(subset=["nav"])
    fund_df.index.name = "date"
    fund_df.reset_index(inplace=True)
    frames.append(fund_df)

df_nav_filled = pd.concat(frames, ignore_index=True)
# Validate NAV > 0 after fill
df_nav_filled = df_nav_filled[df_nav_filled["nav"] > 0]
df_nav_filled.to_csv(f"{PROCESSED_DIR}/02_nav_history.csv", index=False)
logger.info(f"  → Source rows: {before}, After fill: {len(df_nav_filled)} rows saved")
logger.info(f"  → NAV > 0 validation: PASSED (min NAV = {df_nav_filled['nav'].min():.4f})")

# ── 03 AUM by Fund House ──────────────────────────────────────
logger.info("\n[03] Cleaning aum_by_fund_house.csv ...")
df_aum = pd.read_csv(f"{RAW_DIR}/03_aum_by_fund_house.csv")
df_aum["date"] = pd.to_datetime(df_aum["date"], errors="coerce")
df_aum.drop_duplicates(inplace=True)
df_aum.dropna(subset=["date", "fund_house"], inplace=True)
df_aum.to_csv(f"{PROCESSED_DIR}/03_aum_by_fund_house.csv", index=False)
logger.info(f"  → {len(df_aum)} rows saved")

# ── 04 Monthly SIP Inflows ────────────────────────────────────
logger.info("\n[04] Cleaning monthly_sip_inflows.csv ...")
df_sip = pd.read_csv(f"{RAW_DIR}/04_monthly_sip_inflows.csv")
df_sip["month"] = pd.to_datetime(df_sip["month"], format="%Y-%m", errors="coerce")
df_sip.drop_duplicates(subset=["month"], keep="last", inplace=True)
df_sip.dropna(subset=["month"], inplace=True)
df_sip.sort_values("month", inplace=True)
df_sip.to_csv(f"{PROCESSED_DIR}/04_monthly_sip_inflows.csv", index=False)
logger.info(f"  → {len(df_sip)} rows saved")

# ── 05 Category Inflows ───────────────────────────────────────
logger.info("\n[05] Cleaning category_inflows.csv ...")
df_cat = pd.read_csv(f"{RAW_DIR}/05_category_inflows.csv")
df_cat["month"] = pd.to_datetime(df_cat["month"], format="%Y-%m", errors="coerce")
df_cat.drop_duplicates(inplace=True)
df_cat.dropna(subset=["month", "category"], inplace=True)
df_cat.to_csv(f"{PROCESSED_DIR}/05_category_inflows.csv", index=False)
logger.info(f"  → {len(df_cat)} rows saved")

# ── 06 Industry Folio Count ───────────────────────────────────
logger.info("\n[06] Cleaning industry_folio_count.csv ...")
df_folio = pd.read_csv(f"{RAW_DIR}/06_industry_folio_count.csv")
df_folio["month"] = pd.to_datetime(df_folio["month"], format="%Y-%m", errors="coerce")
df_folio.drop_duplicates(subset=["month"], keep="last", inplace=True)
df_folio.dropna(subset=["month"], inplace=True)
df_folio.sort_values("month", inplace=True)
df_folio.to_csv(f"{PROCESSED_DIR}/06_industry_folio_count.csv", index=False)
logger.info(f"  → {len(df_folio)} rows saved")

# ── 07 Scheme Performance ─────────────────────────────────────
logger.info("\n[07] Cleaning scheme_performance.csv ...")
df_perf = pd.read_csv(f"{RAW_DIR}/07_scheme_performance.csv")

# Validate all return columns are numeric
return_cols = ["return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
               "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio",
               "sortino_ratio", "std_dev_ann_pct", "max_drawdown_pct"]
for col in return_cols:
    df_perf[col] = pd.to_numeric(df_perf[col], errors="coerce")

# Flag anomalies
df_perf["anomaly_flag"] = False
df_perf.loc[df_perf["return_1yr_pct"].abs() > 200, "anomaly_flag"] = True
df_perf.loc[df_perf["return_3yr_pct"].abs() > 100, "anomaly_flag"] = True
df_perf.loc[df_perf["beta"].abs() > 3, "anomaly_flag"] = True

anomalies = df_perf["anomaly_flag"].sum()
logger.info(f"  → Anomalous return rows flagged: {anomalies}")

# Check expense_ratio range 0.1% – 2.5%
out_of_range = df_perf[
    (df_perf["expense_ratio_pct"] < 0.1) | (df_perf["expense_ratio_pct"] > 2.5)
]
logger.info(f"  → Expense ratio out-of-range rows: {len(out_of_range)}")
if len(out_of_range) > 0:
    df_perf.loc[out_of_range.index, "anomaly_flag"] = True

df_perf.drop_duplicates(subset=["amfi_code"], keep="first", inplace=True)
df_perf.to_csv(f"{PROCESSED_DIR}/07_scheme_performance.csv", index=False)
logger.info(f"  → {len(df_perf)} rows saved")

# ── 08 Investor Transactions ──────────────────────────────────
logger.info("\n[08] Cleaning investor_transactions.csv ...")
df_txn = pd.read_csv(f"{RAW_DIR}/08_investor_transactions.csv")

# Standardise transaction_type
type_map = {
    "sip": "SIP", "Sip": "SIP", "SIP": "SIP",
    "lumpsum": "Lumpsum", "Lumpsum": "Lumpsum", "LUMPSUM": "Lumpsum",
    "redemption": "Redemption", "Redemption": "Redemption", "REDEMPTION": "Redemption",
}
df_txn["transaction_type"] = df_txn["transaction_type"].map(
    lambda x: type_map.get(str(x).strip(), str(x).strip())
)
valid_types = {"SIP", "Lumpsum", "Redemption"}
invalid_types = df_txn[~df_txn["transaction_type"].isin(valid_types)]
logger.info(f"  → Invalid transaction_type rows: {len(invalid_types)}")

# Fix date formats
df_txn["transaction_date"] = pd.to_datetime(df_txn["transaction_date"], errors="coerce")
df_txn.dropna(subset=["transaction_date"], inplace=True)

# Validate amount > 0
before = len(df_txn)
df_txn = df_txn[df_txn["amount_inr"] > 0]
logger.info(f"  → Removed {before - len(df_txn)} rows with amount ≤ 0")

# Check KYC status enum
valid_kyc = {"Verified", "Pending", "Rejected", "KYC Verified", "KYC Pending"}
kyc_vals = df_txn["kyc_status"].unique()
logger.info(f"  → KYC status values present: {list(kyc_vals)}")

df_txn.drop_duplicates(inplace=True)
df_txn.to_csv(f"{PROCESSED_DIR}/08_investor_transactions.csv", index=False)
logger.info(f"  → {len(df_txn)} rows saved")

# ── 09 Portfolio Holdings ─────────────────────────────────────
logger.info("\n[09] Cleaning portfolio_holdings.csv ...")
df_port = pd.read_csv(f"{RAW_DIR}/09_portfolio_holdings.csv")
df_port["portfolio_date"] = pd.to_datetime(df_port["portfolio_date"], errors="coerce")
df_port["weight_pct"] = pd.to_numeric(df_port["weight_pct"], errors="coerce")
df_port["market_value_cr"] = pd.to_numeric(df_port["market_value_cr"], errors="coerce")
df_port["current_price_inr"] = pd.to_numeric(df_port["current_price_inr"], errors="coerce")
df_port.drop_duplicates(subset=["amfi_code", "stock_symbol", "portfolio_date"], inplace=True)
df_port.dropna(subset=["amfi_code", "stock_symbol"], inplace=True)
df_port.to_csv(f"{PROCESSED_DIR}/09_portfolio_holdings.csv", index=False)
logger.info(f"  → {len(df_port)} rows saved")

# ── 10 Benchmark Indices ──────────────────────────────────────
logger.info("\n[10] Cleaning benchmark_indices.csv ...")
df_bench = pd.read_csv(f"{RAW_DIR}/10_benchmark_indices.csv")
df_bench["date"] = pd.to_datetime(df_bench["date"], errors="coerce")
df_bench["close_value"] = pd.to_numeric(df_bench["close_value"], errors="coerce")
df_bench.drop_duplicates(subset=["date", "index_name"], inplace=True)
df_bench.dropna(subset=["date", "index_name", "close_value"], inplace=True)
df_bench = df_bench[df_bench["close_value"] > 0]
df_bench.sort_values(["index_name", "date"], inplace=True)
df_bench.to_csv(f"{PROCESSED_DIR}/10_benchmark_indices.csv", index=False)
logger.info(f"  → {len(df_bench)} rows saved")

logger.info("\n" + "=" * 60)
logger.info("STEP 2: LOADING INTO SQLITE")
logger.info("=" * 60)

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

# Read cleaned files
df_fund  = pd.read_csv(f"{PROCESSED_DIR}/01_fund_master.csv", parse_dates=["launch_date"])
df_nav   = pd.read_csv(f"{PROCESSED_DIR}/02_nav_history.csv", parse_dates=["date"])
df_aum   = pd.read_csv(f"{PROCESSED_DIR}/03_aum_by_fund_house.csv", parse_dates=["date"])
df_sip   = pd.read_csv(f"{PROCESSED_DIR}/04_monthly_sip_inflows.csv", parse_dates=["month"])
df_cat   = pd.read_csv(f"{PROCESSED_DIR}/05_category_inflows.csv", parse_dates=["month"])
df_folio = pd.read_csv(f"{PROCESSED_DIR}/06_industry_folio_count.csv", parse_dates=["month"])
df_perf  = pd.read_csv(f"{PROCESSED_DIR}/07_scheme_performance.csv")
df_txn   = pd.read_csv(f"{PROCESSED_DIR}/08_investor_transactions.csv", parse_dates=["transaction_date"])
df_port  = pd.read_csv(f"{PROCESSED_DIR}/09_portfolio_holdings.csv", parse_dates=["portfolio_date"])
df_bench = pd.read_csv(f"{PROCESSED_DIR}/10_benchmark_indices.csv", parse_dates=["date"])

# Convert dates to string for SQLite compatibility
for df, col in [
    (df_fund, "launch_date"),
    (df_nav, "date"),
    (df_aum, "date"),
    (df_sip, "month"),
    (df_cat, "month"),
    (df_folio, "month"),
    (df_txn, "transaction_date"),
    (df_port, "portfolio_date"),
    (df_bench, "date"),
]:
    df[col] = df[col].astype(str)

table_map = {
    "fund_master":           df_fund,
    "nav_history":           df_nav,
    "aum_by_fund_house":     df_aum,
    "monthly_sip_inflows":   df_sip,
    "category_inflows":      df_cat,
    "industry_folio_count":  df_folio,
    "scheme_performance":    df_perf,
    "investor_transactions": df_txn,
    "portfolio_holdings":    df_port,
    "benchmark_indices":     df_bench,
}

with engine.connect() as conn:
    for table_name, df in table_map.items():
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()[0]
        src_rows = len(df)
        match = "✓" if result == src_rows else "✗ MISMATCH"
        logger.info(f"  [{match}] {table_name}: source={src_rows}, db={result}")

logger.info("\nAll tables loaded into:", DB_PATH)
logger.info("\n" + "=" * 60)
logger.info("DONE — Day 2 pipeline complete.")
logger.info("=" * 60)
