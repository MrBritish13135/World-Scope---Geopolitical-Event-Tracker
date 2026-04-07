import sqlite3
import hashlib

DB_NAME = "worldscope_p2.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def hash_password(password):
    # Fixed salt for NEA project consistency
    salt = "wjec2026"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Create Events Table (Updated with separate dates)
    cursor.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, 
        country TEXT, 
        type TEXT, 
        start_date TEXT, 
        end_date TEXT, 
        impact TEXT
    )""")
    
    # 2. Create Users Table
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE, 
        password TEXT
    )""")
    
    # 3. SEED DATA: Automatic Sample Users
    # We check if admin exists; if not, we create sample accounts
    cursor.execute("SELECT * FROM users WHERE username='admin'")
    if not cursor.fetchone():
        sample_users = [
            ('admin', hash_password('admin123')),
            ('test_user', hash_password('password123'))
        ]
        cursor.executemany("INSERT INTO users (username, password) VALUES (?, ?)", sample_users)
        print("Prototype 2: Sample users initialized.")

    conn.commit()
    conn.close()

def create_user(username, password):
    """Used by the Sign-Up tab in auth_p2.py"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", 
                       (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username taken
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?", 
                   (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    return user

def add_event(name, country, etype, s_date, e_date, impact):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""INSERT INTO events (name, country, type, start_date, end_date, impact) 
                   VALUES (?,?,?,?,?,?)""", (name, country, etype, s_date, e_date, impact))
    conn.commit()
    conn.close()

def get_events():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events")
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_event(event_id):
    """The missing delete function for Prototype 2 CRUD"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE id=?", (event_id,))
    conn.commit()
    conn.close()