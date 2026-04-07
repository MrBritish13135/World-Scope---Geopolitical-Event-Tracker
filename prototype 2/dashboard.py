import customtkinter as ctk
from tkinter import ttk, messagebox
import database_p2 as db

class Dashboard(ctk.CTk):
    def __init__(self, username, logout_callback):
        super().__init__()
        self.logout_callback = logout_callback
        self.title(f"WorldScope P2 - Logged in as: {username}")
        self.geometry("900x900")

        # --- 1. TOP NAVIGATION BAR (For Logout) ---
        self.nav_bar = ctk.CTkFrame(self, height=50, corner_radius=0)
        self.nav_bar.pack(side="top", fill="x")
        
        self.user_label = ctk.CTkLabel(self.nav_bar, text=f"Welcome, {username}", font=("Arial", 14, "bold"))
        self.user_label.pack(side="left", padx=20)
        
        self.btn_logout = ctk.CTkButton(self.nav_bar, text="Logout", fg_color="#d35400", 
                                        hover_color="#e67e22", width=100, command=self.logout)
        self.btn_logout.pack(side="right", padx=20)

        # --- 2. TABBED INTERFACE ---
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)
        self.tab_view = self.tabs.add("View Events")
        self.tab_add = self.tabs.add("Add Event")

        self.setup_view_tab()
        self.setup_add_tab()

    def setup_view_tab(self):
        # Treeview for Data Visualization
        cols = ("ID", "Name", "Country", "Start Date", "End Date", "Impact")
        self.tree = ttk.Treeview(self.tab_view, columns=cols, show="headings")
        
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        self.tree.pack(pady=10, fill="both", expand=True)

        # Control Buttons
        btn_frame = ctk.CTkFrame(self.tab_view, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="Refresh List", command=self.load_data).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Delete Selected", fg_color="red", command=self.delete_item).pack(side="right", padx=10)
        
        self.load_data()

    def setup_add_tab(self):
        # Organized Grid Layout for the Form
        form_frame = ctk.CTkFrame(self.tab_add, fg_color="transparent")
        form_frame.pack(pady=30)

        # Event Name
        ctk.CTkLabel(form_frame, text="Event Name:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        self.e_name = ctk.CTkEntry(form_frame, width=250)
        self.e_name.grid(row=0, column=1)

        # Country
        ctk.CTkLabel(form_frame, text="Country:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        self.e_country = ctk.CTkEntry(form_frame, width=250)
        self.e_country.grid(row=1, column=1)

        # Start Date
        ctk.CTkLabel(form_frame, text="Start Date (DD/MM/YYYY):").grid(row=2, column=0, padx=10, pady=10, sticky="e")
        self.e_start = ctk.CTkEntry(form_frame, width=250, placeholder_text="e.g. 01/01/2026")
        self.e_start.grid(row=2, column=1)

        # End Date
        ctk.CTkLabel(form_frame, text="End Date (DD/MM/YYYY):").grid(row=3, column=0, padx=10, pady=10, sticky="e")
        self.e_end = ctk.CTkEntry(form_frame, width=250, placeholder_text="e.g. 05/01/2026")
        self.e_end.grid(row=3, column=1)

        # Impact
        ctk.CTkLabel(form_frame, text="Impact Level:").grid(row=4, column=0, padx=10, pady=10, sticky="e")
        self.e_impact = ctk.CTkComboBox(form_frame, values=["Low", "Medium", "High", "Severe"], width=250)
        self.e_impact.grid(row=4, column=1)

        # Submit
        self.btn_submit = ctk.CTkButton(self.tab_add, text="Save Event to Database", 
                                        command=self.submit_event, width=200, height=40)
        self.btn_submit.pack(pady=20)

    def load_data(self):
        """Clears tree and fetches fresh data from database module"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # database_p2.get_events() should return rows with our new columns
        for row in db.get_events():
            self.tree.insert("", "end", values=row)

    def submit_event(self):
        """Handles validation and sending data to database_p2"""
        name = self.e_name.get()
        country = self.e_country.get()
        s_date = self.e_start.get()
        e_date = self.e_end.get()
        impact = self.e_impact.get()

        if not all([name, country, s_date, e_date]):
            messagebox.showwarning("Input Error", "Please fill in all date and name fields.")
            return

        db.add_event(name, country, "General", s_date, e_date, impact)
        messagebox.showinfo("Success", f"Event '{name}' has been recorded.")
        
        # Clear fields
        self.e_name.delete(0, 'end')
        self.e_country.delete(0, 'end')
        self.e_start.delete(0, 'end')
        self.e_end.delete(0, 'end')
        
        self.load_data()
        self.tabs.set("View Events") # Switch tab automatically

    def delete_item(self):
        selected = self.tree.selection()
        if selected:
            item_id = self.tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", "Delete this record?"):
                db.delete_event(item_id)
                self.load_data()

    def logout(self):
        """Closes dashboard and triggers the login window to return"""
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            self.destroy()
            self.logout_callback()