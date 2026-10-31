"""STEP 4/5: load the cleaned CSVs from data/processed/ into PostgreSQL.

Each run is a FULL REBUILD: tables are emptied first, so running it again
(for example after swapping sample data for real data) never creates duplicates.

Run:  python src/load_to_postgres.py
"""
import sys

import pandas as pd
from sqlalchemy import create_engine, text

import config

TABLES = {
    "monthly_upi": ["month", "banks_live", "volume_mn", "value_cr"],
    "app_monthly": ["month", "app_name", "volume_mn", "value_cr"],
    "bank_monthly": ["month", "bank_name", "role", "volume_mn",
                     "approved_pct", "business_decline_pct", "technical_decline_pct"],
    "events": ["month", "event_name", "event_type", "notes"],
}


def main() -> int:
    if not (config.PROCESSED_DIR / "monthly_upi.csv").exists():
        print("[ERROR] data/processed/monthly_upi.csv not found. Run: python src/clean_data.py")
        return 1

    engine = create_engine(config.get_url())
    with engine.begin() as conn:  # one transaction: all or nothing
        conn.execute(text("TRUNCATE monthly_upi, app_monthly, bank_monthly, events RESTART IDENTITY"))
        for table, cols in TABLES.items():
            path = config.PROCESSED_DIR / f"{table}.csv"
            if not path.exists():
                print(f"[skip] {table}: no processed file")
                continue
            df = pd.read_csv(path, parse_dates=["month"])[cols]
            if "banks_live" in df.columns:
                df["banks_live"] = df["banks_live"].astype("Int64")
            df.to_sql(table, conn, if_exists="append", index=False, method="multi", chunksize=1000)
            print(f"[ok] {table}: {len(df)} rows loaded")
    engine.dispose()
    return 0


if __name__ == "__main__":
    sys.exit(main())
