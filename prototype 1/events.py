import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime
import csv

# Main window setup
root = tk.Tk()
root.title("Worldscope")
root.geometry("400x600")
root.withdraw()

# Database setup
conn = sqlite3.connect("events.db")
cursor = conn.cursor()
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
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL
)
""")
conn.commit()

cursor.execute("SELECT * FROM users WHERE username='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("admin", "admin123", "admin"))
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                   ("user", "1234", "user"))
    conn.commit()


# Options for dropdown menus
TYPE_OPTIONS = ["Election", "Protest", "Summit", "Conflict", "Sanctions", "Other"]
IMPACT_OPTIONS = ["Low", "Medium", "High", "Severe"]

# Function to validate date format (DD/MM/YYYY)
def validate_date(datestr):
    try:
        datetime.strptime(datestr, "%d/%m/%Y")
        return True
    except ValueError:
        return False

# Function to clear form fields
def clear_form():
    entry_name.delete(0, tk.END)
    entry_country.delete(0, tk.END)
    combobox_type.set('')
    entry_date.delete(0, tk.END)
    entry_description.delete("1.0", tk.END)
    entry_source.delete(0, tk.END)
    combobox_impact.set('')

# Function to add event
def add_event():
    name = entry_name.get().strip()
    country = entry_country.get().strip()
    event_type = combobox_type.get().strip()
    date = entry_date.get().strip()
    description = entry_description.get("1.0", tk.END).strip()
    source = entry_source.get().strip()
    impact = combobox_impact.get().strip()

    # Basic validation
    if not name or not country or not event_type or not date:
        messagebox.showerror("Error", "Please fill in required fields: Name, Country, Type, Date.")
        return

    if not validate_date(date):
        messagebox.showerror("Error", "Date must be in DD/MM/YYYY format (e.g. 25/09/2025).")
        return

    # Insert event into database
    try:
        cursor.execute("""
            INSERT INTO events (name, country, type, date, description, source, impact)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, country, event_type, date, description, source, impact))
        conn.commit()
        messagebox.showinfo("Success", "Event added successfully!")
        clear_form()
    except Exception as e:
        messagebox.showerror("Database error", str(e))

