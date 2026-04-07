import sqlite3
import hashlib
import os
import shutil
from datetime import datetime



BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "worldscope_v3.db")

# ─── Connection & Utilities ───────────────────────────────────────────────────

def get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_password(password: str) -> str:
    # Fixed salt is acceptable for an A-level NEA project.
    # Production systems would store a unique random salt per user.
    salt = "wjec2026"
    return hashlib.sha256((salt + password).encode()).hexdigest()

# ─── Activity Logging (DB-backed) ─────────────────────────────────────────────

def log_activity(username: str, action: str) -> None:
    """
    Writes a timestamped log entry to the activity_logs table.
    Replaces the old flat-file approach so entries can be queried,
    filtered, and sorted from the admin UI.
    """
    conn = get_connection()
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO activity_logs (timestamp, username, action) VALUES (?,?,?)",
            (timestamp, username, action)
        )
        conn.commit()
    except Exception as e:
        print(f"log_activity error: {e}")
    finally:
        conn.close()

def get_recent_logs(limit: int = 5) -> list:
    """Returns the last `limit` log entries as formatted strings (oldest first)."""
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT timestamp, username, action FROM activity_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = cur.fetchall()
        return [f"[{r[0]}] USER: {r[1]} | ACTION: {r[2]}\n" for r in reversed(rows)]
    except Exception:
        return ["No activity recorded yet.\n"]
    finally:
        conn.close()

def get_logs_filtered(keyword: str = "", username_filter: str = "All",
                      limit: int = 500) -> list:
    """
    Returns raw log rows for the admin Activity Logs view.
    Returns [(id, timestamp, username, action), ...]
    """
    conn = get_connection()
    cur  = conn.cursor()
    try:
        wildcard = f"%{keyword}%"
        cur.execute("""
            SELECT id, timestamp, username, action
            FROM activity_logs
            WHERE (action LIKE ? OR username LIKE ?)
            AND   (username = ? OR ? = 'All')
            ORDER BY id DESC LIMIT ?
        """, (wildcard, wildcard, username_filter, username_filter, limit))
        return cur.fetchall()
    except Exception as e:
        print(f"get_logs_filtered error: {e}")
        return []
    finally:
        conn.close()

