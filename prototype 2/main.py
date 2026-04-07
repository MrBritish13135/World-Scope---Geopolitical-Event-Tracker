import customtkinter as ctk
from tkinter import ttk, messagebox
import database_p2 as db
from auth import AuthWindow

class Dashboard(ctk.CTk):
    def __init__(self, username, logout_callback):
        super().__init__()
        self.logout_callback = logout_callback
        self.title(f"WorldScope Dashboard - {username}")
        self.geometry("900x900")

        # Top Bar for Logout
        self.top_nav = ctk.CTkFrame(self, height=50)
        self.top_nav.pack(side="top", fill="x")
        ctk.CTkLabel(self.top_nav, text=f"Logged in as: {username}").pack(side="left", padx=20)
        ctk.CTkButton(self.top_nav, text="Logout", fg_color="red", width=80, command=self.logout).pack(side="right", padx=20)

        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(padx=20, pady=10, fill="both", expand=True)
        self.tab_view = self.tabs.add("View Events")
        self.tab_add = self.tabs.add("Add Event")

        self.setup_view_tab()
        self.setup_add_tab()

    def setup_view_tab(self):
        cols = ("ID", "Name", "Country", "Start Date", "End Date", "Impact")
        self.tree = ttk.Treeview(self.tab_view, columns=cols, show="headings")
        for col in cols:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        self.tree.pack(pady=10, fill="both", expand=True)

        btn_frame = ctk.CTkFrame(self.tab_view, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="Refresh List", command=self.refresh).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Delete Selected", fg_color="red", command=self.delete_selected).pack(side="right", padx=10)
        self.refresh()

    def setup_add_tab(self):
        # Entry form with separate date fields
        ctk.CTkLabel(self.tab_add, text="Event Name:").pack(pady=5)
        self.e_name = ctk.CTkEntry(self.tab_add, width=300); self.e_name.pack()

        ctk.CTkLabel(self.tab_add, text="Country:").pack(pady=5)
        self.e_country = ctk.CTkEntry(self.tab_add, width=300); self.e_country.pack()

        ctk.CTkLabel(self.tab_add, text="Start Date:").pack(pady=5)
        self.e_start = ctk.CTkEntry(self.tab_add, width=300); self.e_start.pack()

        ctk.CTkLabel(self.tab_add, text="End Date:").pack(pady=5)
        self.e_end = ctk.CTkEntry(self.tab_add, width=300); self.e_end.pack()

        ctk.CTkButton(self.tab_add, text="Add Event", command=self.save).pack(pady=20)

    def save(self):
        db.add_event(self.e_name.get(), self.e_country.get(), "General", self.e_start.get(), self.e_end.get(), "Medium")
        messagebox.showinfo("Success", "Event Added!")
        self.refresh()
        self.tabs.set("View Events")

    def refresh(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for row in db.get_events(): self.tree.insert("", "end", values=row)

    def delete_selected(self):
        selected = self.tree.selection()
        if selected:
            item_id = self.tree.item(selected[0])['values'][0]
            if messagebox.askyesno("Confirm", "Delete this record?"):
                db.delete_event(item_id)
                self.refresh()

    def logout(self):
        self.destroy()
        self.logout_callback()

def start():
    db.init_db()
    def handle_login(user):
        app = Dashboard(user, start) # Passing start back as the logout callback
        app.mainloop()

    auth = AuthWindow(handle_login)
    auth.mainloop()

if __name__ == "__main__":
    start()