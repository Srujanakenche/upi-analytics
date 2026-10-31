-- ======================================================================
-- 04 : Bank performance analysis on bank_monthly
-- Technical decline = the system failed (bank server down, timeout)
-- Business decline  = the bank refused (low balance, wrong PIN, limit)
-- Run:  python src/run_sql.py sql/04_banks.sql
-- ======================================================================

-- Q1. Top 10 remitter banks by volume in the latest month
SELECT bank_name,
       volume_mn,
       approved_pct,
       business_decline_pct,
       technical_decline_pct
FROM bank_monthly
WHERE role = 'remitter'
  AND month = (SELECT MAX(month) FROM bank_monthly)
ORDER BY volume_mn DESC
LIMIT 10;

-- Q2. Volume-weighted technical decline rate over the last 12 months (big banks matter more)
SELECT bank_name,
       ROUND(SUM(volume_mn), 0) AS volume_12m_mn,
       ROUND(SUM(volume_mn * technical_decline_pct) / SUM(volume_mn), 2) AS weighted_tech_decline_pct
FROM bank_monthly
WHERE role = 'remitter'
  AND month > (SELECT MAX(month) FROM bank_monthly) - INTERVAL '12 months'
GROUP BY bank_name
HAVING SUM(volume_mn) > 0
ORDER BY weighted_tech_decline_pct DESC;

-- Q3. Banks whose technical declines got WORSE: last 6 months vs the 6 months before
WITH ref AS (
    SELECT MAX(month) AS latest FROM bank_monthly
),
w AS (
    SELECT b.bank_name,
           AVG(CASE WHEN b.month > ref.latest - INTERVAL '6 months'
                    THEN b.technical_decline_pct END) AS recent_6m,
           AVG(CASE WHEN b.month <= ref.latest - INTERVAL '6 months'
                     AND b.month >  ref.latest - INTERVAL '12 months'
                    THEN b.technical_decline_pct END) AS prior_6m
    FROM bank_monthly b
    CROSS JOIN ref
    WHERE b.role = 'remitter'
      AND b.month > ref.latest - INTERVAL '12 months'
    GROUP BY b.bank_name
)
SELECT bank_name,
       ROUND(prior_6m, 2)            AS prior_6m,
       ROUND(recent_6m, 2)           AS recent_6m,
       ROUND(recent_6m - prior_6m, 2) AS change_pp
FROM w
WHERE recent_6m IS NOT NULL AND prior_6m IS NOT NULL
ORDER BY change_pp DESC;

-- Q4. Remitter vs beneficiary: which side fails more on average? (latest 12 months)
SELECT role,
       ROUND(AVG(technical_decline_pct), 2) AS avg_technical_decline_pct,
       ROUND(AVG(business_decline_pct), 2)  AS avg_business_decline_pct
FROM bank_monthly
WHERE month > (SELECT MAX(month) FROM bank_monthly) - INTERVAL '12 months'
GROUP BY role;
