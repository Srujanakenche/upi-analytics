# UPI Transaction Analytics (India)

End-to-end analytics project on India's UPI payments data: PostgreSQL for storage and analysis,
Python for cleaning and forecasting, Power BI for the dashboard.

> Status: work in progress (see checklist below).

## Business questions
1. How fast is UPI growing, in volume and in value?
2. Is the average payment getting smaller?
3. Which apps dominate, and is the market getting more concentrated?
4. Which banks have the highest technical decline rates, and is it getting better or worse?
5. Do festival months behave differently?
6. What will volume look like over the next 6 months, and how reliable is that forecast?

## Tech stack
PostgreSQL | Python (pandas, SQLAlchemy, statsmodels) | Power BI | Git/GitHub

## Project structure
```
data/raw/         your downloaded NPCI/RBI CSVs (standard format, see docs/data_sources.md)
data/reference/   hand-made reference tables (events.csv)
data/processed/   cleaned CSVs (generated)
sql/              schema, analysis queries, Power BI views
src/              Python scripts (clean, load, forecast)
dashboard/        Power BI file (.pbix) and screenshots
docs/             data notes and images
```

## How to run
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (Mac/Linux: source .venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env             # then edit .env with your PostgreSQL password

python src/init_db.py              # create database + tables
python src/clean_data.py           # validate and clean data/raw -> data/processed
python src/load_to_postgres.py     # load into PostgreSQL
python src/run_sql.py sql/02_growth.sql
python src/run_sql.py sql/03_apps.sql
python src/run_sql.py sql/04_banks.sql
python src/run_sql.py sql/05_views_for_powerbi.sql
python src/forecast.py             # backtest + 6-month forecast
```

## Progress checklist
- [x] Step 1: Repo and project skeleton
- [x] Step 2: PostgreSQL and Python environment
- [x] Step 3: Database and tables created
- [x] Step 4: Pipeline tested with sample data
- [x] Step 5: Real NPCI data collected and loaded
- [x] Step 6: SQL analysis
- [x] Step 7: Forecast
- [x] Step 8: Power BI dashboard
- [x] Step 9: Insights and README finished

## Data
Source: NPCI UPI statistics (add the exact page URL and download date here).

## Key findings
_To be filled in with real results after the analysis._

## Limitations
- Public data is aggregated (monthly totals per app and per bank). There is no user-level data.
- App and bank history starts later than the overall monthly series.
- Forecasts are statistical extrapolations and do not know about future policy changes.
