import sqlite3
from pathlib import Path

path = Path(__file__).parent / "shop.db"
if path.exists():
    path.unlink()  # start fresh if you run this twice

conn = sqlite3.connect(path)
conn.executescript("""
CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT, signup_date TEXT);
CREATE TABLE products (product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL);
CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer_id INTEGER, order_date TEXT, status TEXT);
CREATE TABLE order_items (order_id INTEGER, product_id INTEGER, quantity INTEGER);
""")

conn.executemany("INSERT INTO customers VALUES (?,?,?,?)", [
    (1, "Asha", "Hyderabad", "2025-01-10"),
    (2, "Ravi", "Mumbai", "2025-02-14"),
    (3, "Meera", "Hyderabad", "2025-03-05"),
    (4, "John", "Delhi", "2025-03-20"),
    (5, "Priya", "Mumbai", "2025-04-11"),
    (6, "Karan", "Chennai", "2025-05-02"),
])
conn.executemany("INSERT INTO products VALUES (?,?,?,?)", [
    (1, "Laptop", "Electronics", 55000),
    (2, "Headphones", "Electronics", 2500),
    (3, "Notebook", "Stationery", 120),
    (4, "Pen Pack", "Stationery", 80),
    (5, "Backpack", "Accessories", 1800),
    (6, "Desk Lamp", "Home", 950),
])
conn.executemany("INSERT INTO orders VALUES (?,?,?,?)", [
    (1, 1, "2025-06-01", "delivered"),
    (2, 1, "2025-06-15", "delivered"),
    (3, 2, "2025-06-20", "cancelled"),
    (4, 3, "2025-07-02", "delivered"),
    (5, 4, "2025-07-10", "pending"),
    (6, 5, "2025-07-18", "delivered"),
    (7, 2, "2025-08-01", "delivered"),
    (8, 3, "2025-08-09", "delivered"),
])
conn.executemany("INSERT INTO order_items VALUES (?,?,?)", [
    (1, 1, 1), (1, 2, 1), (2, 3, 10), (3, 5, 1),
    (4, 2, 2), (4, 4, 5), (5, 6, 1), (6, 3, 5),
    (6, 5, 1), (7, 1, 1), (8, 6, 2), (8, 3, 3),
])
conn.commit()
conn.close()
print("Created shop.db")