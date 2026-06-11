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

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bluestock_mf.db")

# Map user-facing labels → DB risk_grade values
RISK_MAP = {
    "low":      ["Low"],
    "moderate": ["Moderate", "Moderately High"],
    "high":     ["High", "Very High"],
}

RISK_DESCRIPTION = {
    "Low":      "Capital preservation, minimal volatility. Suitable for conservative investors or short horizons.",
    "Moderate": "Balanced growth with manageable risk. Suitable for 3–5 year horizons.",
    "High":     "Aggressive growth with higher volatility. Suitable for long-term wealth creation (5+ years).",
}


def get_recommendations(risk_appetite: str) -> pd.DataFrame:
    """
    Return top 3 funds by Sharpe ratio for the given risk appetite.

    Parameters
    ----------
    risk_appetite : str   "Low" | "Moderate" | "High"

    Returns
    -------
    pd.DataFrame  with columns: Rank, Fund, Category, Sharpe, 3yr_Return%, Expense_Ratio%
    """
    key = risk_appetite.strip().lower()
    if key not in RISK_MAP:
        raise ValueError(f"risk_appetite must be Low / Moderate / High — got '{risk_appetite}'")

    grades = RISK_MAP[key]
    placeholders = ",".join("?" * len(grades))

    db = sqlite3.connect(DB_PATH)
    query = f"""
        SELECT
            sp.amfi_code,
            sp.scheme_name        AS Fund,
            sp.category           AS Category,
            sp.risk_grade         AS Risk_Grade,
            sp.sharpe_ratio       AS Sharpe,
            sp.return_3yr_pct     AS Return_3yr_pct,
            sp.expense_ratio_pct  AS Expense_Ratio_pct,
            sp.morningstar_rating AS Stars
        FROM scheme_performance sp
        WHERE sp.risk_grade IN ({placeholders})
          AND sp.sharpe_ratio IS NOT NULL
        ORDER BY sp.sharpe_ratio DESC
        LIMIT 3
    """
    df = pd.read_sql(query, db, params=grades)
    db.close()

    df.index = range(1, len(df) + 1)
    df.index.name = "Rank"
    return df


def print_recommendations(risk_appetite: str) -> None:
    key = risk_appetite.strip().lower()
    if key not in RISK_MAP:
        print(f"[ERROR] Invalid risk appetite '{risk_appetite}'. Choose: Low / Moderate / High")
        return

    label = key.capitalize()
    grades = RISK_MAP[key]

    print("\n" + "═" * 68)
    print(f"  BLUESTOCK MF FUND RECOMMENDER  |  Risk Appetite: {label}")
    print("═" * 68)
    print(f"  Profile: {RISK_DESCRIPTION[grades[0]]}")
    print("─" * 68)

    try:
        df = get_recommendations(risk_appetite)
    except Exception as e:
        print(f"[ERROR] Could not fetch recommendations: {e}")
        return

    if df.empty:
        print("  No funds found for this risk profile.")
        return

    for rank, row in df.iterrows():
        stars = "★" * int(row["Stars"]) if pd.notna(row["Stars"]) else "N/A"
        print(f"\n  #{rank}  {row['Fund']}")
        print(f"      Category   : {row['Category']}")
        print(f"      Risk Grade : {row['Risk_Grade']}")
        print(f"      Sharpe     : {row['Sharpe']:.2f}")
        print(f"      3yr Return : {row['Return_3yr_pct']:.1f}%")
        print(f"      Expense    : {row['Expense_Ratio_pct']:.2f}%")
        print(f"      Rating     : {stars}")

    print("\n" + "─" * 68)
    print("  Disclaimer: Past performance is not indicative of future results.")
    print("  This is for educational purposes only. Consult a SEBI-registered")
    print("  investment adviser before investing.")
    print("═" * 68 + "\n")


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
        help="Risk appetite: Low / Moderate / High"
    )
    args = parser.parse_args()

    if args.risk:
        print_recommendations(args.risk)
    else:
        interactive_mode()
