"""STEP 4/5: validate and clean the raw CSV files.

Reads three files in the "standard format" (see docs/data_sources.md):
    upi_monthly.csv        (required)
    upi_apps_monthly.csv   (optional)
    upi_banks_monthly.csv  (optional)
plus data/reference/events.csv, and writes tidy versions to data/processed/.

Run on real data:    python src/clean_data.py
Run on sample data:  python src/clean_data.py --input data/sample
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

import config

SPEC = {
    "upi_monthly.csv": {
        "required": ["month", "volume_mn", "value_cr"],
        "optional": ["banks_live"],
        "key": ["month"],
        "out": "monthly_upi.csv",
    },
    "upi_apps_monthly.csv": {
        "required": ["month", "app_name", "volume_mn", "value_cr"],
        "optional": [],
        "key": ["month", "app_name"],
        "out": "app_monthly.csv",
    },
    "upi_banks_monthly.csv": {
        "required": ["month", "bank_name", "role", "volume_mn"],
        "optional": ["approved_pct", "business_decline_pct", "technical_decline_pct"],
        "key": ["month", "bank_name", "role"],
        "out": "bank_monthly.csv",
    },
}

errors: list[str] = []
warnings: list[str] = []


def to_number(series: pd.Series) -> pd.Series:
    """'1,234.5' -> 1234.5 ; junk -> NaN"""
    cleaned = series.astype(str).str.replace(",", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def clean_table(path: Path, spec: dict) -> pd.DataFrame | None:
    name = path.name
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]

    missing = [c for c in spec["required"] if c not in df.columns]
    if missing:
        errors.append(f"{name}: missing columns {missing}. Found: {list(df.columns)}")
        return None
    for c in spec["optional"]:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[spec["required"] + spec["optional"]].copy()

    # --- month -> first day of month ---
    parsed = pd.to_datetime(df["month"], errors="coerce")
    bad = parsed.isna().sum()
    if bad:
        errors.append(f"{name}: {bad} rows have an unreadable 'month'. Use YYYY-MM, e.g. 2024-05")
        return None
    df["month"] = parsed.dt.to_period("M").dt.to_timestamp()

    # --- numbers ---
    for c in df.columns:
        if c in ("month", "app_name", "bank_name", "role"):
            continue
        df[c] = to_number(df[c])
    if df[["volume_mn"]].isna().any().any():
        warnings.append(f"{name}: {int(df['volume_mn'].isna().sum())} rows with missing volume_mn dropped")
        df = df.dropna(subset=["volume_mn"])
    neg = (df["volume_mn"] < 0).sum()
    if neg:
        warnings.append(f"{name}: {neg} negative volumes dropped")
        df = df[df["volume_mn"] >= 0]

    # --- text columns ---
    if "app_name" in df.columns:
        key = df["app_name"].astype(str).str.strip()
        df["app_name"] = key.str.lower().map(config.APP_ALIASES).fillna(key)
    if "bank_name" in df.columns:
        df["bank_name"] = df["bank_name"].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    if "role" in df.columns:
        r = df["role"].astype(str).str.lower().str.strip()
        df["role"] = r.where(r.isin(["remitter", "beneficiary"]),
                             r.str.extract(r"(remitter|beneficiary)", expand=False))
        n_bad = df["role"].isna().sum()
        if n_bad:
            warnings.append(f"{name}: {n_bad} rows with unknown role dropped (use remitter / beneficiary)")
            df = df.dropna(subset=["role"])

    # --- percentage sanity ---
    for c in ("approved_pct", "business_decline_pct", "technical_decline_pct"):
        if c in df.columns:
            outside = ((df[c] < 0) | (df[c] > 100)).sum()
            if outside:
                warnings.append(f"{name}: {outside} values of {c} outside 0-100 (check units)")

    # --- duplicates ---
    dups = df.duplicated(subset=spec["key"], keep="last").sum()
    if dups:
        warnings.append(f"{name}: {dups} duplicate rows on {spec['key']} (kept the last one)")
        df = df.drop_duplicates(subset=spec["key"], keep="last")

    return df.sort_values(spec["key"]).reset_index(drop=True)


def extra_checks_monthly(df: pd.DataFrame) -> None:
    full = pd.date_range(df["month"].min(), df["month"].max(), freq="MS")
    gaps = full.difference(df["month"])
    if len(gaps):
        warnings.append("upi_monthly.csv: missing months: " + ", ".join(gaps.strftime("%Y-%m")))
    ticket = df["value_cr"] * 10 / df["volume_mn"]  # rupees per transaction
    weird = df[(ticket < 50) | (ticket > 20000)]
    if len(weird):
        warnings.append(
            f"upi_monthly.csv: {len(weird)} months have an odd average ticket (<Rs50 or >Rs20,000). "
            f"Check units! volume must be in MILLIONS, value in CRORE rupees. First: {weird['month'].iloc[0]:%Y-%m}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(config.RAW_DIR), help="folder with the raw CSVs")
    args = ap.parse_args()
    in_dir = Path(args.input)
    if not in_dir.is_absolute():
        in_dir = config.ROOT / in_dir
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Reading from: {in_dir}")
    if in_dir.resolve() == config.SAMPLE_DIR.resolve():
        print("!! SAMPLE (fake) data. Do not use any number from it in your README or resume. !!")

    for fname, spec in SPEC.items():
        path = in_dir / fname
        if not path.exists():
            if fname == "upi_monthly.csv":
                errors.append(f"{fname} not found in {in_dir} (this one is required)")
            else:
                print(f"[skip] {fname} not found (optional)")
                (config.PROCESSED_DIR / spec["out"]).unlink(missing_ok=True)
            continue
        df = clean_table(path, spec)
        if df is None:
            continue
        if fname == "upi_monthly.csv":
            extra_checks_monthly(df)
        if "app_name" in df.columns:
            print("   app names after cleaning:", ", ".join(sorted(df["app_name"].unique())))
        df.to_csv(config.PROCESSED_DIR / spec["out"], index=False)
        print(f"[ok] {fname}: {len(df)} rows, {df['month'].min():%Y-%m} to {df['month'].max():%Y-%m}")

    ev = pd.read_csv(config.REFERENCE_DIR / "events.csv")
    ev["month"] = pd.to_datetime(ev["month"]).dt.to_period("M").dt.to_timestamp()
    ev.to_csv(config.PROCESSED_DIR / "events.csv", index=False)
    print(f"[ok] events.csv: {len(ev)} rows")

    for w in warnings:
        print("[warning]", w)
    for e in errors:
        print("[ERROR]", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
