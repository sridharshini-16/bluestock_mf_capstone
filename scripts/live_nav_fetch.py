"""
live_nav_fetch.py
-----------------
Day 1 – Bluestock Mutual Fund Capstone
Tasks:
  3. Fetch live NAV from mfapi.in for HDFC Top 100 Direct (125497).
     Parse JSON response and save as raw CSV.
  4. Fetch NAV for 5 key schemes:
       SBI Bluechip       119551
       ICICI Bluechip     120503
       Nippon Large Cap   118632
       Axis Bluechip      119092
       Kotak Bluechip     120841
  Also builds:
       data/raw/01_fund_master.csv   – scheme metadata from mfapi
       data/raw/02_nav_history.csv   – historical NAV for all 6 schemes
"""

import os
import time
import json
import requests
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR  = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

MFAPI_BASE = "https://api.mfapi.in/mf"

SCHEMES = {
    125497: "HDFC Top 100 Direct",
    119551: "SBI Bluechip Direct",
    120503: "ICICI Prudential Bluechip Direct",
    118632: "Nippon India Large Cap Direct",
    119092: "Axis Bluechip Direct",
    120841: "Kotak Bluechip Direct",
}


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def fetch_scheme(amfi_code: int, retries: int = 3) -> dict | None:
    """GET https://api.mfapi.in/mf/<amfi_code> with retry logic."""
    url = f"{MFAPI_BASE}/{amfi_code}"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            print(f"  ✓ Fetched {amfi_code} ({SCHEMES.get(amfi_code, 'Unknown')}) "
                  f"– {len(data.get('data', []))} NAV records")
            return data
        except requests.RequestException as exc:
            print(f"  ✗ Attempt {attempt}/{retries} failed for {amfi_code}: {exc}")
            if attempt < retries:
                time.sleep(2 ** attempt)
    return None


def parse_meta(amfi_code: int, raw: dict) -> dict:
    """Extract scheme metadata from mfapi response."""
    meta = raw.get("meta", {})
    return {
        "amfi_code":      amfi_code,
        "scheme_name":    meta.get("scheme_name", SCHEMES.get(amfi_code, "")),
        "fund_house":     meta.get("fund_house", ""),
        "scheme_type":    meta.get("scheme_type", ""),
        "scheme_category":meta.get("scheme_category", ""),
        "scheme_code":    meta.get("scheme_code", amfi_code),
    }


def parse_nav_history(amfi_code: int, raw: dict) -> pd.DataFrame:
    """Convert NAV data list to a tidy DataFrame."""
    records = raw.get("data", [])
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)             # columns: date, nav
    df["amfi_code"]   = amfi_code
    df["scheme_name"] = SCHEMES.get(amfi_code, "")
    df["date"]        = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"]         = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna(subset=["date", "nav"])
    df = df.sort_values("date").reset_index(drop=True)
    return df[["amfi_code", "scheme_name", "date", "nav"]]


# ─────────────────────────────────────────────────────────────────────────────
# Task 3: HDFC Top 100 Direct – fetch, print raw JSON, save CSV
# ─────────────────────────────────────────────────────────────────────────────
def task3_hdfc_top100() -> None:
    print("\n" + "=" * 60)
    print("  Task 3 – HDFC Top 100 Direct (125497)")
    print("=" * 60)

    raw = fetch_scheme(125497)
    if raw is None:
        print("  Failed to fetch HDFC Top 100. Check network connectivity.")
        return

    # Print raw JSON (pretty, first 500 chars for readability)
    raw_str = json.dumps(raw, indent=2)
    print("\n  Raw JSON response (first 800 chars):")
    print(raw_str[:800], "...\n" if len(raw_str) > 800 else "")

    # Save raw JSON
    json_path = os.path.join(RAW_DIR, "hdfc_top100_raw.json")
    with open(json_path, "w") as f:
        json.dump(raw, f, indent=2)
    print(f"  Saved raw JSON → {json_path}")

    # Save as CSV
    df = parse_nav_history(125497, raw)
    csv_path = os.path.join(RAW_DIR, "hdfc_top100_nav.csv")
    df.to_csv(csv_path, index=False)
    print(f"  Saved CSV ({len(df)} rows) → {csv_path}")
    print(f"\n  Latest NAV  : ₹{df['nav'].iloc[-1]:.4f}  on {df['date'].iloc[-1].date()}")
    print(f"  Oldest NAV  : ₹{df['nav'].iloc[0]:.4f}  on {df['date'].iloc[0].date()}")


# ─────────────────────────────────────────────────────────────────────────────
# Task 4: Fetch 5 key schemes → build fund_master + nav_history
# ─────────────────────────────────────────────────────────────────────────────
def task4_five_schemes() -> None:
    print("\n" + "=" * 60)
    print("  Task 4 – 5 Key Schemes")
    print("=" * 60)

    all_meta = []
    all_nav  = []

    for code in SCHEMES:
        raw = fetch_scheme(code)
        if raw is None:
            print(f"  Skipping {code} due to fetch failure.")
            continue
        all_meta.append(parse_meta(code, raw))
        nav_df = parse_nav_history(code, raw)
        if not nav_df.empty:
            all_nav.append(nav_df)
        time.sleep(0.3)   # polite rate-limiting

    # ── Fund master ──────────────────────────────────────────────────────────
    if all_meta:
        fm_df = pd.DataFrame(all_meta)
        # Add placeholder columns expected by data_ingestion.py
        fm_df["category"]     = fm_df["scheme_category"]
        fm_df["sub_category"] = ""
        fm_df["plan"]         = fm_df["scheme_name"].str.extract(r"(Direct|Regular)", expand=False).fillna("Direct")
        fm_df["risk_grade"]   = "Moderate"          # mfapi doesn't expose risk grade

        fm_path = os.path.join(RAW_DIR, "01_fund_master.csv")
        fm_df.to_csv(fm_path, index=False)
        print(f"\n  Saved 01_fund_master.csv ({len(fm_df)} schemes) → {fm_path}")
        print(fm_df[["amfi_code", "scheme_name", "fund_house", "category"]].to_string(index=False))

    # ── NAV history ─────────────────────────────────────────────────────────
    if all_nav:
        nav_df = pd.concat(all_nav, ignore_index=True)
        nav_path = os.path.join(RAW_DIR, "02_nav_history.csv")
        nav_df.to_csv(nav_path, index=False)
        print(f"\n  Saved 02_nav_history.csv ({len(nav_df):,} rows) → {nav_path}")

        # Quick summary
        summary = (nav_df.groupby("scheme_name")
                         .agg(records=("nav","count"),
                              latest_nav=("nav","last"),
                              latest_date=("date","max"))
                         .reset_index())
        print("\n  Per-scheme summary:")
        print(summary.to_string(index=False))


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  BLUESTOCK MF CAPSTONE – Day 1: Live NAV Fetch")
    print("=" * 60)

    task3_hdfc_top100()
    task4_five_schemes()

    print("\n" + "=" * 60)
    print("  Live NAV fetch complete.")
    print("=" * 60)
