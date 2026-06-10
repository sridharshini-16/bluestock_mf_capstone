"""
data_ingestion.py
-----------------
Day 1 – Bluestock Mutual Fund Capstone
Tasks:
  1. Load all 10 provided CSV datasets using Pandas.
     Print .shape, .dtypes, and .head() for each. Note anomalies.
  2. Explore fund master — unique fund houses, categories,
     sub-categories, risk grades. Understand AMFI scheme code structure.
  3. Validate AMFI codes — confirm every code in fund_master
     exists in nav_history. Write a short data quality summary.
"""

import os
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

# All 10 dataset file names (01 & 02 fetched via live_nav_fetch.py / mfapi)
DATASETS = {
    "01_fund_master":         "01_fund_master.csv",
    "02_nav_history":         "02_nav_history.csv",
    "03_aum_by_fund_house":   "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows": "04_monthly_sip_inflows.csv",
    "05_category_inflows":    "05_category_inflows.csv",
    "06_industry_folio_count":"06_industry_folio_count.csv",
    "07_scheme_performance":  "07_scheme_performance.csv",
    "08_investor_transactions":"08_investor_transactions.csv",
    "09_portfolio_holdings":  "09_portfolio_holdings.csv",
    "10_benchmark_indices":   "10_benchmark_indices.csv",
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Load & profile all datasets
# ─────────────────────────────────────────────────────────────────────────────
def load_and_profile(datasets: dict) -> dict:
    """Load every CSV, print shape/dtypes/head, flag anomalies."""
    dfs = {}
    separator = "=" * 70

    for key, filename in datasets.items():
        filepath = os.path.join(RAW_DIR, filename)
        print(f"\n{separator}")
        print(f"  DATASET : {key}  ({filename})")
        print(separator)

        if not os.path.exists(filepath):
            print(f"  ⚠  FILE NOT FOUND: {filepath}")
            print(  "     (Run live_nav_fetch.py first to generate 01 & 02)")
            dfs[key] = None
            continue

        df = pd.read_csv(filepath, low_memory=False)
        dfs[key] = df

        # ── Shape ──────────────────────────────────────────────────────────
        print(f"\n  Shape   : {df.shape[0]:,} rows × {df.shape[1]} columns")

        # ── dtypes ─────────────────────────────────────────────────────────
        print("\n  dtypes:")
        for col, dtype in df.dtypes.items():
            null_count = df[col].isna().sum()
            null_pct   = null_count / len(df) * 100
            flag = "  ◄ nulls" if null_count > 0 else ""
            print(f"    {col:<30} {str(dtype):<12} nulls={null_count:>6} ({null_pct:>5.1f}%){flag}")

        # ── head ───────────────────────────────────────────────────────────
        print("\n  head(3):")
        print(df.head(3).to_string(index=False))

        # ── Anomaly notes ──────────────────────────────────────────────────
        anomalies = []
        # Duplicate rows
        dup_count = df.duplicated().sum()
        if dup_count:
            anomalies.append(f"Duplicate rows: {dup_count}")
        # High null columns (>20 %)
        high_null = df.columns[df.isna().mean() > 0.20].tolist()
        if high_null:
            anomalies.append(f"High-null columns (>20%): {high_null}")
        # Object columns that look numeric
        for col in df.select_dtypes("object").columns:
            sample = df[col].dropna().head(200)
            try:
                pd.to_numeric(sample)
                anomalies.append(f"Column '{col}' stored as object but appears numeric")
            except (ValueError, TypeError):
                pass

        if anomalies:
            print("\n  ⚠  Anomalies detected:")
            for a in anomalies:
                print(f"     • {a}")
        else:
            print("\n  ✓  No major anomalies detected")

    return dfs


# ─────────────────────────────────────────────────────────────────────────────
# 2. Explore fund master
# ─────────────────────────────────────────────────────────────────────────────
def explore_fund_master(dfs: dict) -> None:
    """Print unique fund houses, categories, sub-categories, risk grades."""
    df = dfs.get("01_fund_master")
    if df is None:
        print("\n[explore_fund_master] Skipped – 01_fund_master not loaded.")
        return

    sep = "-" * 60
    print(f"\n{'=' * 70}")
    print("  FUND MASTER EXPLORATION")
    print(f"{'=' * 70}")

    # Unique fund houses
    if "fund_house" in df.columns:
        houses = sorted(df["fund_house"].dropna().unique())
        print(f"\n  Fund Houses ({len(houses)} unique):")
        for h in houses:
            print(f"    • {h}")

    # Categories
    if "category" in df.columns:
        cats = sorted(df["category"].dropna().unique())
        print(f"\n  Categories ({len(cats)} unique):")
        for c in cats:
            print(f"    • {c}")

    # Sub-categories
    if "sub_category" in df.columns:
        subcats = sorted(df["sub_category"].dropna().unique())
        print(f"\n  Sub-Categories ({len(subcats)} unique):")
        for s in subcats:
            print(f"    • {s}")

    # Risk grades
    if "risk_grade" in df.columns:
        grades = df["risk_grade"].value_counts()
        print(f"\n  Risk Grades:")
        for grade, cnt in grades.items():
            print(f"    {grade:<20}: {cnt:>4} schemes")

    # AMFI code structure note
    if "amfi_code" in df.columns:
        codes = df["amfi_code"].dropna()
        print(f"\n  AMFI Code Structure:")
        print(f"    Range  : {int(codes.min())} – {int(codes.max())}")
        print(f"    Length : {codes.astype(str).str.len().value_counts().to_dict()}")
        print(f"    Note   : 6-digit codes; SBI schemes typically 1195xx–1196xx,")
        print(f"             ICICI 1205xx, Axis 1190xx, etc.")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Validate AMFI codes
# ─────────────────────────────────────────────────────────────────────────────
def validate_amfi_codes(dfs: dict) -> None:
    """Check every AMFI code in fund_master exists in nav_history."""
    fm  = dfs.get("01_fund_master")
    nav = dfs.get("02_nav_history")

    print(f"\n{'=' * 70}")
    print("  DATA QUALITY SUMMARY – AMFI CODE VALIDATION")
    print(f"{'=' * 70}")

    if fm is None or nav is None:
        print("\n  Skipped – fund_master or nav_history not loaded.")
        print("  Run live_nav_fetch.py to generate 01_fund_master.csv &")
        print("  02_nav_history.csv, then re-run this script.")
        _print_partial_quality(dfs)
        return

    fm_codes  = set(fm["amfi_code"].dropna().astype(int))
    nav_codes = set(nav["amfi_code"].dropna().astype(int))

    missing_in_nav  = fm_codes  - nav_codes
    extra_in_nav    = nav_codes - fm_codes
    matched         = fm_codes  & nav_codes

    print(f"\n  fund_master  unique AMFI codes : {len(fm_codes):>5}")
    print(f"  nav_history  unique AMFI codes : {len(nav_codes):>5}")
    print(f"  Matched codes                  : {len(matched):>5}  ✓")
    if missing_in_nav:
        print(f"  Codes in fund_master NOT in nav: {len(missing_in_nav):>5}  ⚠")
        print(f"    Sample: {sorted(missing_in_nav)[:10]}")
    else:
        print("  All fund_master codes present in nav_history ✓")

    if extra_in_nav:
        print(f"  Extra codes in nav not in master: {len(extra_in_nav):>5}  (info)")

    _print_partial_quality(dfs)


def _print_partial_quality(dfs: dict) -> None:
    """Print null-rate and duplicate summary for all loaded datasets."""
    print(f"\n  {'Dataset':<30} {'Rows':>7} {'Cols':>5} {'Null%':>7} {'Dups':>6}")
    print(f"  {'-'*60}")
    for key, df in dfs.items():
        if df is None:
            print(f"  {key:<30} {'N/A':>7}")
            continue
        null_pct = df.isna().mean().mean() * 100
        dups     = df.duplicated().sum()
        print(f"  {key:<30} {df.shape[0]:>7,} {df.shape[1]:>5} {null_pct:>6.1f}% {dups:>6}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("  BLUESTOCK MF CAPSTONE – Day 1: Data Ingestion")
    print("=" * 70)

    dfs = load_and_profile(DATASETS)
    explore_fund_master(dfs)
    validate_amfi_codes(dfs)

    print(f"\n{'=' * 70}")
    print("  Data ingestion complete.")
    print(f"{'=' * 70}\n")
