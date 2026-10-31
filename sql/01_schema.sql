-- ======================================================================
-- UPI Analytics : database schema
-- Units used everywhere:
--   volume_mn = number of transactions in MILLIONS
--   value_cr  = value of transactions in CRORE rupees (1 crore = 10 million)
--   month     = always the FIRST day of the month (2024-05-01 means May 2024)
-- ======================================================================

CREATE TABLE IF NOT EXISTS monthly_upi (
    month       DATE PRIMARY KEY CHECK (EXTRACT(DAY FROM month) = 1),
    banks_live  INT,
    volume_mn   NUMERIC(14,2) NOT NULL CHECK (volume_mn >= 0),
    value_cr    NUMERIC(16,2) NOT NULL CHECK (value_cr  >= 0)
);

CREATE TABLE IF NOT EXISTS app_monthly (
    month       DATE NOT NULL CHECK (EXTRACT(DAY FROM month) = 1),
    app_name    TEXT NOT NULL,
    volume_mn   NUMERIC(14,2) NOT NULL CHECK (volume_mn >= 0),
    value_cr    NUMERIC(16,2) CHECK (value_cr >= 0),
    PRIMARY KEY (month, app_name)
);

CREATE TABLE IF NOT EXISTS bank_monthly (
    month                  DATE NOT NULL CHECK (EXTRACT(DAY FROM month) = 1),
    bank_name              TEXT NOT NULL,
    role                   TEXT NOT NULL CHECK (role IN ('remitter', 'beneficiary')),
    volume_mn              NUMERIC(14,2) NOT NULL CHECK (volume_mn >= 0),
    approved_pct           NUMERIC(6,2),
    business_decline_pct   NUMERIC(6,2),
    technical_decline_pct  NUMERIC(6,2),
    PRIMARY KEY (month, bank_name, role)
);

CREATE TABLE IF NOT EXISTS events (
    event_id    SERIAL PRIMARY KEY,
    month       DATE NOT NULL,
    event_name  TEXT NOT NULL,
    event_type  TEXT NOT NULL,   -- milestone / policy / product / macro / festival
    notes       TEXT
);
