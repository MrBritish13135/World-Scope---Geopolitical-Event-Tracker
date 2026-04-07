import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

# 1. DATABASE SETUP
conn = sqlite3.connect("events_p1.db")
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    type TEXT NOT NULL,
    date TEXT NOT NULL,
    impact TEXT
)
""")
# Create users table for authentication
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
""")
conn.commit()

# Insert default admin user if not exists
cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin123')")
    conn.commit()


# 2. GLOBALS & VALIDATION
TYPE_OPTIONS = ["Election", "Protest", "Summit", "Conflict", "Other"]
IMPACT_OPTIONS = ["Low", "Medium", "High", "Severe"]

# Simple date validation (DD/MM/YYYY)
def validate_date(datestr):
    try:
        datetime.strptime(datestr, "%d/%m/%Y")
        return True
    except ValueError:
        return False
# 3. FUNCTIONS
def add_event():
    name = entry_name.get().strip()
    country = entry_country.get().strip()
    event_type = combobox_type.get().strip()
    date = entry_date.get().strip()
    impact = combobox_impact.get().strip()
# Basic validation
    if not name or not country or not date:
        messagebox.showerror("Error", "Please fill in required fields.")
        return
# Validate date format
    if not validate_date(date):
        messagebox.showerror("Error", "Date must be DD/MM/YYYY")
        return
# Insert into database
    try:
        cursor.execute("""
            INSERT INTO events (name, country, type, date, impact)
            VALUES (?, ?, ?, ?, ?)
        """, (name, country, event_type, date, impact))
        conn.commit()
        messagebox.showinfo("Success", "Event added!")
# Clear inputs
        entry_name.delete(0, tk.END)
        entry_country.delete(0, tk.END)
        entry_date.delete(0, tk.END)
# Refresh event list
        load_events()
# Handle database errors
    except Exception as e:
        messagebox.showerror("Database error", str(e))

# Load events from database into Treeview
def load_events():
    for row in tree.get_children():
        tree.delete(row)
# Fetch and display events
    cursor.execute("SELECT * FROM events ORDER BY date")
    for event in cursor.fetchall():
        tree.insert("", tk.END, values=event)

# Logout function
def logout():
    root.withdraw()
    show_login()



# 4. LOGIN WINDOW
def show_login():
    login_win = tk.Toplevel()
    login_win.title("Login")
    login_win.geometry("260x160")
    login_win.resizable(False, False)
# Input fields
    tk.Label(login_win, text="Username:").pack(pady=5)
    user_entry = tk.Entry(login_win)
    user_entry.pack()
# Password field
    tk.Label(login_win, text="Password:").pack(pady=5)
    pass_entry = tk.Entry(login_win, show="*")
    pass_entry.pack()
# Login button
    def check_login():
        u = user_entry.get()
        p = pass_entry.get()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        if cursor.fetchone():
            login_win.destroy()
            root.deiconify()
            load_events()
        else:
            messagebox.showerror("Login", "Invalid credentials")

    tk.Button(login_win, text="Login", command=check_login).pack(pady=10)



# 5. MAIN GUI
# Main window
root = tk.Tk()
root.title("WorldScope - Prototype 1")
root.geometry("500x600")
root.withdraw()

# Input fields
tk.Label(root, text="Event Name:").pack(pady=2)
entry_name = tk.Entry(root, width=40)
entry_name.pack(pady=2)
# Country
tk.Label(root, text="Country:").pack(pady=2)
entry_country = tk.Entry(root, width=40)
entry_country.pack(pady=2)
# Type
tk.Label(root, text="Type:").pack(pady=2)
combobox_type = ttk.Combobox(root, values=TYPE_OPTIONS, width=37)
combobox_type.pack(pady=2)
# Date
tk.Label(root, text="Date (DD/MM/YYYY):").pack(pady=2)
entry_date = tk.Entry(root, width=40)
entry_date.pack(pady=2)
# Impact
tk.Label(root, text="Impact:").pack(pady=2)
combobox_impact = ttk.Combobox(root, values=IMPACT_OPTIONS, width=37)
combobox_impact.pack(pady=2)
# Add Event button
tk.Button(root, text="Save Event", command=add_event).pack(pady=10)
# Treeview
columns = ("ID", "Name", "Country", "Type", "Date", "Impact")
tree = ttk.Treeview(root, columns=columns, show="headings", height=10)
# Set column headings and widths
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=80)
# Display events
tree.pack(pady=10)

# Buttons
tk.Button(root, text="Refresh Events", command=load_events).pack(pady=5)
tk.Button(root, text="Logout", command=logout).pack(pady=5)

# Start with login
if __name__ == "__main__":
    show_login()
    root.mainloop()