def get_all_log_usernames() -> list:
    """Returns a sorted list of every username that appears in the logs."""
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT DISTINCT username FROM activity_logs ORDER BY username")
        return [r[0] for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        conn.close()

# ─── Schema Setup ─────────────────────────────────────────────────────────────

def setup_database() -> None:
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT    UNIQUE NOT NULL,
            password        TEXT    NOT NULL,
            role            TEXT    NOT NULL CHECK(role IN ('admin','analyst','viewer')),
            first_name      TEXT,
            last_name       TEXT,
            last_login_date TEXT,
            last_login_time TEXT
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_types (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT    UNIQUE NOT NULL
        )""")

        # UNIQUE constraint on name prevents silent duplicate events on new DBs.
        # Existing DBs are also protected by the application-layer check in
        # event_name_exists(), which runs before every insert and update.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            type_id     INTEGER NOT NULL,
            start_date  TEXT    NOT NULL,
            end_date    TEXT,
            is_ongoing  INTEGER NOT NULL DEFAULT 0,
            impact      TEXT,
            description TEXT,
            source      TEXT,
            FOREIGN KEY (type_id) REFERENCES event_types(id)
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_actors (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            country  TEXT    NOT NULL,
            UNIQUE(event_id, country),
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS deleted_events (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id        INTEGER,
            event_name      TEXT,
            country         TEXT,
            event_type      TEXT,
            start_date      TEXT,
            end_date        TEXT,
            is_ongoing      INTEGER,
            impact_level    TEXT,
            actor_countries TEXT,
            deleted_by      TEXT,
            deleted_at      TEXT
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS event_locations (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            country  TEXT    NOT NULL,
            UNIQUE(event_id, country),
            FOREIGN KEY (event_id) REFERENCES events(id) ON DELETE CASCADE
        )""")

        # DB-backed activity log — replaces the old flat text file.
        cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_logs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            username  TEXT NOT NULL,
            action    TEXT NOT NULL
        )""")

        # Migration guards for older databases
        for migration in [
            "ALTER TABLE deleted_events ADD COLUMN actor_countries TEXT",
        ]:
            try:
                cur.execute(migration)
            except sqlite3.OperationalError:
                pass  # Column already exists — safe to ignore

        # If the database pre-dates the 3NF refactor, events.country may still exist.
        # SQLite cannot DROP columns directly (pre-3.35), so we use the rename-recreate
        # pattern to strip it out transparently on first run after the upgrade.
        cur.execute("PRAGMA table_info(events)")
        event_cols = [r[1] for r in cur.fetchall()]
        if "country" in event_cols:
            cur.executescript("""
                ALTER TABLE events RENAME TO events_old;

                CREATE TABLE events (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    name        TEXT    NOT NULL UNIQUE,
                    type_id     INTEGER NOT NULL,
                    start_date  TEXT    NOT NULL,
                    end_date    TEXT,
                    is_ongoing  INTEGER NOT NULL DEFAULT 0,
                    impact      TEXT,
                    description TEXT,
                    source      TEXT,
                    FOREIGN KEY (type_id) REFERENCES event_types(id)
                );

                INSERT INTO events (id, name, type_id, start_date, end_date,
                                    is_ongoing, impact, description, source)
                SELECT id, name, type_id, start_date, end_date,
                       is_ongoing, impact, description, source
                FROM events_old;

                DROP TABLE events_old;
            """)

        for t in ["Election", "Protest", "Summit", "Conflict", "Sanctions", "Other"]:
            cur.execute("INSERT OR IGNORE INTO event_types (type_name) VALUES (?)", (t,))

        conn.commit()
        _migrate_old_log_file(conn)
        populate_sample_data()

    except Exception as e:
        print(f"Database setup error: {e}")
        conn.rollback()
    finally:
        conn.close()


def _migrate_old_log_file(conn) -> None:
    """
    One-time import of legacy activity_log.txt entries into activity_logs table.
    Renames the file afterwards so it is never re-imported.
    """
    old_path = os.path.join(BASE_DIR, "activity_log.txt")
    if not os.path.exists(old_path):
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM activity_logs")
        if cur.fetchone()[0] > 0:
            return  # Already have DB logs — skip
        with open(old_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ts_end    = line.index("]")
                    timestamp = line[1:ts_end]
                    rest      = line[ts_end + 2:]
                    user_part, action_part = rest.split(" | ACTION: ", 1)
                    username = user_part.replace("USER: ", "").strip()
                    cur.execute(
                        "INSERT INTO activity_logs (timestamp, username, action) VALUES (?,?,?)",
                        (timestamp, username, action_part.strip())
                    )
                except Exception:
                    continue
        conn.commit()
        os.rename(old_path, old_path + ".migrated")
    except Exception as e:
        print(f"Log migration error: {e}")


def populate_sample_data() -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        users = [
            ("admin",    "SystemAdmin@2025", "admin",   "System", "Admin",  None, None),
            ("admin1",   "Admin1@2025",      "admin",   "Syd",    "Banks",  None, None),
            ("analyst1", "Analyst1@2025",    "analyst", "Ned",    "Miller", None, None),
            ("analyst2", "Analyst2@2025",    "analyst", "Marcus",  "Jones", None, None),
            ("viewer1",  "Viewer1@2025",     "viewer",  "James",  "Bass",   None, None),
            ("viewer2",  "Viewer2@2025",     "viewer",  "Lara",   "Croft",  None, None),
            
            
        ]
        for u, p, r, f, l, log_date, log_time in users:
            cur.execute("SELECT id FROM users WHERE username=?", (u,))
            if not cur.fetchone():
                cur.execute("INSERT INTO users VALUES (NULL,?,?,?,?,?,?,?)",
                            (u, hash_password(p), r, f, l, log_date, log_time))

        cur.execute("SELECT id FROM event_types")
        type_rows = cur.fetchall()
        if not type_rows:
            return
        type_ids = [r[0] for r in type_rows]

        cur.execute("SELECT COUNT(*) FROM events")
        if cur.fetchone()[0] == 0:
            events = [
                ("US Election",   type_ids[0],
                 "05/11/2024", "05/11/2024", 0, "High",   "Presidential election", "https://example.com"),
                ("Paris Protest", type_ids[1],
                 "14/07/2023", "Ongoing",    1, "Medium", "Mass demonstrations",   ""),
            ]
            cur.executemany("INSERT INTO events VALUES (NULL,?,?,?,?,?,?,?,?)", events)
            conn.commit()

            cur.execute("SELECT id FROM events WHERE name='US Election'")
            row = cur.fetchone()
            if row:
                eid = row[0]
                # Location: physically takes place in the United States
                cur.execute("INSERT INTO event_locations (event_id, country) VALUES (?,?)",
                            (eid, "United States of America"))
                # Actors: countries involved/participating
                for actor in ["United States of America", "Russia", "China"]:
                    cur.execute("INSERT INTO event_actors (event_id, country) VALUES (?,?)",
                                (eid, actor))

            cur.execute("SELECT id FROM events WHERE name='Paris Protest'")
            row = cur.fetchone()
            if row:
                eid = row[0]
                cur.execute("INSERT INTO event_locations (event_id, country) VALUES (?,?)",
                            (eid, "France"))
                cur.execute("INSERT INTO event_actors (event_id, country) VALUES (?,?)",
                            (eid, "France"))

        conn.commit()
    except Exception as e:
        print(f"Sample data error: {e}")
        conn.rollback()
    finally:
        conn.close()

# ─── Authentication ───────────────────────────────────────────────────────────

def user_exists(username: str) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (username,))
    result = cur.fetchone()
    conn.close()
    return result is not None

def validate_login(username: str, password: str):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username=? AND password=?",
                (username, hash_password(password)))
    result = cur.fetchone()
    conn.close()
    return result

def update_last_login(username: str) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    now  = datetime.now()
    cur.execute("UPDATE users SET last_login_date=?, last_login_time=? WHERE username=?",
                (now.strftime("%d/%m/%Y"), now.strftime("%H:%M:%S"), username))
    conn.commit()
    conn.close()

def verify_user_password(username: str, plain_password: str) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=? AND password=?",
                (username, hash_password(plain_password)))
    result = cur.fetchone()
    conn.close()
    return result is not None

def update_own_password(username: str, new_password: str) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("UPDATE users SET password=? WHERE username=?",
                (hash_password(new_password), username))
    conn.commit()
    conn.close()
    return True

# ─── Event Types ──────────────────────────────────────────────────────────────

def fetch_event_types():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, type_name FROM event_types ORDER BY type_name")
    rows = cur.fetchall()
    conn.close()
    return rows

# ─── Duplicate Name Check ─────────────────────────────────────────────────────

def event_name_exists(name: str, exclude_id=None) -> bool:
    """
    Returns True if an event with this name already exists (case-insensitive).
    Pass exclude_id when editing so the event doesn't clash with itself.
    """
    conn = get_connection()
    cur  = conn.cursor()
    if exclude_id is not None:
        cur.execute("SELECT id FROM events WHERE LOWER(name)=LOWER(?) AND id!=?",
                    (name, exclude_id))
    else:
        cur.execute("SELECT id FROM events WHERE LOWER(name)=LOWER(?)", (name,))
    result = cur.fetchone()
    conn.close()
    return result is not None

# ─── Dashboard Statistics ─────────────────────────────────────────────────────

def get_dashboard_stats() -> dict:
    """Returns headline counts for the summary bar on the dashboard."""
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM events")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM events WHERE impact='High'")
        high_impact = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM events WHERE is_ongoing=1")
        ongoing = cur.fetchone()[0]
        cur.execute("SELECT COUNT(DISTINCT country) FROM event_locations")
        countries = cur.fetchone()[0]
        return {"total": total, "high_impact": high_impact,
                "ongoing": ongoing, "countries": countries}
    except Exception:
        return {"total": 0, "high_impact": 0, "ongoing": 0, "countries": 0}
    finally:
        conn.close()

# ─── Event CRUD ───────────────────────────────────────────────────────────────

def fetch_events():
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT e.id,
               e.name,

               -- MULTI-LOCATION SUPPORT
               (SELECT GROUP_CONCAT(el.country, ', ')
                FROM event_locations el
                WHERE el.event_id = e.id) AS locations,

               t.type_name,
               e.start_date,
               e.end_date,
               e.impact,

               (SELECT GROUP_CONCAT(ea.country, ', ')
                FROM event_actors ea
                WHERE ea.event_id = e.id) AS actors

        FROM events e
        JOIN event_types t ON e.type_id = t.id
        ORDER BY e.id ASC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_event_by_id(event_id: int):
    """
    Returns (name, type_id, start_date, end_date, is_ongoing, impact, description, source).
    Location countries are fetched separately via fetch_event_locations().
    """
    conn = get_connection()
    cur  = conn.cursor()

    cur.execute("""
        SELECT name, type_id, start_date, end_date,
               is_ongoing, impact, description, source
        FROM events WHERE id=?
    """, (event_id,))

    row = cur.fetchone()
    conn.close()
    return row

def insert_event(payload):
    """
    Inserts a new event row.  payload must be an 8-tuple:
    (name, type_id, start_date, end_date, is_ongoing, impact, description, source)
    Location countries are stored separately via set_event_locations().
    """
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO events (
                name, type_id, start_date, end_date,
                is_ongoing, impact, description, source
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, payload)

        conn.commit()
        return cur.lastrowid

    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def update_event(event_id: int, payload) -> None:
    """
    Updates an existing event row.  payload must be an 8-tuple:
    (name, type_id, start_date, end_date, is_ongoing, impact, description, source)
    Location countries are updated separately via set_event_locations().
    """
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            UPDATE events
            SET name=?, type_id=?, start_date=?, end_date=?,
                is_ongoing=?, impact=?, description=?, source=?
            WHERE id=?
        """, (*payload, event_id))
        conn.commit()
    except sqlite3.Error as e:
        print(f"update_event error: {e}")
        conn.rollback()
    finally:
        conn.close()

