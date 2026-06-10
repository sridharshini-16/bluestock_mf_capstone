# Bluestock Mutual Fund Capstone

A data engineering and analysis capstone project on Indian Mutual Funds using AMFI data, live NAV feeds, and Pandas/Python.

## Project Structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/             # Original CSVs + live NAV fetched from mfapi.in
│   └── processed/       # Cleaned / transformed datasets
├── notebooks/           # Jupyter notebooks for EDA and visualisation
├── sql/                 # SQL queries and schema definitions
├── dashboard/           # Plotly / Dash dashboard files
├── reports/             # Final reports and summaries
├── data_ingestion.py    # Load & profile all 10 datasets, validate AMFI codes
├── live_nav_fetch.py    # Fetch live NAV from mfapi.in for 6 schemes
└── requirements.txt     # Python dependencies
```

## Setup

```bash
git clone https://github.com/sridharshini-16/bluestock_mf_capstone.git
cd bluestock_mf_capstone
pip install -r requirements.txt
```

## Day 1 – Data Ingestion

```bash
# Step 1: Fetch live NAV (creates 01_fund_master.csv & 02_nav_history.csv)
python live_nav_fetch.py

# Step 2: Load, profile and validate all datasets
python data_ingestion.py
```

### Datasets

| # | File | Description |
|---|------|-------------|
| 01 | `01_fund_master.csv` | Scheme metadata (generated via live_nav_fetch.py) |
| 02 | `02_nav_history.csv` | Historical NAV (generated via live_nav_fetch.py) |
| 03 | `03_aum_by_fund_house.csv` | AUM by fund house (quarterly) |
| 04 | `04_monthly_sip_inflows.csv` | SIP inflow & account data |
| 05 | `05_category_inflows.csv` | Category-level net inflows |
| 06 | `06_industry_folio_count.csv` | Industry folio counts |
| 07 | `07_scheme_performance.csv` | Scheme returns, risk metrics |
| 08 | `08_investor_transactions.csv` | Investor transaction ledger |
| 09 | `09_portfolio_holdings.csv` | Scheme portfolio holdings |
| 10 | `10_benchmark_indices.csv` | Nifty / Sensex daily closes |

## Data Sources

- Live NAV: [mfapi.in](https://api.mfapi.in)
- Static datasets: Provided by Bluestock Fintech internship programme
