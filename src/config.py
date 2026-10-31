"""Central settings: folder paths and database connection.

Everything else imports from here, so you only change things in one place.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")  # reads DB_USER, DB_PASSWORD ... from the .env file

RAW_DIR = ROOT / "data" / "raw"
SAMPLE_DIR = ROOT / "data" / "sample"
PROCESSED_DIR = ROOT / "data" / "processed"
REFERENCE_DIR = ROOT / "data" / "reference"
SQL_DIR = ROOT / "sql"

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "upi_analytics")


def get_url(dbname: str | None = None) -> URL:
    """Build a safe connection URL (handles special characters in the password)."""
    return URL.create(
        "postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=dbname or DB_NAME,
    )


# Different spellings of the same app in NPCI files -> one clean name.
# If clean_data.py prints an app name you don't recognise, add it here.
APP_ALIASES = {
    "phonepe": "PhonePe",
    "phone pe": "PhonePe",
    "google pay": "Google Pay",
    "googlepay": "Google Pay",
    "gpay": "Google Pay",
    "google pay (gpay)": "Google Pay",
    "paytm": "Paytm",
    "paytm payments bank app": "Paytm",
    "paytm app": "Paytm",
    "amazon pay": "Amazon Pay",
    "cred": "CRED",
    "navi": "Navi",
    "navi app": "Navi",
    "bhim": "BHIM",
    "bhim upi": "BHIM",
    "whatsapp": "WhatsApp",
    "whatsapp pay": "WhatsApp",
}
