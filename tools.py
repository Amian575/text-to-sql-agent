import os
import re
import sqlite3
from pathlib import Path
from langchain_core.tools import tool

DB_FILE = (Path(__file__).parent / os.getenv("DB_FILE", "chinook.db")).resolve()
MAX_ROWS = 20

# Words that should never appear in a read-only analytics query
BLOCKED_WORDS = [
    "insert", "update", "delete", "drop", "alter", "create",
    "replace", "attach", "detach", "pragma", "vacuum", "reindex",
]

# Text inside quotes ("Update Date", 'a;b', `x`, [y]) is a name or a value, not a command
QUOTED_PARTS = re.compile(r'''"[^"]*"|'[^']*'|`[^`]*`|\[[^\]]*\]''')


def connect_readonly():
    """Open the database so that writing is impossible."""
    return sqlite3.connect(f"{DB_FILE.as_uri()}?mode=ro", uri=True)


def quote_ident(name: str) -> str:
    """Wrap a table or column name in double quotes so spaces are safe."""
    return '"' + name.replace('"', '""') + '"'


def needs_quotes(name: str) -> bool:
    return not name.replace("_", "").isalnum()


def check_sql_is_safe(sql: str):
    """Return None if the query is safe, otherwise a message saying why not."""
    cleaned = sql.strip().rstrip(";").strip()
    scan = QUOTED_PARTS.sub('""', cleaned)

    if ";" in scan:
        return "Only one SQL statement is allowed."

    if not re.match(r"^(select|with)\b", scan, re.IGNORECASE):
        return "Only SELECT queries are allowed."

    lowered = scan.lower()
    for word in BLOCKED_WORDS:
        if re.search(rf"\b{word}\b", lowered):
            return f"The keyword '{word}' is not allowed."

    return None


@tool
def list_tables() -> str:
    """List all table names in the database."""
    conn = connect_readonly()
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    conn.close()
    return ", ".join(r[0] for r in rows)


@tool
def get_schema(table_name: str) -> str:
    """Return the column names and types for one table."""
    conn = connect_readonly()
    names = [
        r[0]
        for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    ]
    if table_name not in names:
        conn.close()
        return f"Error: unknown table '{table_name}'. Valid tables: {', '.join(names)}"
    rows = conn.execute(f"PRAGMA table_info({quote_ident(table_name)})").fetchall()
    conn.close()
    return ", ".join(
        f"{quote_ident(r[1]) if needs_quotes(r[1]) else r[1]} {r[2]}" for r in rows
    )


@tool
def run_query(sql: str) -> str:
    """Run a read-only SQL query and return up to 20 rows. If the query is invalid or not allowed, returns an error message."""
    problem = check_sql_is_safe(sql)
    if problem:
        return f"Error: {problem}"

    conn = connect_readonly()
    try:
        rows = conn.execute(sql).fetchall()
        result = str(rows[:MAX_ROWS])
        if len(rows) > MAX_ROWS:
            result += f"\n(Showing {MAX_ROWS} of {len(rows)} rows)"
        return result
    except sqlite3.Error as e:
        return f"Error: {e}"
    finally:
        conn.close()