def delete_event_from_db(event_id: int, event_name: str, deleted_by: str) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "SELECT start_date, end_date, is_ongoing, impact, type_id FROM events WHERE id=?",
            (event_id,)
        )
        row = cur.fetchone()
        if not row:
            return False

        cur.execute("SELECT type_name FROM event_types WHERE id=?", (row[4],))
        t = cur.fetchone()
        type_name = t[0] if t else "General"

        # Snapshot location countries from event_locations (3NF-correct source)
        cur.execute("SELECT country FROM event_locations WHERE event_id=?", (event_id,))
        location_country = ", ".join(r[0] for r in cur.fetchall())

        cur.execute("SELECT country FROM event_actors WHERE event_id=?", (event_id,))
        actors = ", ".join(r[0] for r in cur.fetchall())

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO deleted_events (
                event_id, event_name, country, event_type,
                start_date, end_date, is_ongoing, impact_level,
                actor_countries, deleted_by, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (event_id, event_name, location_country, type_name,
              row[0], row[1], row[2], row[3], actors, deleted_by, now_str))

        cur.execute("DELETE FROM events WHERE id=?", (event_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"delete_event_from_db error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def fetch_deleted_events():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, event_id, event_name, start_date, end_date,
               is_ongoing, deleted_at, deleted_by, actor_countries
        FROM deleted_events ORDER BY deleted_at DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def fetch_deleted_events_filtered(keyword: str = "", deleted_by: str = "All") -> list:
    """Filters the deleted events archive by event name and/or who deleted it."""
    conn = get_connection()
    cur  = conn.cursor()
    wildcard = f"%{keyword}%"
    cur.execute("""
        SELECT id, event_id, event_name, start_date, end_date,
               is_ongoing, deleted_at, deleted_by, actor_countries
        FROM deleted_events
        WHERE event_name LIKE ?
        AND  (deleted_by = ? OR ? = 'All')
        ORDER BY deleted_at DESC
    """, (wildcard, deleted_by, deleted_by))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_deleted_by_options() -> list:
    """Returns all unique 'deleted_by' values for the archive filter dropdown."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT deleted_by FROM deleted_events ORDER BY deleted_by")
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def restore_event_from_db(log_id: int, original_id: int) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            SELECT event_name, country, event_type, start_date, end_date,
                   is_ongoing, impact_level, actor_countries
            FROM deleted_events WHERE id=?
        """, (log_id,))
        row = cur.fetchone()
        if not row:
            return False

        cur.execute("SELECT id FROM event_types WHERE type_name=?", (row[2],))
        t = cur.fetchone()
        if not t:
            return False
        type_id = t[0]

        # Restore the core event row — no country column on events table
        cur.execute("""
            INSERT INTO events (id, name, type_id, start_date, end_date,
                                is_ongoing, impact)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (original_id, row[0], type_id, row[3], row[4], row[5], row[6]))

        # Restore location countries from the snapshotted comma-separated string
        location_str = row[1]
        if location_str:
            for loc in [c.strip() for c in location_str.split(",") if c.strip()]:
                cur.execute("INSERT INTO event_locations (event_id, country) VALUES (?,?)",
                            (original_id, loc))

        # Restore actor countries
        actors_str = row[7]
        if actors_str:
            for actor in [a.strip() for a in actors_str.split(",") if a.strip()]:
                cur.execute("INSERT INTO event_actors (event_id, country) VALUES (?,?)",
                            (original_id, actor))

        cur.execute("DELETE FROM deleted_events WHERE id=?", (log_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"restore_event_from_db error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# ─── Actor Countries ──────────────────────────────────────────────────────────

def fetch_event_actors(event_id: int) -> list:
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT country FROM event_actors WHERE event_id=? ORDER BY country",
                (event_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def set_event_actors(event_id: int, countries: list) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM event_actors WHERE event_id=?", (event_id,))
        for country in countries:
            if country:
                cur.execute("INSERT INTO event_actors (event_id, country) VALUES (?,?)",
                            (event_id, country))
        conn.commit()
    except sqlite3.Error as e:
        print(f"set_event_actors error: {e}")
        conn.rollback()
    finally:
        conn.close()

# ─── Location Countries ───────────────────────────────────────────────────────

def fetch_event_locations(event_id: int) -> list:
    """Returns the list of location countries for an event (from event_locations)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT country FROM event_locations WHERE event_id=? ORDER BY country",
                (event_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]

def set_event_locations(event_id: int, countries: list) -> None:
    """Replaces all location rows for an event with the supplied list."""
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM event_locations WHERE event_id=?", (event_id,))
        for country in countries:
            if country:
                cur.execute("INSERT INTO event_locations (event_id, country) VALUES (?,?)",
                            (event_id, country))
        conn.commit()
    except sqlite3.Error as e:
        print(f"set_event_locations error: {e}")
        conn.rollback()
    finally:
        conn.close()

# ─── Search & Filter ──────────────────────────────────────────────────────────

def fetch_events_filtered(keyword: str, country: str, event_type: str):
    conn = get_connection()
    cur  = conn.cursor()
    wildcard = f"%{keyword}%"
    cur.execute("""
        SELECT e.id,
               e.name,
               (SELECT GROUP_CONCAT(el.country, ', ')
                FROM event_locations el WHERE el.event_id = e.id) AS locations,
               t.type_name,
               e.start_date,
               e.end_date,
               e.impact,
               (SELECT GROUP_CONCAT(ea.country, ', ')
                FROM event_actors ea WHERE ea.event_id = e.id
                ORDER BY ea.country) AS actors
        FROM events e
        JOIN event_types t ON e.type_id = t.id
        WHERE (e.name LIKE ? OR e.description LIKE ?
               OR EXISTS (SELECT 1 FROM event_locations el2
                          WHERE el2.event_id = e.id AND el2.country LIKE ?)
               OR EXISTS (SELECT 1 FROM event_actors ea2
                          WHERE ea2.event_id = e.id AND ea2.country LIKE ?))
        AND (? = 'All' OR EXISTS (SELECT 1 FROM event_locations el3
                                  WHERE el3.event_id = e.id AND el3.country = ?))
        AND (t.type_name = ? OR ? = 'All')
        ORDER BY substr(e.start_date,7,4) DESC,
                 substr(e.start_date,4,2) DESC,
                 substr(e.start_date,1,2) DESC
    """, (wildcard, wildcard, wildcard, wildcard,
          country, country, event_type, event_type))
    rows = cur.fetchall()
    conn.close()
    return rows

# ─── Dashboard Aggregates ─────────────────────────────────────────────────────

def get_events_by_country():
    """Returns (country, count) aggregated from event_locations (the 3NF-correct source)."""
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT country, COUNT(*) FROM event_locations GROUP BY country ORDER BY COUNT(*) DESC")
    data = cur.fetchall()
    conn.close()
    return data

def get_events_by_actor_country():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        "SELECT country, COUNT(*) FROM event_actors GROUP BY country ORDER BY COUNT(*) DESC"
    )
    data = cur.fetchall()
    conn.close()
    return data

def get_events_by_type():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT t.type_name, COUNT(e.id)
        FROM event_types t LEFT JOIN events e ON t.id = e.type_id
        GROUP BY t.type_name ORDER BY COUNT(e.id) DESC
    """)
    data = cur.fetchall()
    conn.close()
    return data

def get_events_by_impact():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT impact, COUNT(*) FROM events
        GROUP BY impact
        ORDER BY CASE impact WHEN 'High' THEN 1 WHEN 'Medium' THEN 2
                             WHEN 'Low'  THEN 3 ELSE 4 END
    """)
    data = cur.fetchall()
    conn.close()
    return data

