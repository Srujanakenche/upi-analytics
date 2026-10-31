"""STEP 3: create the database (if missing) and the tables.

Run:  python src/init_db.py
Safe to run many times (it never deletes data).
"""
from sqlalchemy import create_engine, text

import config


def create_database_if_missing() -> None:
    # Connect to the default "postgres" database, because our own DB may not exist yet.
    admin = create_engine(config.get_url("postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": config.DB_NAME}
        ).scalar()
        if exists:
            print(f"[ok] database '{config.DB_NAME}' already exists")
        else:
            conn.execute(text(f'CREATE DATABASE "{config.DB_NAME}"'))
            print(f"[ok] created database '{config.DB_NAME}'")
    admin.dispose()


def create_tables() -> None:
    engine = create_engine(config.get_url())
    schema_sql = (config.SQL_DIR / "01_schema.sql").read_text(encoding="utf-8")
    with engine.begin() as conn:  # begin() = auto-commit at the end
        conn.exec_driver_sql(schema_sql)
    print("[ok] tables created (monthly_upi, app_monthly, bank_monthly, events)")
    engine.dispose()


if __name__ == "__main__":
    create_database_if_missing()
    create_tables()
