"""STEP 4: generate SYNTHETIC sample data so you can test the whole pipeline.

!!! THIS DATA IS FAKE. Never put it in your README, dashboard screenshots or resume. !!!
It is only for checking that clean -> load -> SQL -> Power BI all work.
Once your real NPCI data is ready, you replace it (see docs/data_sources.md).

Run:  python src/make_sample_data.py
"""
import numpy as np
import pandas as pd

import config

rng = np.random.default_rng(42)
config.SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

months = pd.period_range("2016-04", "2026-09", freq="M").to_timestamp()
n = len(months)
t = np.arange(n)

# ---- monthly totals: S-shaped (logistic) growth + seasonality + noise -----------
vol = 24700 / (1 + np.exp(-0.09 * (t - 82)))
season = {1: 1.00, 2: 0.95, 3: 1.03, 4: 0.99, 5: 1.01, 6: 0.99,
          7: 1.00, 8: 1.02, 9: 1.00, 10: 1.04, 11: 1.03, 12: 1.04}
vol = vol * np.array([season[m.month] for m in months])
vol = vol * (months.days_in_month / 30)
vol = vol * rng.normal(1.0, 0.012, n)
ticket = 1250 + 1800 * np.exp(-t / 30)              # average rupees per transaction
value_cr = vol * ticket / 10                         # value in crore rupees
banks_live = (21 + 650 * (1 - np.exp(-t / 40))).astype(int)

monthly = pd.DataFrame({
    "month": months.strftime("%Y-%m"),
    "banks_live": banks_live,
    "volume_mn": vol.round(2),
    "value_cr": value_cr.round(2),
})
monthly.to_csv(config.SAMPLE_DIR / "upi_monthly.csv", index=False)

# ---- app-wise market share (starts Jan 2021) ------------------------------------
app_months = months[months >= "2021-01-01"]
k = np.linspace(0, 1, len(app_months))
shares = {
    "PhonePe":    35 + 13 * k,
    "Google Pay": 40 - 3 * k,
    "Paytm":      17 - 10 * k,
    "Navi":       0.2 + 1.8 * k,
    "CRED":       0.3 + 0.7 * k,
    "Amazon Pay": 1.5 - 0.3 * k,
    "BHIM":       1.5 - 0.7 * k,
}
shares["Others"] = 100 - sum(shares.values())
rows = []
for j, m in enumerate(app_months):
    row = monthly.loc[monthly.month == m.strftime("%Y-%m")].iloc[0]
    for app, s in shares.items():
        sh = max(s[j] + rng.normal(0, 0.2), 0.05) / 100
        rows.append((m.strftime("%Y-%m"), app, round(row.volume_mn * sh, 2),
                     round(row.value_cr * sh * rng.normal(1.0, 0.03), 2)))
pd.DataFrame(rows, columns=["month", "app_name", "volume_mn", "value_cr"]) \
    .to_csv(config.SAMPLE_DIR / "upi_apps_monthly.csv", index=False)

# ---- bank-wise performance (starts Jan 2022) ------------------------------------
banks = {"State Bank of India": 0.26, "HDFC Bank": 0.11, "ICICI Bank": 0.08,
         "Axis Bank": 0.07, "Bank of Baroda": 0.05, "Punjab National Bank": 0.05,
         "Kotak Mahindra Bank": 0.04, "Canara Bank": 0.04, "Union Bank of India": 0.03,
         "Yes Bank": 0.03, "IndusInd Bank": 0.02, "Bank of India": 0.02}
base_tech = {b: rng.uniform(0.3, 2.0) for b in banks}
base_bus = {b: rng.uniform(1.0, 3.0) for b in banks}
rows = []
for m in months[months >= "2022-01-01"]:
    tot = monthly.loc[monthly.month == m.strftime("%Y-%m"), "volume_mn"].iloc[0]
    for role in ("remitter", "beneficiary"):
        for b, sh in banks.items():
            tech = max(base_tech[b] + rng.normal(0, 0.15), 0.05)
            bus = max(base_bus[b] + rng.normal(0, 0.2), 0.05)
            rows.append((m.strftime("%Y-%m"), b, role,
                         round(tot * sh * rng.normal(1, 0.02), 2),
                         round(100 - tech - bus, 2), round(bus, 2), round(tech, 2)))
pd.DataFrame(rows, columns=["month", "bank_name", "role", "volume_mn", "approved_pct",
                            "business_decline_pct", "technical_decline_pct"]) \
    .to_csv(config.SAMPLE_DIR / "upi_banks_monthly.csv", index=False)

print(f"[ok] wrote 3 SYNTHETIC files to {config.SAMPLE_DIR}")
print("     remember: this is fake data, only for testing the pipeline.")
