-- ======================================================================
-- 03 : App market analysis on app_monthly
-- Note: shares are calculated among the apps present in your file.
-- Run:  python src/run_sql.py sql/03_apps.sql
-- ======================================================================

-- Q1. Market share of every app in the latest month
SELECT app_name,
       volume_mn,
       ROUND(100.0 * volume_mn / SUM(volume_mn) OVER (), 2) AS share_pct,
       RANK() OVER (ORDER BY volume_mn DESC)                AS rank
FROM app_monthly
WHERE month = (SELECT MAX(month) FROM app_monthly)
ORDER BY volume_mn DESC;

-- Q2. Combined share of the top 3 apps, month by month
WITH s AS (
    SELECT month, app_name,
           100.0 * volume_mn / SUM(volume_mn) OVER (PARTITION BY month) AS share_pct,
           ROW_NUMBER() OVER (PARTITION BY month ORDER BY volume_mn DESC) AS rn
    FROM app_monthly
)
SELECT month, ROUND(SUM(share_pct), 2) AS top3_share_pct
FROM s
WHERE rn <= 3
GROUP BY month
ORDER BY month DESC;

-- Q3. HHI (market concentration) per month. 10000 = monopoly. Above 2500 = highly concentrated
WITH s AS (
    SELECT month, 100.0 * volume_mn / SUM(volume_mn) OVER (PARTITION BY month) AS share_pct
    FROM app_monthly
)
SELECT month, ROUND(SUM(POWER(share_pct, 2))::NUMERIC, 0) AS hhi
FROM s
GROUP BY month
ORDER BY month DESC;

-- Q4. Who gained or lost share in the last 12 months? (percentage points)
WITH s AS (
    SELECT month, app_name,
           100.0 * volume_mn / SUM(volume_mn) OVER (PARTITION BY month) AS share_pct
    FROM app_monthly
),
cmp AS (
    SELECT app_name, month, share_pct,
           LAG(share_pct, 12) OVER (PARTITION BY app_name ORDER BY month) AS share_12m_ago
    FROM s
)
SELECT app_name,
       ROUND(share_12m_ago, 2)             AS share_12m_ago,
       ROUND(share_pct, 2)                 AS share_now,
       ROUND(share_pct - share_12m_ago, 2) AS change_pp
FROM cmp
WHERE month = (SELECT MAX(month) FROM app_monthly) AND share_12m_ago IS NOT NULL
ORDER BY change_pp DESC;

-- Q5. Average ticket size per app in the latest month (rupees per transaction)
SELECT app_name,
       ROUND(value_cr * 10.0 / NULLIF(volume_mn, 0), 0) AS avg_ticket_inr
FROM app_monthly
WHERE month = (SELECT MAX(month) FROM app_monthly)
ORDER BY avg_ticket_inr DESC;