# Function to export to CSV
def export_csv(treeview):
    rows = [treeview.item(i)["values"] for i in treeview.get_children()]
    if not rows:
        messagebox.showinfo("Export", "No rows to export.")
        return
    filename = "worldscope_export.csv"
    try:
        with open(filename, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Country", "Type", "Date", "Impact"])
            writer.writerows(rows)
        messagebox.showinfo("Export", f"Exported {len(rows)} rows to {filename}")
    except Exception as e:
        messagebox.showerror("Export Error", str(e))

# Function to view events
def view_events():
    view_win = tk.Toplevel(root)
    view_win.title("View Events")
    view_win.geometry("850x400")

    # Filter frame
    filter_frame = tk.Frame(view_win)
    filter_frame.pack(fill="x", padx=8, pady=6)

    tk.Label(filter_frame, text="Country:").grid(row=0, column=0, padx=4, sticky="w")
    tk.Label(filter_frame, text="Type:").grid(row=0, column=2, padx=4, sticky="w")

    # Country dropdown
    cursor.execute("SELECT DISTINCT country FROM events ORDER BY country ASC")
    countries = ["All"] + [r[0] for r in cursor.fetchall()]

    # Type dropdown
    cursor.execute("SELECT DISTINCT type FROM events ORDER BY type ASC")
    types = ["All"] + [r[0] for r in cursor.fetchall()]

    country_var = tk.StringVar(master=view_win, value="All")
    type_var = tk.StringVar(master=view_win, value="All")

    country_menu = ttk.Combobox(filter_frame, values=countries, textvariable=country_var, state="readonly", width=30)
    country_menu.grid(row=0, column=1, padx=4)
    type_menu = ttk.Combobox(filter_frame, values=types, textvariable=type_var, state="readonly", width=28)
    type_menu.grid(row=0, column=3, padx=4)

    tree_frame = tk.Frame(view_win)
    tree_frame.pack(fill="both", expand=True, padx=8, pady=(0,8))

    cols = ("id", "name", "country", "type", "date", "impact")
    tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")

    for c in cols:
        tree.heading(c, text=c.title())

    tree.column("id", width=40, anchor="center")
    tree.column("name", width=220)
    tree.column("country", width=120, anchor="center")
    tree.column("type", width=120, anchor="center")
    tree.column("date", width=100, anchor="center")
    tree.column("impact", width=80, anchor="center")

    ysb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=ysb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    ysb.grid(row=0, column=1, sticky="ns")
    tree_frame.grid_rowconfigure(0, weight=1)
    tree_frame.grid_columnconfigure(0, weight=1)

    # Load data function
    def load_data():
        # Clear existing data
        for child in tree.get_children():
            tree.delete(child)

        query = "SELECT id, name, country, type, date, impact FROM events"
        conditions = []
        params = []

        if country_var.get() != "All":
            conditions.append("country = ?")
            params.append(country_var.get())
        if type_var.get() != "All":
            conditions.append("type = ?")
            params.append(type_var.get())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY date DESC"

        cursor.execute(query, params)
        for row in cursor.fetchall():
            tree.insert("", tk.END, values=row)

    # Delete selected event
    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("Delete", "No event selected.")
            return

        event_id = tree.item(selected[0])["values"][0]
        confirm = messagebox.askyesno("Delete", f"Delete event ID {event_id}?")
        if confirm:
            cursor.execute("DELETE FROM events WHERE id = ?", (event_id,))
            conn.commit()
            tree.delete(selected[0])
            messagebox.showinfo("Delete", f"Event ID {event_id} deleted.")

    # Buttons
    btn_frame = tk.Frame(filter_frame)
    btn_frame.grid(row=0, column=4, padx=8)
    ttk.Button(btn_frame, text="Apply", command=load_data).pack(side="left", padx=2)
    ttk.Button(btn_frame, text="Clear", command=lambda: (country_var.set("All"), type_var.set("All"), load_data())).pack(side="left", padx=2)
    ttk.Button(btn_frame, text="Export CSV", command=lambda: export_csv(tree)).pack(side="left", padx=6)
    ttk.Button(btn_frame, text="Delete Selected", command=delete_selected).pack(side="left", padx=6)

    load_data()

def on_closing():
    if messagebox.askokcancel("Quit", "Do you want to quit WorldScope?"):
        try:
            conn.close()
        except:
            pass
        finally:
            root.destroy()

# FUNCTION TO SHOW LOGIN SCREEN 
def show_login():
    login_win = tk.Toplevel()
    login_win.title("Login")
    login_win.geometry("300x150")
    login_win.grab_set()  # focus

    tk.Label(login_win, text="Username:").pack(pady=5)
    username_entry = ttk.Entry(login_win, width=25)
    username_entry.pack()

    tk.Label(login_win, text="Password:").pack(pady=5)
    password_entry = ttk.Entry(login_win, show="*", width=25)
    password_entry.pack()

    def check_login():
        username = username_entry.get()
        password = password_entry.get()
        if username == "user" and password == "1234":
            messagebox.showinfo("Login", "Login successful!")
            login_win.destroy()
            root.deiconify()  # Show main GUI
        else:
            messagebox.showerror("Login", "Invalid credentials!")

    ttk.Button(login_win, text="Login", command=check_login).pack(pady=10)

# Main GUI layout
frm = tk.Frame(root, padx=12, pady=12)
frm.pack(fill="both", expand=True)

tk.Label(frm, text="Event Name *").pack(anchor="w")
entry_name = ttk.Entry(frm, width=50)
entry_name.pack(anchor="w", pady=2)

tk.Label(frm, text="Country *").pack(anchor="w")
entry_country = ttk.Entry(frm, width=50)
entry_country.pack(anchor="w", pady=2)

tk.Label(frm, text="Type of Event *").pack(anchor="w")
combobox_type = ttk.Combobox(frm, values=TYPE_OPTIONS, width=48)
combobox_type.pack(anchor="w", pady=2)

tk.Label(frm, text="Date (DD/MM/YYYY) *").pack(anchor="w")
entry_date = ttk.Entry(frm, width=50)
entry_date.pack(anchor="w", pady=2)

tk.Label(frm, text="Description").pack(anchor="w")
desc_frame = tk.Frame(frm)
desc_frame.pack(anchor="w", pady=4, fill="x")
entry_description = tk.Text(desc_frame, width=50, height=6)
scrollbar_desc = ttk.Scrollbar(desc_frame, orient="vertical", command=entry_description.yview)
entry_description.configure(yscrollcommand=scrollbar_desc.set)
entry_description.pack(side="left", fill="both", expand=True)
scrollbar_desc.pack(side="right", fill="y")

tk.Label(frm, text="Source (URL / reference)").pack(anchor="w")
entry_source = ttk.Entry(frm, width=50)
entry_source.pack(anchor="w", pady=2)

tk.Label(frm, text="Impact Level").pack(anchor="w")
combobox_impact = ttk.Combobox(frm, values=IMPACT_OPTIONS, width=48)
combobox_impact.pack(anchor="w", pady=2)

btns = tk.Frame(frm)
btns.pack(anchor="center", pady=12)
ttk.Button(btns, text="Add Event", command=add_event).grid(row=0, column=0, padx=8)
ttk.Button(btns, text="View Events", command=view_events).grid(row=0, column=1, padx=8)
ttk.Button(btns, text="Clear Form", command=clear_form).grid(row=0, column=2, padx=8)

root.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    show_login()  # Show login first
    root.mainloop()
