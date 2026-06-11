-- =============================================================
-- Bluestock MF Capstone – Analytical SQL Queries
-- File: queries.sql
-- Run against: bluestock_mf.db
-- =============================================================

-- ── Query 1: Top 5 Fund Houses by Latest AUM ─────────────────
-- Business: Identify market leaders by assets under management.
SELECT
    fund_house,
    SUM(aum_crore)          AS total_aum_crore,
    ROUND(SUM(aum_lakh_crore), 2) AS total_aum_lakh_crore,
    SUM(num_schemes)        AS total_schemes
FROM aum_by_fund_house
WHERE date = (SELECT MAX(date) FROM aum_by_fund_house)
GROUP BY fund_house
ORDER BY total_aum_crore DESC
LIMIT 5;

-- ── Query 2: Average NAV per Calendar Month (per fund) ────────
-- Business: Track monthly price level of each mutual fund scheme.
SELECT
    amfi_code,
    SUBSTR(date, 1, 7)          AS year_month,
    ROUND(AVG(nav), 4)          AS avg_nav,
    ROUND(MIN(nav), 4)          AS min_nav,
    ROUND(MAX(nav), 4)          AS max_nav
FROM nav_history
GROUP BY amfi_code, SUBSTR(date, 1, 7)
ORDER BY amfi_code, year_month;

-- ── Query 3: SIP Year-on-Year Growth ─────────────────────────
-- Business: Measure the annual expansion of SIP culture in India.
SELECT
    SUBSTR(month, 1, 4)             AS year,
    SUM(sip_inflow_crore)           AS annual_sip_crore,
    ROUND(AVG(yoy_growth_pct), 2)   AS avg_yoy_growth_pct,
    ROUND(AVG(active_sip_accounts_crore), 3) AS avg_active_sip_accounts_cr
FROM monthly_sip_inflows
GROUP BY SUBSTR(month, 1, 4)
ORDER BY year;

-- ── Query 4: Total Transactions by State ─────────────────────
-- Business: Understand geographic distribution of mutual fund investments.
SELECT
    state,
    COUNT(*)                        AS num_transactions,
    ROUND(SUM(amount_inr) / 1e7, 2) AS total_amount_crore,
    ROUND(AVG(amount_inr), 0)       AS avg_ticket_inr
FROM investor_transactions
GROUP BY state
ORDER BY num_transactions DESC;

-- ── Query 5: Funds with Expense Ratio < 1% ────────────────────
-- Business: Surface cost-efficient funds for investor recommendations.
SELECT
    f.amfi_code,
    f.scheme_name,
    f.fund_house,
    f.category,
    f.expense_ratio_pct,
    p.return_3yr_pct,
    p.sharpe_ratio,
    p.morningstar_rating
FROM fund_master f
LEFT JOIN scheme_performance p USING (amfi_code)
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;

-- ── Query 6: Monthly Net Inflows by Category ──────────────────
-- Business: Spot which fund categories are gaining/losing investor money.
SELECT
    month,
    category,
    ROUND(net_inflow_crore, 2)  AS net_inflow_crore
FROM category_inflows
ORDER BY month DESC, net_inflow_crore DESC;

-- ── Query 7: Top 10 Performing Funds by 3-Year Return ─────────
-- Business: Rank wealth-creators for long-term investors.
SELECT
    amfi_code,
    scheme_name,
    fund_house,
    category,
    return_3yr_pct,
    alpha,
    sharpe_ratio,
    expense_ratio_pct,
    morningstar_rating
FROM scheme_performance
ORDER BY return_3yr_pct DESC
LIMIT 10;

-- ── Query 8: Transaction Breakdown by Type and City Tier ──────
-- Business: Understand SIP vs Lumpsum vs Redemption split across
--            metros, Tier-2, and Tier-3 cities.
SELECT
    city_tier,
    transaction_type,
    COUNT(*)                            AS num_txns,
    ROUND(SUM(amount_inr) / 1e7, 2)    AS total_amount_crore,
    ROUND(AVG(amount_inr), 0)           AS avg_amount_inr
FROM investor_transactions
GROUP BY city_tier, transaction_type
ORDER BY city_tier, transaction_type;

-- ── Query 9: Sector Concentration in Portfolio Holdings ───────
-- Business: Identify which sectors dominate mutual fund portfolios
--            and flag over-concentration risk.
SELECT
    sector,
    COUNT(DISTINCT amfi_code)       AS num_funds_holding,
    ROUND(AVG(weight_pct), 2)       AS avg_weight_pct,
    ROUND(SUM(market_value_cr), 2)  AS total_market_value_cr
FROM portfolio_holdings
GROUP BY sector
ORDER BY total_market_value_cr DESC;

-- ── Query 10: NAV vs Benchmark – Monthly Alpha Approximation ──
-- Business: Compare fund NAV growth to benchmark index to measure
--            active management value.
WITH nav_monthly AS (
    SELECT
        amfi_code,
        SUBSTR(date, 1, 7)  AS ym,
        FIRST_VALUE(nav) OVER (
            PARTITION BY amfi_code, SUBSTR(date, 1, 7)
            ORDER BY date
        )                   AS nav_start,
        LAST_VALUE(nav) OVER (
            PARTITION BY amfi_code, SUBSTR(date, 1, 7)
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                   AS nav_end
    FROM nav_history
),
fund_monthly_return AS (
    SELECT
        amfi_code,
        ym,
        ROUND((nav_end - nav_start) * 100.0 / nav_start, 2) AS fund_monthly_return_pct
    FROM nav_monthly
    GROUP BY amfi_code, ym
),
bench_monthly AS (
    SELECT
        SUBSTR(date, 1, 7)  AS ym,
        index_name,
        FIRST_VALUE(close_value) OVER (
            PARTITION BY SUBSTR(date, 1, 7), index_name
            ORDER BY date
        )                   AS idx_start,
        LAST_VALUE(close_value) OVER (
            PARTITION BY SUBSTR(date, 1, 7), index_name
            ORDER BY date
            ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
        )                   AS idx_end
    FROM benchmark_indices
),
bench_return AS (
    SELECT
        ym,
        index_name,
        ROUND((idx_end - idx_start) * 100.0 / idx_start, 2) AS bench_return_pct
    FROM bench_monthly
    WHERE index_name = 'NIFTY50'
    GROUP BY ym
)
SELECT
    f.amfi_code,
    fm.scheme_name,
    f.ym,
    f.fund_monthly_return_pct,
    b.bench_return_pct,
    ROUND(f.fund_monthly_return_pct - b.bench_return_pct, 2) AS monthly_alpha
FROM fund_monthly_return f
JOIN bench_return b ON f.ym = b.ym
JOIN (SELECT DISTINCT amfi_code, scheme_name FROM scheme_performance) fm
     ON f.amfi_code = fm.amfi_code
ORDER BY f.ym DESC, monthly_alpha DESC
LIMIT 100;
