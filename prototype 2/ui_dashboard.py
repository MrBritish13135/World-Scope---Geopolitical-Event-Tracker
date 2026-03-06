import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import database

class DashboardFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True, padx=10, pady=10)
        
        
        self.left_frm = tk.Frame(self, width=300)
        self.left_frm.pack(side="left", fill="y", padx=10)
        
        self.right_frm = tk.Frame(self)
        self.right_frm.pack(side="right", fill="both", expand=True)

        self.setup_form()
        self.setup_treeview()
        self.refresh_data()

    def setup_form(self):
        """Creates the 'Add Event' inputs"""
        tk.Label(self.left_frm, text="ADD NEW EVENT", font=("Arial", 12, "bold")).pack(pady=10)
        
        tk.Label(self.left_frm, text="Event Name").pack(anchor="w")
        self.ent_name = ttk.Entry(self.left_frm)
        self.ent_name.pack(fill="x", pady=2)

        tk.Label(self.left_frm, text="Country").pack(anchor="w")
        self.ent_country = ttk.Entry(self.left_frm)
        self.ent_country.pack(fill="x", pady=2)

        tk.Label(self.left_frm, text="Type").pack(anchor="w")
        self.cb_type = ttk.Combobox(self.left_frm, values=["Election", "Protest", "Summit", "Conflict"])
        self.cb_type.pack(fill="x", pady=2)

        tk.Label(self.left_frm, text="Date (DD/MM/YYYY)").pack(anchor="w")
        self.ent_date = ttk.Entry(self.left_frm)
        self.ent_date.pack(fill="x", pady=2)

        ttk.Button(self.left_frm, text="Save Event", command=self.save_event).pack(pady=15)

    def setup_treeview(self):
        """Creates the data display"""
        tk.Label(self.right_frm, text="EVENT LOG", font=("Arial", 12, "bold")).pack(pady=10)
        cols = ("ID", "Name", "Country", "Type", "Date")
        self.tree = ttk.Treeview(self.right_frm, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=100)
        self.tree.pack(fill="both", expand=True)

    def save_event(self):
        """Validates and sends data to database.py"""
        name = self.ent_name.get()
        country = self.ent_country.get()
        etype = self.cb_type.get()
        date = self.ent_date.get()

        if not name or not country:
            messagebox.showerror("Error", "Name and Country are required!")
            return

        success = database.add_event_to_db(name, country, etype, date, "", "", "")
        if success:
            messagebox.showinfo("Success", "Event added!")
            self.refresh_data()
            self.clear_fields()

    def refresh_data(self):
        """Clears and reloads the list"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for row in database.get_all_events():
            self.tree.insert("", tk.END, values=row)

    def clear_fields(self):
        self.ent_name.delete(0, tk.END)
        self.ent_country.delete(0, tk.END)