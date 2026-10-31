-- ======================================================================
-- 05 : Views that Power BI will connect to
-- A view is a saved query. Power BI reads these like normal tables.
-- Run:  python src/run_sql.py sql/05_views_for_powerbi.sql
-- ======================================================================

-- Month table (a "calendar") so Power BI can slice by year and month
CREATE OR REPLACE VIEW vw_dim_month AS
SELECT d::DATE                          AS month,
       EXTRACT(YEAR FROM d)::INT        AS year,
       EXTRACT(MONTH FROM d)::INT       AS month_num,
       TO_CHAR(d, 'Mon')                AS month_name,
       TO_CHAR(d, 'YYYY-MM')            AS year_month
FROM generate_series(
        (SELECT MIN(month) FROM monthly_upi),
        (SELECT MAX(month) FROM monthly_upi) + INTERVAL '12 months',
        INTERVAL '1 month') AS d;

-- Main KPI view: growth, ticket size, moving average, festival flag
CREATE OR REPLACE VIEW vw_monthly_kpis AS
SELECT m.month,
       m.banks_live,
       m.volume_mn,
       m.value_cr,
       ROUND(m.value_cr * 10.0 / NULLIF(m.volume_mn, 0), 0)                                              AS avg_ticket_inr,
       ROUND(100.0 * (m.volume_mn - LAG(m.volume_mn, 1)  OVER w) / NULLIF(LAG(m.volume_mn, 1)  OVER w, 0), 2) AS volume_mom_pct,
       ROUND(100.0 * (m.volume_mn - LAG(m.volume_mn, 12) OVER w) / NULLIF(LAG(m.volume_mn, 12) OVER w, 0), 2) AS volume_yoy_pct,
       ROUND(100.0 * (m.value_cr  - LAG(m.value_cr, 12)  OVER w) / NULLIF(LAG(m.value_cr, 12)  OVER w, 0), 2) AS value_yoy_pct,
       ROUND(AVG(m.volume_mn) OVER (ORDER BY m.month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2)       AS vol_3m_avg,
       EXISTS (SELECT 1 FROM events e WHERE e.month = m.month AND e.event_type = 'festival')              AS is_festival_month
FROM monthly_upi m
WINDOW w AS (ORDER BY m.month);

-- App market share per month
CREATE OR REPLACE VIEW vw_app_share AS
SELECT month,
       app_name,
       volume_mn,
       value_cr,
       ROUND(100.0 * volume_mn / SUM(volume_mn) OVER (PARTITION BY month), 2) AS share_pct,
       RANK() OVER (PARTITION BY month ORDER BY volume_mn DESC)               AS rank_in_month
FROM app_monthly;

-- Bank performance (decline rates are already in the table)
CREATE OR REPLACE VIEW vw_bank_performance AS
SELECT month,
       bank_name,
       role,
       volume_mn,
       approved_pct,
       business_decline_pct,
       technical_decline_pct,
       RANK() OVER (PARTITION BY month, role ORDER BY volume_mn DESC) AS volume_rank
FROM bank_monthly;

-- Events, so you can show milestones on charts
CREATE OR REPLACE VIEW vw_events AS
SELECT month, event_name, event_type, notes FROM events;
