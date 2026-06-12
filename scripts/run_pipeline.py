"""
run_pipeline.py — Master Execution Script
Bluestock Mutual Fund Capstone Project

This script orchestrates the full end-to-end pipeline:
    1. ETL: Data ingestion, cleaning, and SQLite DB load
    2. Metrics: CAGR, Sharpe, drawdown, alpha/beta computation
    3. Recommendations: Fund scoring and screener

Usage:
    python scripts/run_pipeline.py          # Run full pipeline
    python scripts/run_pipeline.py --etl    # ETL only
    python scripts/run_pipeline.py --metrics # Metrics only

Author: Bluestock Fintech Intern
Date:   June 2026
"""

import argparse
import logging
import os
import sys
import time

# ── Logging setup ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log"),
    ],
)
log = logging.getLogger(__name__)


def run_etl():
    """Execute the ETL pipeline: raw CSV → cleaned CSV → SQLite DB."""
    log.info("=" * 60)
    log.info("STAGE 1 — ETL Pipeline")
    log.info("=" * 60)
    t0 = time.time()
    try:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "etl_pipeline",
            pathlib.Path(__file__).with_name("etl_pipeline.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        log.info(f"ETL completed in {time.time() - t0:.1f}s")
        return True
    except Exception as exc:
        log.error(f"ETL failed: {exc}")
        return False


def run_metrics():
    """Compute fund performance metrics: CAGR, Sharpe, drawdown, alpha/beta."""
    log.info("=" * 60)
    log.info("STAGE 2 — Performance Metrics")
    log.info("=" * 60)
    t0 = time.time()
    try:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "compute_metrics",
            pathlib.Path(__file__).with_name("compute_metrics.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        log.info(f"Metrics computed in {time.time() - t0:.1f}s")
        return True
    except Exception as exc:
        log.error(f"Metrics stage failed: {exc}")
        return False


def run_recommender():
    """Run fund screener and generate ranked recommendations."""
    log.info("=" * 60)
    log.info("STAGE 3 — Fund Recommender / Screener")
    log.info("=" * 60)
    t0 = time.time()
    try:
        import importlib.util, pathlib
        spec = importlib.util.spec_from_file_location(
            "recommender",
            pathlib.Path(__file__).with_name("recommender.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        log.info(f"Recommender completed in {time.time() - t0:.1f}s")
        return True
    except Exception as exc:
        log.error(f"Recommender stage failed: {exc}")
        return False


def main():
    """Parse CLI arguments and run the requested pipeline stages."""
    parser = argparse.ArgumentParser(
        description="Bluestock MF Capstone — Master Pipeline Runner"
    )
    parser.add_argument("--etl",        action="store_true", help="Run ETL stage only")
    parser.add_argument("--metrics",    action="store_true", help="Run metrics stage only")
    parser.add_argument("--recommender",action="store_true", help="Run recommender stage only")
    args = parser.parse_args()

    # If no flag supplied, run all stages
    run_all = not (args.etl or args.metrics or args.recommender)

    log.info("╔══════════════════════════════════════════════════════╗")
    log.info("║   Bluestock Mutual Fund Capstone — Master Pipeline   ║")
    log.info("╚══════════════════════════════════════════════════════╝")

    results = {}

    if run_all or args.etl:
        results["ETL"] = run_etl()

    if run_all or args.metrics:
        results["Metrics"] = run_metrics()

    if run_all or args.recommender:
        results["Recommender"] = run_recommender()

    # ── Summary ───────────────────────────────────────────────
    log.info("=" * 60)
    log.info("PIPELINE SUMMARY")
    log.info("=" * 60)
    all_ok = True
    for stage, ok in results.items():
        status = "✓ PASS" if ok else "✗ FAIL"
        log.info(f"  {stage:<20} {status}")
        if not ok:
            all_ok = False

    if all_ok:
        log.info("\nAll stages completed successfully.")
    else:
        log.error("\nOne or more stages failed — check pipeline.log for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
