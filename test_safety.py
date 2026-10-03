from tools import run_query, connect_readonly

tests = [
    "SELECT COUNT(*) FROM Customer",
    "DELETE FROM Customer",
    "DROP TABLE Customer",
    "SELECT 1; DROP TABLE Customer",
    "UPDATE Customer SET Country = 'X'",
]

print("--- Layer 1: the validator ---")
for sql in tests:
    print(sql, "->", run_query.invoke({"sql": sql}))

print()
print("--- Layer 2: the read-only database ---")
conn = connect_readonly()
try:
    conn.execute("DELETE FROM Customer")
except Exception as e:
    print("The database itself refused:", e)