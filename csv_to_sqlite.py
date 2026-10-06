import sqlite3
import sys
from pathlib import Path

import pandas as pd

if len(sys.argv) < 2:
    raise SystemExit('Usage: python csv_to_sqlite.py "path\\to\\file.csv" [table_name]')

csv_path = Path(sys.argv[1])
table = sys.argv[2] if len(sys.argv) > 2 else csv_path.stem.replace(" ", "_")

try:
    df = pd.read_csv(csv_path)
except UnicodeDecodeError:
    df = pd.read_csv(csv_path, encoding="latin-1")

out = csv_path.with_suffix(".db")
conn = sqlite3.connect(out)
df.to_sql(table, conn, if_exists="replace", index=False)
conn.close()
print(f"Created {out} with table '{table}': {len(df)} rows, {len(df.columns)} columns")