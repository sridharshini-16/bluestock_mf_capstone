-- =============================================================
-- Bluestock MF Capstone – SQLite Star Schema
-- File: schema.sql
-- =============================================================

-- ── Dimension: Fund ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code          INTEGER PRIMARY KEY,
    fund_house         TEXT    NOT NULL,
    scheme_name        TEXT    NOT NULL,
    category           TEXT,
    sub_category       TEXT,
    plan               TEXT,
    launch_date        TEXT,
    benchmark          TEXT,
    expense_ratio_pct  REAL,
    exit_load_pct      REAL,
    min_sip_amount     INTEGER,
    min_lumpsum_amount INTEGER,
    fund_manager       TEXT,
    risk_category      TEXT,
    sebi_category_code TEXT
);

-- ── Dimension: Date ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_id      TEXT PRIMARY KEY,   -- ISO date YYYY-MM-DD
    year         INTEGER NOT NULL,
    quarter      INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    month_name   TEXT    NOT NULL,
    week         INTEGER NOT NULL,
    day          INTEGER NOT NULL,
    day_of_week  TEXT    NOT NULL,
    is_weekend   INTEGER NOT NULL DEFAULT 0  -- 1 = weekend
);

-- ── Fact: NAV (daily) ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code INTEGER NOT NULL,
    date      TEXT    NOT NULL,
    nav       REAL    NOT NULL CHECK (nav > 0),
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (date)      REFERENCES dim_date (date_id),
    UNIQUE (amfi_code, date)
);

-- ── Fact: Transactions ────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id             INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id        TEXT    NOT NULL,
    transaction_date   TEXT    NOT NULL,
    amfi_code          INTEGER NOT NULL,
    transaction_type   TEXT    NOT NULL CHECK (
                           transaction_type IN ('SIP', 'Lumpsum', 'Redemption')
                       ),
    amount_inr         REAL    NOT NULL CHECK (amount_inr > 0),
    state              TEXT,
    city               TEXT,
    city_tier          TEXT,
    age_group          TEXT,
    gender             TEXT,
    annual_income_lakh REAL,
    payment_mode       TEXT,
    kyc_status         TEXT    CHECK (kyc_status IN ('Verified', 'Pending', 'Rejected')),
    FOREIGN KEY (amfi_code)        REFERENCES dim_fund (amfi_code),
    FOREIGN KEY (transaction_date) REFERENCES dim_date (date_id)
);

-- ── Fact: Scheme Performance ──────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code          INTEGER NOT NULL,
    scheme_name        TEXT,
    fund_house         TEXT,
    category           TEXT,
    plan               TEXT,
    return_1yr_pct     REAL,
    return_3yr_pct     REAL,
    return_5yr_pct     REAL,
    benchmark_3yr_pct  REAL,
    alpha              REAL,
    beta               REAL,
    sharpe_ratio       REAL,
    sortino_ratio      REAL,
    std_dev_ann_pct    REAL,
    max_drawdown_pct   REAL,
    aum_crore          INTEGER,
    expense_ratio_pct  REAL    CHECK (expense_ratio_pct BETWEEN 0.1 AND 2.5),
    morningstar_rating INTEGER CHECK (morningstar_rating BETWEEN 1 AND 5),
    risk_grade         TEXT,
    anomaly_flag       INTEGER DEFAULT 0,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

-- ── Fact: AUM by Fund House ────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date           TEXT    NOT NULL,
    fund_house     TEXT    NOT NULL,
    aum_lakh_crore REAL,
    aum_crore      INTEGER,
    num_schemes    INTEGER,
    FOREIGN KEY (date) REFERENCES dim_date (date_id)
);

-- ── Supporting: SIP Inflows ───────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_sip_inflows (
    sip_id                     INTEGER PRIMARY KEY AUTOINCREMENT,
    month                      TEXT    NOT NULL,
    sip_inflow_crore           INTEGER,
    active_sip_accounts_crore  REAL,
    new_sip_accounts_lakh      REAL,
    sip_aum_lakh_crore         REAL,
    yoy_growth_pct             REAL
);

-- ── Supporting: Category Inflows ─────────────────────────────
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    cat_id           INTEGER PRIMARY KEY AUTOINCREMENT,
    month            TEXT    NOT NULL,
    category         TEXT    NOT NULL,
    net_inflow_crore REAL
);

-- ── Supporting: Portfolio Holdings ───────────────────────────
CREATE TABLE IF NOT EXISTS fact_portfolio_holdings (
    holding_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code         INTEGER NOT NULL,
    stock_symbol      TEXT    NOT NULL,
    stock_name        TEXT,
    sector            TEXT,
    weight_pct        REAL,
    market_value_cr   REAL,
    current_price_inr REAL,
    portfolio_date    TEXT,
    FOREIGN KEY (amfi_code) REFERENCES dim_fund (amfi_code)
);

-- ── Supporting: Benchmark Indices ────────────────────────────
CREATE TABLE IF NOT EXISTS fact_benchmark (
    bench_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    date        TEXT    NOT NULL,
    index_name  TEXT    NOT NULL,
    close_value REAL    NOT NULL CHECK (close_value > 0),
    UNIQUE (date, index_name)
);
