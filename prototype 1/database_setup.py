import sqlite3
#connection to database 
conn = sqlite3.connect("test.db")
cursor = conn.cursor()
#error path 
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    type TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    source TEXT,
    impact TEXT
)
""")

conn.commit()
conn.close()
print("Database and table is an success")