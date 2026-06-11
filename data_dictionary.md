# Bluestock MF Capstone – Data Dictionary

> **Project:** Bluestock Mutual Fund Analytics Capstone  
> **Author:** Internship Batch  
> **Last Updated:** Day 2  
> **Database:** `bluestock_mf.db` (SQLite)  
> **Raw Data:** `data/raw/`  
> **Processed Data:** `data/processed/`

---

## Table of Contents

1. [01_fund_master](#01-fund_master)
2. [02_nav_history](#02-nav_history)
3. [03_aum_by_fund_house](#03-aum_by_fund_house)
4. [04_monthly_sip_inflows](#04-monthly_sip_inflows)
5. [05_category_inflows](#05-category_inflows)
6. [06_industry_folio_count](#06-industry_folio_count)
7. [07_scheme_performance](#07-scheme_performance)
8. [08_investor_transactions](#08-investor_transactions)
9. [09_portfolio_holdings](#09-portfolio_holdings)
10. [10_benchmark_indices](#10-benchmark_indices)
11. [Cleaning Notes](#cleaning-notes)

---

## 01 fund_master

**Source file:** `01_fund_master.csv`  
**SQLite table:** `fund_master`  
**Rows (cleaned):** 40  
**Grain:** One row per AMFI-registered mutual fund scheme.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (PK) | Unique AMFI registration number assigned to each scheme | Positive integer |
| `fund_house` | TEXT | Asset Management Company (AMC) name | e.g., "SBI Mutual Fund" |
| `scheme_name` | TEXT | Full official name of the scheme | Free text |
| `category` | TEXT | SEBI-defined broad fund category | Equity / Debt / Hybrid / Solution Oriented / Other |
| `sub_category` | TEXT | SEBI-defined sub-category within the category | e.g., "Large Cap Fund" |
| `plan` | TEXT | Growth or IDCW (Dividend) plan | Growth / IDCW |
| `launch_date` | DATE (TEXT ISO) | Date when the scheme was first launched | YYYY-MM-DD |
| `benchmark` | TEXT | Index against which the fund's performance is measured | e.g., "NIFTY 50 TRI" |
| `expense_ratio_pct` | REAL | Annual fee charged to investors as % of AUM | 0.1 – 2.5 |
| `exit_load_pct` | REAL | Percentage fee charged on early redemption | 0.0 – 2.0 |
| `min_sip_amount` | INTEGER | Minimum SIP instalment amount (₹) | ≥ 100 |
| `min_lumpsum_amount` | INTEGER | Minimum one-time investment amount (₹) | ≥ 500 |
| `fund_manager` | TEXT | Name of the lead portfolio manager | Free text |
| `risk_category` | TEXT | SEBI Riskometer level | Low / Low to Moderate / Moderate / Moderately High / High / Very High |
| `sebi_category_code` | TEXT | Short SEBI category code for regulatory reporting | e.g., "EC01" |

---

## 02 nav_history

**Source file:** `02_nav_history.csv`  
**SQLite table:** `nav_history`  
**Rows (cleaned, after forward-fill):** 64,320  
**Grain:** One row per fund per calendar date (including forward-filled holidays/weekends).

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (FK → fund_master) | Fund identifier | Valid amfi_code |
| `date` | DATE (TEXT ISO) | NAV date | YYYY-MM-DD |
| `nav` | REAL | Net Asset Value per unit in ₹ | > 0 |

**Cleaning applied:**
- Dates parsed to `datetime`, sorted by `amfi_code + date`.
- Duplicates removed (keep last).
- Full calendar range created per fund; NAV forward-filled for weekends/holidays.
- Rows with `nav ≤ 0` removed.

---

## 03 aum_by_fund_house

**Source file:** `03_aum_by_fund_house.csv`  
**SQLite table:** `aum_by_fund_house`  
**Rows (cleaned):** 90  
**Grain:** One row per fund house per reporting date (quarterly).

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `date` | DATE (TEXT ISO) | Quarter-end reporting date | YYYY-MM-DD |
| `fund_house` | TEXT | AMC name | Free text |
| `aum_lakh_crore` | REAL | AUM in lakh crore rupees (₹ lakh cr) | > 0 |
| `aum_crore` | INTEGER | AUM in crore rupees | > 0 |
| `num_schemes` | INTEGER | Number of active schemes offered | > 0 |

---

## 04 monthly_sip_inflows

**Source file:** `04_monthly_sip_inflows.csv`  
**SQLite table:** `monthly_sip_inflows`  
**Rows (cleaned):** 48  
**Grain:** One row per calendar month for the entire industry.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `month` | DATE (TEXT ISO) | First day of the month | YYYY-MM-DD |
| `sip_inflow_crore` | INTEGER | Total SIP collections for the month (₹ crore) | > 0 |
| `active_sip_accounts_crore` | REAL | Total active SIP accounts in crore | > 0 |
| `new_sip_accounts_lakh` | REAL | New SIP registrations in lakh during the month | ≥ 0 |
| `sip_aum_lakh_crore` | REAL | AUM attributable to SIP investments | > 0 |
| `yoy_growth_pct` | REAL | Year-over-year growth in SIP inflows | Can be NULL for first 12 months |

---

## 05 category_inflows

**Source file:** `05_category_inflows.csv`  
**SQLite table:** `category_inflows`  
**Rows (cleaned):** 144  
**Grain:** One row per fund category per month.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `month` | DATE (TEXT ISO) | First day of the month | YYYY-MM-DD |
| `category` | TEXT | Fund category name | e.g., "Large Cap", "Mid Cap" |
| `net_inflow_crore` | REAL | Net flow (inflow − redemption) in ₹ crore | Can be negative (net outflow) |

---

## 06 industry_folio_count

**Source file:** `06_industry_folio_count.csv`  
**SQLite table:** `industry_folio_count`  
**Rows (cleaned):** 21  
**Grain:** One row per month for the entire industry.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `month` | DATE (TEXT ISO) | First day of the month | YYYY-MM-DD |
| `total_folios_crore` | REAL | Total investor folios in crore | > 0 |
| `equity_folios_crore` | REAL | Equity-category folios in crore | > 0 |
| `debt_folios_crore` | REAL | Debt-category folios in crore | > 0 |
| `hybrid_folios_crore` | REAL | Hybrid-category folios in crore | > 0 |
| `others_folios_crore` | REAL | Other-category folios in crore | > 0 |

---

## 07 scheme_performance

**Source file:** `07_scheme_performance.csv`  
**SQLite table:** `scheme_performance`  
**Rows (cleaned):** 40  
**Grain:** One row per fund scheme (point-in-time snapshot).

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (FK) | Fund identifier | Valid amfi_code |
| `scheme_name` | TEXT | Fund scheme name | Free text |
| `fund_house` | TEXT | AMC name | Free text |
| `category` | TEXT | Fund category | Free text |
| `plan` | TEXT | Growth / IDCW | Growth / IDCW |
| `return_1yr_pct` | REAL | Trailing 1-year return (%) | Numeric; flagged if abs > 200 |
| `return_3yr_pct` | REAL | Trailing 3-year annualised return (%) | Numeric; flagged if abs > 100 |
| `return_5yr_pct` | REAL | Trailing 5-year annualised return (%) | Numeric |
| `benchmark_3yr_pct` | REAL | Benchmark 3-year annualised return (%) | Numeric |
| `alpha` | REAL | Jensen's Alpha – excess return vs benchmark | Numeric |
| `beta` | REAL | Systematic risk relative to market | Flagged if abs > 3 |
| `sharpe_ratio` | REAL | Risk-adjusted return (excess return / std dev) | Numeric |
| `sortino_ratio` | REAL | Downside risk-adjusted return | Numeric |
| `std_dev_ann_pct` | REAL | Annualised standard deviation of returns (%) | > 0 |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough decline (%) | Negative or zero |
| `aum_crore` | INTEGER | Fund AUM at snapshot date (₹ crore) | > 0 |
| `expense_ratio_pct` | REAL | Annual expense ratio charged to investors | 0.1 – 2.5 (validated) |
| `morningstar_rating` | INTEGER | Morningstar star rating | 1 – 5 |
| `risk_grade` | TEXT | Qualitative risk assessment | Low / Moderate / High |
| `anomaly_flag` | INTEGER | 1 = anomalous value detected in return/expense columns | 0 or 1 |

---

## 08 investor_transactions

**Source file:** `08_investor_transactions.csv`  
**SQLite table:** `investor_transactions`  
**Rows (cleaned):** 32,778  
**Grain:** One row per individual investor transaction.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `investor_id` | TEXT | Unique investor identifier | e.g., "INV003054" |
| `transaction_date` | DATE (TEXT ISO) | Date of the transaction | YYYY-MM-DD |
| `amfi_code` | INTEGER (FK) | Fund in which transaction was made | Valid amfi_code |
| `transaction_type` | TEXT | Standardised transaction category | SIP / Lumpsum / Redemption |
| `amount_inr` | INTEGER | Transaction amount in Indian Rupees | > 0 |
| `state` | TEXT | Indian state of the investor | Free text |
| `city` | TEXT | City of the investor | Free text |
| `city_tier` | TEXT | Tier classification of the city | Tier 1 / Tier 2 / Tier 3 |
| `age_group` | TEXT | Age bracket of the investor | e.g., "25-35" |
| `gender` | TEXT | Investor gender | Male / Female / Other |
| `annual_income_lakh` | REAL | Investor's annual income in lakh rupees | > 0 |
| `payment_mode` | TEXT | Payment instrument used | UPI / NEFT / Cheque / etc. |
| `kyc_status` | TEXT | KYC (Know Your Customer) compliance status | Verified / Pending / Rejected |

**Cleaning applied:**
- `transaction_type` standardised to title-case enum {SIP, Lumpsum, Redemption}.
- Dates parsed; rows with null dates dropped.
- Rows with `amount_inr ≤ 0` removed.
- Duplicates removed.

---

## 09 portfolio_holdings

**Source file:** `09_portfolio_holdings.csv`  
**SQLite table:** `portfolio_holdings`  
**Rows (cleaned):** 322  
**Grain:** One row per fund–stock holding at a portfolio snapshot date.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `amfi_code` | INTEGER (FK) | Fund identifier | Valid amfi_code |
| `stock_symbol` | TEXT | NSE/BSE trading symbol of the stock | e.g., "HDFCBANK" |
| `stock_name` | TEXT | Full company name | Free text |
| `sector` | TEXT | GICS/industry sector of the stock | e.g., "Financials" |
| `weight_pct` | REAL | Portfolio allocation to this stock (%) | 0 – 100 |
| `market_value_cr` | REAL | Market value of the holding (₹ crore) | > 0 |
| `current_price_inr` | REAL | Stock price at the snapshot date (₹) | > 0 |
| `portfolio_date` | DATE (TEXT ISO) | Date of the portfolio snapshot | YYYY-MM-DD |

---

## 10 benchmark_indices

**Source file:** `10_benchmark_indices.csv`  
**SQLite table:** `benchmark_indices`  
**Rows (cleaned):** 8,050  
**Grain:** One row per index per trading day.

| Column | Data Type | Business Definition | Allowed Values / Range |
|---|---|---|---|
| `date` | DATE (TEXT ISO) | Trading date | YYYY-MM-DD |
| `index_name` | TEXT | Name of the benchmark index | e.g., "NIFTY50", "SENSEX" |
| `close_value` | REAL | Closing index value on that date | > 0 |

---

## Cleaning Notes

| File | Key Cleaning Actions |
|---|---|
| `nav_history` | Date parse → sort → dedup → forward-fill calendar gaps → NAV > 0 check |
| `investor_transactions` | Standardise transaction_type enum → date parse → amount > 0 → dedup |
| `scheme_performance` | Numeric coercion of all return columns → anomaly flagging → expense_ratio 0.1–2.5% check |
| `fund_master` | Date parse for launch_date → dedup on amfi_code |
| `aum_by_fund_house` | Date parse → dedup |
| `monthly_sip_inflows` | Month parse → dedup → sort |
| `category_inflows` | Month parse → dedup |
| `industry_folio_count` | Month parse → dedup → sort |
| `portfolio_holdings` | Date parse → numeric coerce → dedup on (amfi_code, stock_symbol, date) |
| `benchmark_indices` | Date parse → close_value > 0 → dedup on (date, index_name) |

---

*Generated as part of Day 2 deliverables – Bluestock MF Capstone Internship.*
