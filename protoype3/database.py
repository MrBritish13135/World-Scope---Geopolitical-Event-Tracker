import sqlite3
import hashlib
import os
import shutil
from datetime import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "worldscope_v3.db")

def backup_database():
    conn = get_connection()
    conn.close()
    try:
        # Use a consistent folder name
        backup_dir = os.path.join(BASE_DIR, "backups") 
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"worldscope_backup_{timestamp}.db"
        destination = os.path.join(backup_dir, backup_filename)

        shutil.copy2(DB_PATH, destination)
        return True, backup_filename
    except Exception as e:
        return False, str(e)

def log_activity(username, action):
    # Create activity_log.txt if it doesn't exist
    log_path = os.path.join(BASE_DIR, "activity_log.txt")
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"{timestamp} USER: {username} | ACTION: {action}\n")

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str) -> str:
    salt = "wjec2026"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def setup_database():
    try:
        conn = get_connection()
        cur = conn.cursor()
        #cur.execute("DROP TABLE IF EXISTS deleted_events")
        #conn.commit()
        # Create Tables
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            last_login_date TEXT,
            last_login_time TEXT
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT UNIQUE NOT NULL
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            type_id INTEGER NOT NULL,
            start_date TEXT NOT NULL, -- -- e.g., '2024-11-20'
            end_date TEXT,  -- Optional end date for multi-day events
            is_ongoing INTEGER NOT NULL DEFAULT 0, -- 1 for True, 0 for False
            impact TEXT,
            description TEXT,
            source TEXT,
            FOREIGN KEY (type_id) REFERENCES event_types(id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS deleted_events (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             event_id INTEGER,
            event_name TEXT,
            country TEXT,
            event_type TEXT,
           start_date TEXT,
           end_date TEXT,
           is_ongoing INTEGER,
           impact_level TEXT,
           deleted_by TEXT,
           deleted_at TEXT
)
""")
        # Insert default types
        for t in ["Election", "Protest", "Summit", "Conflict", "Sanctions", "Other"]:
            cur.execute("INSERT OR IGNORE INTO event_types (type_name) VALUES (?)", (t,))
        conn.commit()
    finally:
        conn.close()

    # Add Admin and Sample Data
    populate_sample_data()

def populate_sample_data():
    conn = get_connection()
    cur = conn.cursor()

    # Create Sample Users
    users = [
    ("admin",    "SystemAdmin@2025",    "admin",   "System", "Admin", None, None),
    ("viewer1",  "Viewer1@2025",     "viewer",  "James",  "Bass",  None, None),
    ("analyst1", "Analyst1@2025",    "analyst", "Ned",    "Miller",None, None),
    ("admin1",   "Admin1@2025",  "admin",   "Syd",    "Banks", None, None),
]


    for u, p, r, f, l, log_date, log_time in users: 
        cur.execute("SELECT id FROM users WHERE username=?", (u,))
        if not cur.fetchone():
            cur.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?,?,?)",
                        (u, hash_password(p), r, f, l, log_date, log_time))

    # Get Type IDs for the events
    cur.execute("SELECT id FROM event_types")
    type_rows = cur.fetchall()
    if type_rows:
        type_ids = [r[0] for r in type_rows]

        # Insert Sample Events
        cur.execute("SELECT COUNT(*) FROM events")
        if cur.fetchone()[0] == 0:
            #  (Name, Country, TypeID, StartDate, EndDate, IsOngoing, Impact, Desc, URL)
            events = [
                ("US Election", "USA", type_ids[0], "05/11/2024", "05/11/2024", 0, "High", "Presidential election", "https://example.com"),
                ("Paris Protest", "France", type_ids[1], "14/07/2023", "Ongoing", 1, "Medium", "Mass demonstrations", ""),
            ]
            
            # Insert events with 9 placeholders
            cur.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?,?,?,?,?)", events)

    conn.commit()
    conn.close()

# ─── Helper Queries ───

def user_exists(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def validate_login(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username=? AND password=?",
                (username, hash_password(password)))
    result = cur.fetchone()
    conn.close()
    return result # Returns (role,) or None

def fetch_event_types():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, type_name FROM event_types")
    rows = cur.fetchall()
    conn.close()
    return rows

# ─── Event Management ───

def fetch_events():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id, e.name, e.country, t.type_name, e.start_date, e.end_date, e.impact
        FROM events e
        JOIN event_types t ON e.type_id = t.id
        ORDER BY e.id ASC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_event_by_id(event_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT name, country, start_date, impact, description, source, type_id, end_date, is_ongoing
        FROM events 
        WHERE id=?
    """, (event_id,))
    row = cur.fetchone()
    conn.close()
    return row

def insert_event(payload):
    conn = get_connection()
    cur = conn.cursor()
    # Note: Column order must match payload: (name, country, type_id, start, end, ongoing, impact, desc, source)
    query = """INSERT INTO events 
               (name, country, type_id, start_date, end_date, is_ongoing, impact, description, source) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"""
    try:
        cur.execute(query, payload)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        conn.close()
    
def update_event(event_id, payload):
    conn = get_connection()
    cur = conn.cursor()
    # Corrected column mapping
    cur.execute("""
        UPDATE events 
        SET name=?, country=?, type_id=?, start_date=?, end_date=?, is_ongoing=?, impact=?, description=?, source=?
        WHERE id=?
    """, (*payload, event_id))
    conn.commit()
    conn.close()

