"""Run a .sql file and print the result of every query in the terminal.

Handy for learning: you see each query's title (the comment above it) and its output.

Run:  python src/run_sql.py sql/02_growth.sql
      python src/run_sql.py sql/02_growth.sql --rows 40
(You can also paste the same queries into pgAdmin's Query Tool.)
"""
import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

import config


def split_statements(sql: str):
    """Yield (title, statement). Statements end with ';'. Comments start with '--'.
    The title is the comment block written directly above a query (a blank line resets it)."""
    for chunk in sql.split(";"):
        title_lines, body_lines = [], []
        for line in chunk.strip().splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                if not body_lines:
                    title_lines.append(stripped.lstrip("- ").strip())
            elif not stripped:
                if not body_lines:
                    title_lines = []
            else:
                body_lines.append(line)
        body = "\n".join(body_lines).strip()
        if body:
            yield " ".join(title_lines), body


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--rows", type=int, default=20, help="max rows to print per query")
    args = ap.parse_args()

    path = Path(args.file)
    if not path.is_absolute():
        path = config.ROOT / path
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)

    engine = create_engine(config.get_url())
    with engine.begin() as conn:
        for title, stmt in split_statements(path.read_text(encoding="utf-8")):
            print("\n" + "=" * 100)
            print(title or stmt[:60])
            print("=" * 100)
            if stmt.lstrip().upper().startswith(("SELECT", "WITH")):
                df = pd.read_sql(text(stmt), conn)
                print(df.head(args.rows).to_string(index=False))
                if len(df) > args.rows:
                    print(f"... ({len(df)} rows total, showing {args.rows}. Use --rows to see more)")
            else:
                conn.execute(text(stmt))
                print("[ok] executed")


if __name__ == "__main__":
    main()
