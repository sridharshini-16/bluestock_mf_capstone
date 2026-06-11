"""
recommender.py — Simple Fund Recommender
Bluestock MF Capstone | Day 6

Usage:
    python recommender.py                  # interactive prompt
    python recommender.py --risk High      # CLI flag
    python recommender.py --risk Low
    python recommender.py --risk Moderate
"""

import argparse
import sqlite3
import os
import pandas as pd

BASE    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "db", "bluestock_mf.db")
CSV_PATH = os.path.join(BASE, "data", "raw", "07_scheme_performance.csv")

# Map user-facing labels → DB risk_grade values
RISK_MAP = {
    "low"      : ["Low"],
    "moderate" : ["Moderate"],
    "high"     : ["High", "Very High", "Moderately High"],
}

RISK_DESCRIPTION = {
    "low"      : "Capital preservation, minimal volatility. Suitable for conservative investors or short horizons.",
    "moderate" : "Balanced growth with manageable risk. Suitable for 3–5 year horizons.",
    "high"     : "Aggressive growth with higher volatility. Suitable for long-term wealth creation (5+ years).",
}


def _load_scheme_performance() -> pd.DataFrame:
    """Load scheme_performance from DB if available, else fall back to CSV."""
    if os.path.exists(DB_PATH):
        try:
            db = sqlite3.connect(DB_PATH)
            df = pd.read_sql(
                "SELECT amfi_code, scheme_name, category, risk_grade, "
                "sharpe_ratio, return_3yr_pct, expense_ratio_pct, morningstar_rating "
                "FROM scheme_performance",
                db,
            )
            db.close()
            return df
        except Exception:
            pass
    if os.path.exists(CSV_PATH):
        return pd.read_csv(CSV_PATH)
    raise FileNotFoundError(
        f"Could not find scheme_performance in DB ({DB_PATH}) or CSV ({CSV_PATH})."
    )


def get_recommendations(risk_appetite: str, top_n: int = 3) -> pd.DataFrame:
    """
    Return top N funds by Sharpe ratio for the given risk appetite.

    Parameters
    ----------
    risk_appetite : str   "Low" | "Moderate" | "High"
    top_n         : int   Number of recommendations (default 3)

    Returns
    -------
    pd.DataFrame  ranked by Sharpe ratio
    """
    key = risk_appetite.strip().lower()
    if key not in RISK_MAP:
        raise ValueError(f"risk_appetite must be Low / Moderate / High — got '{risk_appetite}'")

    grades = RISK_MAP[key]
    perf   = _load_scheme_performance()

    result = (
        perf[perf["risk_grade"].isin(grades) & perf["sharpe_ratio"].notna()]
        .nlargest(top_n, "sharpe_ratio")
        [["amfi_code", "scheme_name", "category", "risk_grade",
          "sharpe_ratio", "return_3yr_pct", "expense_ratio_pct", "morningstar_rating"]]
        .reset_index(drop=True)
    )
    result.index = range(1, len(result) + 1)
    result.index.name = "Rank"
    return result


def print_recommendations(risk_appetite: str) -> None:
    key   = risk_appetite.strip().lower()
    if key not in RISK_MAP:
        print(f"[ERROR] Invalid risk appetite '{risk_appetite}'. Choose: Low / Moderate / High")
        return

    label = key.capitalize()
    print("\n" + "═" * 72)
    print(f"  BLUESTOCK MF FUND RECOMMENDER  |  Risk Appetite: {label}")
    print("═" * 72)
    print(f"  Profile : {RISK_DESCRIPTION[key]}")
    print("─" * 72)

    try:
        df = get_recommendations(risk_appetite)
    except Exception as e:
        print(f"[ERROR] Could not fetch recommendations: {e}")
        return

    if df.empty:
        print("  No funds found for this risk profile.")
        return

    for rank, row in df.iterrows():
        stars = "★" * int(row["morningstar_rating"]) if pd.notna(row.get("morningstar_rating")) else "N/A"
        print(f"\n  #{rank}  {row['scheme_name']}")
        print(f"       Category   : {row['category']}")
        print(f"       Risk Grade : {row['risk_grade']}")
        print(f"       Sharpe     : {row['sharpe_ratio']:.2f}")
        print(f"       3yr Return : {row['return_3yr_pct']:.1f}%")
        print(f"       Expense    : {row['expense_ratio_pct']:.2f}%")
        print(f"       Rating     : {stars}")

    print("\n" + "─" * 72)
    print("  ⚠  Disclaimer: Past performance is not indicative of future results.")
    print("     This is for educational purposes only. Consult a SEBI-registered")
    print("     investment adviser before investing.")
    print("═" * 72 + "\n")


def interactive_mode() -> None:
    print("\n  Welcome to the Bluestock MF Fund Recommender")
    print("  ─────────────────────────────────────────────")
    while True:
        risk = input("  Enter your risk appetite [Low / Moderate / High / quit]: ").strip()
        if risk.lower() in ("quit", "q", "exit"):
            print("  Goodbye!\n")
            break
        if risk.lower() in RISK_MAP:
            print_recommendations(risk)
        else:
            print("  Please enter: Low, Moderate, or High\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bluestock MF Fund Recommender")
    parser.add_argument(
        "--risk", type=str, default=None,
        help="Risk appetite: Low / Moderate / High",
    )
    args = parser.parse_args()

    if args.risk:
        print_recommendations(args.risk)
    else:
        interactive_mode()