def delete_event_from_db(event_id, event_name, current_admin):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        cur.execute("SELECT country, start_date, end_date, is_ongoing, impact, type_id FROM events WHERE id=?", (event_id,))
        row = cur.fetchone()
        
        if row:
            cur.execute("SELECT type_name FROM event_types WHERE id=?", (row[5],))
            type_res = cur.fetchone()
            type_name = type_res[0] if type_res else "General"

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cur.execute("""
                INSERT INTO deleted_events (
                    event_id, event_name, country, event_type, 
                    start_date, end_date, is_ongoing, impact_level, 
                    deleted_by, deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (event_id, event_name, row[0], type_name, row[1], row[2], row[3], row[4], current_admin, now_str))
            
            cur.execute("DELETE FROM events WHERE id=?", (event_id,))
            conn.commit()
            return True
        return False
    except Exception as e:
        print(f"Archival Error: {e}")
        return False
    finally:
        conn.close()
def fetch_deleted_events():
    """Fetches all archived events for the admin view."""
    conn = sqlite3.connect(DB_PATH) # Use your existing DB_PATH
    cur = conn.cursor()
    # The order here must match the indices used in dashboard.py:
    # 0:id, 1:event_id, 2:event_name, 3:start_date, 4:end_date, 5:is_ongoing, 6:deleted_at, 7:deleted_by
    cur.execute("""
        SELECT id, event_id, event_name, start_date, end_date, is_ongoing, deleted_at, deleted_by 
        FROM deleted_events 
        ORDER BY deleted_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def restore_event_from_db(log_id, original_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT event_name, country, event_type, start_date, end_date, is_ongoing, impact_level 
            FROM deleted_events WHERE id = ?
        """, (log_id,))
        row = cur.fetchone()
        
        if row:
            cur.execute("SELECT id FROM event_types WHERE type_name = ?", (row[2],))
            t_id = cur.fetchone()[0]

            # Re-insert with original dates and status
            cur.execute("""
                INSERT INTO events (id, name, country, type_id, start_date, end_date, is_ongoing, impact)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (original_id, row[0], row[1], t_id, row[3], row[4], row[5], row[6]))
            
            cur.execute("DELETE FROM deleted_events WHERE id = ?", (log_id,))
            conn.commit()
            return True
    finally:
        conn.close()

# ─── User Management ───

def create_user(username, password, role, first_name, last_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (username, password, role, first_name, last_name) 
        VALUES (?, ?, ?, ?, ?)
    """, (username, hash_password(password), role, first_name, last_name))
    conn.commit()
    conn.close()

def update_last_login(username):
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now()
    current_date = now.strftime("%d/%m/%Y")
    current_time = now.strftime("%H:%M:%S")

    query = "UPDATE users SET last_login_date=?, last_login_time=? WHERE username=?"
    cur.execute(query, (current_date, current_time, username))

    conn.commit()
    conn.close()

def fetch_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, role, first_name, last_name, last_login_date, last_login_time FROM users")
    data = cur.fetchall()
    conn.close()
    return data

def delete_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

def admin_reset_password(user_id, new_password):
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(new_password)
    cur.execute("UPDATE users SET password=? WHERE id=?", (hashed, user_id))
    conn.commit()
    conn.close()

def update_user(user_id, username, role, first_name, last_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE users 
            SET username=?, role=?, first_name=?, last_name=?
            WHERE id=?
        """, (username, role, first_name, last_name, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

# ─── Data for Dashboard ───
def get_events_by_country():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT country, COUNT(*) FROM events GROUP BY country")
    data = cur.fetchall()
    conn.close()
    return data
def get_events_by_type():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.type_name, COUNT(e.id) 
        FROM event_types t
        LEFT JOIN events e ON t.id = e.type_id
        GROUP BY t.type_name
    """)
    data = cur.fetchall()
    conn.close()
    return data

def get_events_by_impact():
    conn = get_connection()
    cur = conn.cursor()
    # This ensures the chart legend and slices always follow Highmedium-low order, even if some categories have zero events
    cur.execute("""
        SELECT impact, COUNT(*) 
        FROM events 
        GROUP BY impact 
        ORDER BY 
            CASE impact 
                WHEN 'High' THEN 1 
                WHEN 'Medium' THEN 2 
                WHEN 'Low' THEN 3 
                ELSE 4 
            END
    """)
    data = cur.fetchall()
    conn.close()
    return data

def fetch_events_filtered(keyword, country, event_type):
    conn = get_connection()
    cur = conn.cursor()
    wildcard = f"%{keyword}%"
    
    # Apply filters
    query = """
        SELECT e.id, e.name, e.country, t.type_name, e.start_date, e.end_date, e.impact 
        FROM events e
        JOIN event_types t ON e.type_id = t.id
        WHERE (e.name LIKE ? OR e.country LIKE ? OR e.description LIKE ?)
          AND (e.country = ? OR ? = 'All')
          AND (t.type_name = ? OR ? = 'All')
        ORDER BY 
            substr(e.start_date, 7, 4) DESC, 
            substr(e.start_date, 4, 2) DESC, 
            substr(e.start_date, 1, 2) DESC
    """
    params = (wildcard, wildcard, wildcard, country, country, event_type, event_type)
    
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

def verify_user_password(username, plain_password):
    """Checks if the provided password matches the one in the DB."""
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(plain_password)
    cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, hashed))
    result = cur.fetchone()
    conn.close()
    return result is not None

def update_own_password(username, new_password):
    """Updates the password for the specific user."""
    conn = get_connection()
    cur = conn.cursor()
    hashed = hash_password(new_password)
    cur.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
    conn.commit()
    conn.close()
    return True
