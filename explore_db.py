import sqlite3

conn = sqlite3.connect("chinook.db")
cur = conn.cursor()

# 1. What tables exist?
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", cur.fetchall())

# 2. What columns does the Customer table have?
cur.execute("PRAGMA table_info(Customer)")
for col in cur.fetchall():
    print(col[1], col[2])   # column name, column type

# 3. A real question answered with SQL
cur.execute("SELECT COUNT(*) FROM Customer WHERE Country = 'Canada'")
print("Canadian customers:", cur.fetchone()[0])