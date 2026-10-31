# Data sources and the "standard format"

All scripts expect your data in 3 simple CSV files inside `data/raw/`.
You download the numbers from NPCI / RBI, then paste them into these formats (Excel is fine,
save as CSV UTF-8).

## Units (very important)
| Column | Unit |
|---|---|
| `volume_mn` | number of transactions in **millions** (24 billion = 24000) |
| `value_cr`  | value in **crore rupees** (Rs 29 lakh crore = 2900000) |
| `month`     | write as `YYYY-MM`, e.g. `2025-08` |
| `*_pct`     | percent as a plain number (96.5 means 96.5%) |

## File 1 (required): `data/raw/upi_monthly.csv`
```
month,banks_live,volume_mn,value_cr
2023-03,414,8653.97,1404950.59
```
`banks_live` is optional (leave empty if you don't have it).

## File 2 (optional, needed for the app analysis): `data/raw/upi_apps_monthly.csv`
```
month,app_name,volume_mn,value_cr
2024-08,PhonePe,...,...
```
Name spellings are cleaned automatically (see `APP_ALIASES` in `src/config.py`).

## File 3 (optional, needed for the bank analysis): `data/raw/upi_banks_monthly.csv`
```
month,bank_name,role,volume_mn,approved_pct,business_decline_pct,technical_decline_pct
2024-08,State Bank of India,remitter,...,...,...,...
```
`role` is `remitter` or `beneficiary`.

## Where to get the numbers
- NPCI UPI Product Statistics: https://www.npci.org.in/what-we-do/upi/product-statistics
  (monthly volume, value, banks live). Also see https://www.npci.org.in/statistics/monthly-metrics
- NPCI also publishes app-wise (TPAP) and bank-wise (remitter / beneficiary) UPI statistics under the
  same statistics section of the website. App-wise and bank-wise history usually starts later than 2016,
  so those tables will have fewer months. That is normal.
- RBI DBIE (Database on Indian Economy) for wider payment-system context (optional, stretch goal).

NPCI's tables may be loaded by a script on the page, so a plain copy or download may need a few tries.
Copy the table into Excel, fix the columns and units, and save as CSV.

## Reference file (already included): `data/reference/events.csv`
Festivals, launches and policy events used for the seasonality analysis.
Double-check any date you plan to quote in your README.

## Rules for your repo
- Write the NPCI page URL and the date you downloaded the data in the README (a "Data" section).
- Never use `data/sample/` numbers anywhere public. They are fake.
