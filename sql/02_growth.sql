-- ======================================================================
-- 02 : Growth analysis on monthly_upi
-- Run:  python src/run_sql.py sql/02_growth.sql
-- ======================================================================

-- Q1. Month-on-month (MoM) and year-on-year (YoY) growth of volume and value
SELECT month,
       volume_mn,
       ROUND(100.0 * (volume_mn - LAG(volume_mn, 1)  OVER w) / NULLIF(LAG(volume_mn, 1)  OVER w, 0), 2) AS volume_mom_pct,
       ROUND(100.0 * (volume_mn - LAG(volume_mn, 12) OVER w) / NULLIF(LAG(volume_mn, 12) OVER w, 0), 2) AS volume_yoy_pct,
       ROUND(100.0 * (value_cr  - LAG(value_cr, 12)  OVER w) / NULLIF(LAG(value_cr, 12)  OVER w, 0), 2) AS value_yoy_pct
FROM monthly_upi
WINDOW w AS (ORDER BY month)
ORDER BY month DESC;

-- Q2. Average ticket size in rupees (value / volume). Falling = more small payments
SELECT month,
       volume_mn,
       value_cr,
       ROUND(value_cr * 10.0 / volume_mn, 0) AS avg_ticket_inr
FROM monthly_upi
ORDER BY month DESC;

-- Q3. 3-month moving average of volume (smooths out noise)
SELECT month,
       volume_mn,
       ROUND(AVG(volume_mn) OVER (ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 2) AS vol_3m_avg
FROM monthly_upi
ORDER BY month DESC;

-- Q4. Calendar-year totals and growth (months_in_data tells you if a year is partial)
WITH yearly AS (
    SELECT EXTRACT(YEAR FROM month)::INT AS year,
           COUNT(*)                      AS months_in_data,
           SUM(volume_mn)                AS volume_mn,
           SUM(value_cr)                 AS value_cr
    FROM monthly_upi
    GROUP BY 1
)
SELECT year,
       months_in_data,
       ROUND(volume_mn, 0) AS volume_mn,
       ROUND(value_cr, 0)  AS value_cr,
       ROUND(100.0 * (volume_mn - LAG(volume_mn) OVER (ORDER BY year)) / NULLIF(LAG(volume_mn) OVER (ORDER BY year), 0), 1) AS volume_growth_pct
FROM yearly
ORDER BY year;

-- Q5. Do festival months grow faster than other months? (JOIN with the events table)
WITH g AS (
    SELECT month,
           100.0 * (volume_mn - LAG(volume_mn) OVER (ORDER BY month)) / NULLIF(LAG(volume_mn) OVER (ORDER BY month), 0) AS mom_pct
    FROM monthly_upi
)
SELECT CASE WHEN e.month IS NOT NULL THEN 'festival month' ELSE 'other month' END AS month_type,
       COUNT(*)                 AS n_months,
       ROUND(AVG(g.mom_pct), 2) AS avg_mom_pct
FROM g
LEFT JOIN (SELECT DISTINCT month FROM events WHERE event_type = 'festival') e ON e.month = g.month
WHERE g.mom_pct IS NOT NULL AND g.month >= DATE '2019-01-01'
GROUP BY 1;

-- Q6. The 5 strongest and 5 weakest MoM growth months since 2019 (RANK)
WITH g AS (
    SELECT month,
           ROUND(100.0 * (volume_mn - LAG(volume_mn) OVER (ORDER BY month)) / NULLIF(LAG(volume_mn) OVER (ORDER BY month), 0), 2) AS mom_pct
    FROM monthly_upi
),
r AS (
    SELECT month, mom_pct,
           RANK() OVER (ORDER BY mom_pct DESC) AS rank_best,
           RANK() OVER (ORDER BY mom_pct ASC)  AS rank_worst
    FROM g
    WHERE mom_pct IS NOT NULL AND month >= DATE '2019-01-01'
)
SELECT month, mom_pct, rank_best, rank_worst
FROM r
WHERE rank_best <= 5 OR rank_worst <= 5
ORDER BY mom_pct DESC;