# ─── User Management ──────────────────────────────────────────────────────────

def fetch_users():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("""
        SELECT id, username, role, first_name, last_name, last_login_date, last_login_time
        FROM users ORDER BY id
    """)
    data = cur.fetchall()
    conn.close()
    return data

def create_user(username: str, password: str, role: str,
                first_name: str, last_name: str) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (username, password, role, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, (username, hash_password(password), role, first_name, last_name))
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"create_user error: {e}")
    finally:
        conn.close()

def update_user(user_id: int, username: str, role: str,
                first_name: str, last_name: str) -> bool:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("""
            UPDATE users SET username=?, role=?, first_name=?, last_name=?
            WHERE id=?
        """, (username, role, first_name, last_name, user_id))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def delete_user(user_id: int) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    finally:
        conn.close()

def admin_reset_password(user_id: int, new_password: str) -> None:
    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute("UPDATE users SET password=? WHERE id=?",
                    (hash_password(new_password), user_id))
        conn.commit()
    finally:
        conn.close()


def backup_database(backup_folder="backups"):
    """
    Creates a timestamped backup copy of the database file.
    Returns (success: bool, message: str)
    """
    try:
        if not os.path.exists(backup_folder):
            os.makedirs(backup_folder)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"worldscope_backup_{timestamp}.db"
        backup_path = os.path.join(backup_folder, backup_filename)

        shutil.copy2(DB_PATH, backup_path)

        return True, backup_path  

    except Exception as e:
        return False, str(e)