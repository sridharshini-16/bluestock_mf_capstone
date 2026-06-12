# Bluestock Mutual Fund Analytics Capstone

> **A full-stack data engineering and analytics project on the Indian Mutual Fund industry.**  
> Built during the Bluestock Fintech Internship — June 2026.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Objectives](#objectives)
- [Repository Structure](#repository-structure)
- [Dataset Descriptions](#dataset-descriptions)
- [Setup Instructions](#setup-instructions)
- [How to Run the ETL Pipeline](#how-to-run-the-etl-pipeline)
- [How to Open the Dashboard](#how-to-open-the-dashboard)
- [Key Findings](#key-findings)
- [Deliverables](#deliverables)

---

## Project Overview

This capstone project analyses the Indian Mutual Fund ecosystem using 10 interconnected datasets covering fund metadata, NAV history, AUM trends, SIP flows, investor demographics, and scheme-level performance metrics. The pipeline ingests raw CSV data, cleans and normalises it into a SQLite database, computes risk/return metrics, and surfaces insights through an interactive Power BI dashboard and a comprehensive final report.

**Period covered:** January 2022 – December 2025  
**Funds analysed:** 40 schemes across 10 AMCs  
**Transactions processed:** 32,778 investor records  
**Industry AUM captured:** Rs. 39+ lakh crore

---

## Objectives

1. Build a reproducible ETL pipeline for 10 MF datasets
2. Perform exploratory data analysis (EDA) on fund flows, NAVs, and investor behaviour
3. Compute CAGR, Sharpe ratio, Sortino ratio, alpha, beta, and max drawdown for all schemes
4. Benchmark fund performance against NIFTY 50, NIFTY 100, and NIFTY 500 indices
5. Analyse SIP growth trends and investor demographic patterns
6. Build an interactive 4-page Power BI dashboard
7. Deliver a 15-20 page final PDF report and 12-slide presentation
8. Publish all code, data, and outputs to a versioned GitHub repository

---

## Repository Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/                     # Original 10 CSV datasets (unmodified)
│   ├── processed/               # Cleaned CSVs + derived metrics CSVs
│   └── db/
│       └── bluestock_mf.db      # SQLite database (all 10 tables)
├── scripts/
│   ├── run_pipeline.py          # Master execution script
│   ├── etl_pipeline.py          # ETL: cleaning, validation, DB load
│   ├── compute_metrics.py       # CAGR, Sharpe, drawdown, alpha/beta
│   ├── recommender.py           # Fund screener & scoring
│   └── live_nav_fetch.py        # Optional: live NAV fetch from AMFI API
├── notebooks/
│   ├── 01_data_ingestion.ipynb
│   ├── 03_eda_analysis.ipynb
│   ├── 04_Performance_Analytics.ipynb
│   └── 05_Advanced_Analytics.ipynb
├── dashboard/
│   ├── bluestock_mf_dashboard.pbix
│   ├── Dashboard.pdf
│   └── screenshots/
├── reports/
│   ├── Final_Report/            # Chart PNGs
│   ├── Final_Report.pdf         # 15-20 page final PDF report
│   └── Bluestock_MF_Presentation.pptx
├── sql/
│   ├── schema.sql
│   └── queries.sql
├── requirements.txt
├── data_dictionary.md
└── README.md
```

---

## Dataset Descriptions

| # | File | Rows | Description |
|---|------|------|-------------|
| 01 | `01_fund_master.csv` | 40 | Fund metadata: AMC, category, benchmark, expense ratio, fund manager |
| 02 | `02_nav_history.csv` | 46,000 | Daily NAV per fund (Jan 2022 – Dec 2025) |
| 03 | `03_aum_by_fund_house.csv` | 90 | Quarterly AUM per AMC in Rs. crore |
| 04 | `04_monthly_sip_inflows.csv` | 48 | Monthly SIP inflows, active SIP accounts, new registrations |
| 05 | `05_category_inflows.csv` | 144 | Monthly net inflows by fund category |
| 06 | `06_industry_folio_count.csv` | 21 | Quarterly folio counts by asset class |
| 07 | `07_scheme_performance.csv` | 40 | Scheme-level risk/return metrics |
| 08 | `08_investor_transactions.csv` | 32,778 | Individual SIP/lumpsum/redemption transactions |
| 09 | `09_portfolio_holdings.csv` | 322 | Stock-level portfolio holdings with weights |
| 10 | `10_benchmark_indices.csv` | 8,050 | Daily closing values for NIFTY 50, NIFTY 100, NIFTY 500 |

---

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- pip package manager
- Power BI Desktop (free, for .pbix dashboard)

### 1. Clone the Repository

```bash
git clone https://github.com/sridharshini-16/bluestock_mf_capstone.git
cd bluestock_mf_capstone
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

---

## How to Run the ETL Pipeline

### Full Pipeline (recommended)

```bash
python scripts/run_pipeline.py
```

### Individual Stages

```bash
python scripts/run_pipeline.py --etl        # ETL only
python scripts/run_pipeline.py --metrics    # Metrics only
python scripts/run_pipeline.py --recommender # Recommender only
```

**Outputs:**
- Cleaned CSVs: `data/processed/`
- SQLite DB: `data/db/bluestock_mf.db`
- Metrics: `data/processed/cagr_comparison.csv`, `alpha_beta.csv`, `fund_scorecard.csv`

---

## How to Open the Dashboard

### Power BI Desktop (Interactive)

1. Download [Power BI Desktop](https://powerbi.microsoft.com/desktop/) (free)
2. Open `dashboard/bluestock_mf_dashboard.pbix`
3. Refresh data source pointing to `data/processed/`
4. Four pages: Industry Overview, Fund Performance, Investor Analytics, SIP & Market Trends

### Static PDF Export

Open `dashboard/Dashboard.pdf` in any PDF viewer.

---

## Key Findings

- **AUM nearly doubled** from Rs. 38.6L Cr (Mar 2022) to Rs. 67L+ Cr (Dec 2025)
- **SIP inflows surged 169%** — from Rs. 11,517 Cr to Rs. 31,002 Cr/month
- **Folio count doubled** — 13.26 Cr to 26.12 Cr, reflecting mass retail participation
- **Direct plans outperform** regular plans by 150-300 bps annually
- **Mid & Small Cap** funds delivered 20%+ 1-year returns with higher drawdown risk
- **SBI MF leads** with Rs. 12.5L Cr AUM; top-5 AMCs control ~67% of industry assets
- **Only 35% of schemes** beat their benchmark on a 3-year risk-adjusted basis

---

## Deliverables

| # | Deliverable | Location |
|---|------------|----------|
| 1 | Final PDF Report (15-20 pages) | `reports/Final_Report.pdf` |
| 2 | 12-slide Presentation | `reports/Bluestock_MF_Presentation.pptx` |
| 3 | Power BI Dashboard | `dashboard/bluestock_mf_dashboard.pbix` |
| 4 | SQLite Database | `data/db/bluestock_mf.db` |
| 5 | Cleaned Datasets | `data/processed/` |
| 6 | Analysis Notebooks | `notebooks/` |
| 7 | Clean Python Scripts | `scripts/` |

---

## Version History

| Tag | Description |
|-----|-------------|
| `v1.0` | Final submission — Complete Bluestock MF Capstone |

---

*Built during the Bluestock Fintech Internship, June 2026.*
