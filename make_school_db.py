import sqlite3
from pathlib import Path

path = Path(__file__).parent / "school.db"
if path.exists():
    path.unlink()

conn = sqlite3.connect(path)
conn.execute('CREATE TABLE "Student Records" ("Student ID" INTEGER, "Full Name" TEXT, "Course" TEXT, "Marks" INTEGER)')
conn.executemany('INSERT INTO "Student Records" VALUES (?,?,?,?)', [
    (1, "Anita Rao", "Computer Science", 88),
    (2, "Bilal Khan", "Computer Science", 72),
    (3, "Charu Nair", "Mathematics", 91),
    (4, "Deepak Verma", "Mathematics", 65),
    (5, "Esha Gupta", "Physics", 79),
    (6, "Farhan Ali", "Physics", 84),
    (7, "Gita Menon", "Computer Science", 95),
    (8, "Harsh Patel", "Statistics", 58),
])
conn.commit()
conn.close()
print("Created school.db")