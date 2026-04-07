import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import geopandas as gpd
import pandas as pd
import os
import csv
from datetime import datetime
import shutil
from database import (
    fetch_events, fetch_event_by_id, insert_event, update_event, delete_event_from_db,
    fetch_users, create_user, update_user, delete_user, admin_reset_password,
    user_exists, fetch_event_types, get_events_by_country, get_events_by_actor_country,
    get_events_by_type, get_events_by_impact,backup_database, get_recent_logs,
    fetch_event_actors, set_event_actors,
    fetch_event_locations, set_event_locations,
    get_dashboard_stats, event_name_exists,
    get_logs_filtered, get_all_log_usernames,
    fetch_deleted_events_filtered, get_deleted_by_options,
)
import re
from countries import VALID_COUNTRIES


class DashboardFrame(ctk.CTkFrame):
    def __init__(self, master, user, on_logout):
        super().__init__(master)
        self.user = user
        self.on_logout = on_logout

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.build_sidebar()
        self.build_content()
        self.show_dashboard()

    def build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, border_width=1, border_color="#333333")
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        # Profile Section
        ctk.CTkLabel(self.sidebar, text="👤", font=("Roboto", 50)).pack(pady=(30, 5))
        ctk.CTkLabel(self.sidebar, text=f"{self.user['username'].upper()}",
                     font=("Roboto", 16, "bold"), text_color="#3b8ed0").pack(pady=(0, 30))

        # Nav Buttons
        menu_items = [
            ("📊 Dashboard", self.show_dashboard),
            ("🌍 Event Logs", self.load_events_view),
            ("⚙️ Settings", self.show_settings)
        ]

        if self.user["role"] == "admin":
            menu_items.insert(2, ("👥 User Mgmt", self.show_users))
            menu_items.insert(3, ("🗑️ Deleted Events", self.show_deleted_events))
            menu_items.insert(4, ("📋 Activity Logs", self.show_activity_logs))

        for text, cmd in menu_items:
            btn = ctk.CTkButton(self.sidebar, text=text, font=("Roboto", 13),
                                fg_color="transparent", text_color=("gray10", "gray90"),
                                hover_color=("#dbdbdb", "#2b2b2b"), anchor="w", command=cmd)
            btn.pack(fill="x", padx=15, pady=5)

        # Switch User
        self.switch_button = ctk.CTkButton(
            self.sidebar, text="🔄 Switch User", fg_color="#8e44ad",
            border_width=1, command=self.switch_user, hover_color="#732d91"
        )
        self.switch_button.pack(side="bottom", fill="x", padx=20, pady=(0, 10))

        # Logout
        ctk.CTkButton(self.sidebar, text="🚪 Logout", fg_color="#c0392b",
                      hover_color="#e74c3c", command=self.logout).pack(side="bottom", fill="x", padx=20, pady=20)

    def build_content(self):
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    # --- VIEWS ---

    def show_dashboard(self):
        self.clear_content()

        # Header & Submenu Bar
        header_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(header_frame, text="Global Event Data Dashboard", font=("Roboto", 28, "bold")).pack(side="left")

        # Submenu Buttons
        nav_bar = ctk.CTkFrame(self.content, height=40)
        nav_bar.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(nav_bar, text="Types of Events Compared", width=150, command=self.draw_type_chart).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(nav_bar, text="Impact Levels", width=120, command=self.draw_impact_chart).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(nav_bar, text="Heat Map: Location", width=140, command=lambda: self.draw_world_map("location")).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(nav_bar, text="Heat Map: Actors", width=130, command=lambda: self.draw_world_map("actors")).pack(side="left", padx=5, pady=5)

        # ── Summary stats bar ──────────────────────────────────────────────
        stats = get_dashboard_stats()
        stats_bar = ctk.CTkFrame(self.content, corner_radius=12,
                                 fg_color=("#e8f4fd", "#1e3a4a"), border_width=1,
                                 border_color=("#3b8ed0", "#3b8ed0"))
        stats_bar.pack(fill="x", pady=(0, 10))

        stat_items = [
            ("📦", str(stats["total"]),       "Total Events"),
            ("🔴", str(stats["high_impact"]), "High Impact"),
            ("🔄", str(stats["ongoing"]),     "Ongoing"),
            ("🌍", str(stats["countries"]),   "Countries"),
        ]
        for icon, count, label in stat_items:
            cell = ctk.CTkFrame(stats_bar, fg_color="transparent")
            cell.pack(side="left", padx=30, pady=8)
            ctk.CTkLabel(cell, text=f"{icon}  {count}",
                         font=("Roboto", 22, "bold"),
                         text_color="#3b8ed0").pack()
            ctk.CTkLabel(cell, text=label,
                         font=("Roboto", 10),
                         text_color="gray").pack()

        # Chart Container
        self.chart_container = ctk.CTkFrame(self.content, fg_color="#2b2b2b", corner_radius=15)
        self.chart_container.pack(fill="both", expand=True)

        if self.user["role"] == "admin":
            activity_frame = ctk.CTkFrame(self.content, height=160, corner_radius=15, border_width=1)
            activity_frame.pack(fill="x")

            ctk.CTkLabel(activity_frame, text="🕒 Recent System Activity",
                         font=("Roboto", 14, "bold"), text_color="#3b8ed0").pack(anchor="w", padx=20, pady=(10, 5))

            log_display = ctk.CTkTextbox(activity_frame, height=100, font=("Consolas", 12), activate_scrollbars=True)
            log_display.pack(fill="both", expand=True, padx=20, pady=(0, 15))

            logs = get_recent_logs(5)
            log_display.insert("0.0", "".join(logs))
            log_display.configure(state="disabled")

        # Default view
        self.draw_type_chart()

    def get_theme_colors(self):
        if ctk.get_appearance_mode() == "Dark":
            return {
                "bg": "#2b2b2b",
                "fg": "white",
                "accent": "#3b8ed0",
                "text": "white"
            }
        else:
            return {
                "bg": "#dbdbdb",
                "text": "black",
                "grid": "#bcbcbc"
            }

    def clear_charts(self):
        for widget in self.chart_container.winfo_children():
            widget.destroy()

    def draw_type_chart(self):
        self.current_chart_type = "type"
        self.clear_charts()
        data = get_events_by_type()
        if not data:
            return

        colors = self.get_theme_colors()
        types, counts = zip(*data)

        fig, ax = plt.subplots(figsize=(7, 5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        ax.bar(types, counts, color='#3b8ed0')
        ax.set_title("Events by Category", color=colors["text"], pad=15)
        ax.tick_params(colors=colors["text"])

        for spine in ax.spines.values():
            spine.set_edgecolor(colors["text"])

        self.render_figure(fig)

    def draw_impact_chart(self):
        self.current_chart_type = "impact"
        self.clear_charts()
        data = get_events_by_impact()
        if not data:
            ctk.CTkLabel(self.chart_container, text="No impact data available yet.").pack(expand=True)
            return

        colors = self.get_theme_colors()
        impacts, counts = zip(*data)
        colour_map = {"High": "#e74c3c", "Medium": "#f1c40f", "Low": "#2ecc71"}
        chart_colours = [colour_map.get(imp, "#3b8ed0") for imp in impacts]

        fig, ax = plt.subplots(figsize=(6, 4), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])

        pie_result = ax.pie(
            counts,
            labels=impacts,
            autopct='%1.1f%%',
            startangle=140,
            textprops={'color': colors["text"], 'fontsize': 10},
            colors=chart_colours,
            pctdistance=0.85
        )

        if len(pie_result) == 3:
            _, _, autotexts = pie_result
            for autotext in autotexts:
                autotext.set_fontweight('bold')

        ax.set_title("Impact Severity Distribution", color=colors["text"], pad=20, fontsize=14, weight='bold')
        self.render_figure(fig)

    def show_settings(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text=" Account & Application Settings", font=("Roboto", 28, "bold")).pack(pady=(0, 20), anchor="w")

        settings_card = ctk.CTkFrame(self.content, fg_color=("#f9f9f9", "#252525"), corner_radius=15, border_width=1)
        settings_card.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(settings_card, text="Appearance Mode", font=("Roboto", 14, "bold")).pack(pady=(15, 5), padx=20, anchor="w")
        mode_menu = ctk.CTkOptionMenu(settings_card, values=["Dark", "Light", "System"],
                                      command=self.change_appearance_mode)
        mode_menu.pack(pady=(0, 15), padx=20, anchor="w")
        mode_menu.set(ctk.get_appearance_mode())

        if self.user.get("role") == "admin":
            admin_card = ctk.CTkFrame(self.content, fg_color=("#f1f1f1", "#1a1a1a"), corner_radius=15, border_width=2, border_color="#3b8ed0")
            admin_card.pack(fill="x", padx=5, pady=10)

            ctk.CTkLabel(admin_card, text="🛠️ Administrative Tools", font=("Roboto", 14, "bold"), text_color="#3b8ed0").pack(pady=(15, 5), padx=20, anchor="w")

            ctk.CTkButton(admin_card, text="Backup Database", fg_color="#2980b9", hover_color="#3498db",
                          command=self.run_backup).pack(side="left", padx=20, pady=(0, 20))

            ctk.CTkLabel(admin_card, text="Create a timestamped security snapshot of the database.",
                         font=("Roboto", 11), text_color="gray").pack(side="left", pady=(0, 20))

        # --- Password Section ---
        pwd_card = ctk.CTkFrame(self.content, fg_color=("#f9f9f9", "#252525"), corner_radius=15, border_width=1)
        pwd_card.pack(fill="x", padx=5, pady=10)

        ctk.CTkLabel(pwd_card, text="Security: Change Password", font=("Roboto", 14, "bold")).pack(pady=(15, 5), padx=20, anchor="w")
        self.old_pwd = ctk.CTkEntry(pwd_card, placeholder_text="Current Password", show="*", width=200)
        self.old_pwd.pack(side="left", padx=20, pady=10)
        self.new_pwd = ctk.CTkEntry(pwd_card, placeholder_text="New Password", show="*", width=200)
        self.new_pwd.pack(side="left", padx=10, pady=10)
        ctk.CTkButton(pwd_card, text="Update Password", command=self.change_password_action).pack(side="left", padx=10)

        # System Info
        ctk.CTkLabel(settings_card, text="System Info", font=("Roboto", 14, "bold")).pack(pady=(10, 5), padx=20, anchor="w")
        ctk.CTkLabel(settings_card, text=f"Logged in as: {self.user['username']} | Role: {self.user['role']}",
                     text_color="gray").pack(pady=(0, 20), padx=20, anchor="w")

    def change_appearance_mode(self, new_mode: str):
        ctk.set_appearance_mode(new_mode)

        if hasattr(self, 'chart_container'):
            try:
                if self.chart_container.winfo_exists():
                    is_dark = (new_mode == "Dark")
                    self.chart_container.configure(fg_color="#2b2b2b" if is_dark else "#dbdbdb")
                    if hasattr(self, 'current_chart_type'):
                        if self.current_chart_type == "type":
                            self.draw_type_chart()
                        elif self.current_chart_type == "impact":
                            self.draw_impact_chart()
                        elif self.current_chart_type == "map":
                            self.draw_world_map(getattr(self, 'current_map_mode', 'location'))
            except (tk.TclError, AttributeError):
                pass

    def change_password_action(self):
        from database import verify_user_password, update_own_password

        old = self.old_pwd.get().strip()
        new = self.new_pwd.get().strip()
        if not old or not new:
            messagebox.showerror("Error", "Both fields are required.")
            return

        if verify_user_password(self.user["username"], old):
            update_own_password(self.user["username"], new)
            messagebox.showinfo("Success", "Password updated successfully.")
            self.old_pwd.delete(0, 'end')
            self.new_pwd.delete(0, 'end')
        else:
            messagebox.showerror("Error", "Current password is incorrect.")

    def run_backup(self):
        success, message = backup_database()
        if success:
            from database import log_activity
            log_activity(self.user['username'], f"Database Backup Created: {message}")

            confirm = messagebox.askyesno("Success",
                f"Backup created successfully!\n\nWould you like to open the backups folder?")

            if confirm:
                backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
                if not os.path.exists(backup_path):
                    os.makedirs(backup_path)
                # os.startfile() is Windows-only; use a cross-platform approach
                import sys, subprocess
                if sys.platform == "win32":
                    os.startfile(backup_path)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", backup_path])
                else:
                    subprocess.Popen(["xdg-open", backup_path])
        else:
            messagebox.showerror("Backup Failed", f"Error: {message}")

    # --- EVENTS VIEW ---

    def load_events_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Global Event Logs", font=("Roboto", 24, "bold")).pack(pady=(0, 10), anchor="w")

        # Search Bar
        search_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        search_bar.pack(fill="x", pady=5)

        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search by name, country, or description...", width=400)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.run_search())

        ctk.CTkButton(search_bar, text="🔍 Search", width=80, command=self.run_search).pack(side="left", padx=5)
        ctk.CTkButton(search_bar, text="🧹 Clear", width=80, fg_color="#7f8c8d", hover_color="#95a5a6",
                      command=self.clear_search).pack(side="left", padx=5)

        # Filters
        ctk.CTkLabel(search_bar, text="Country:").pack(side="left", padx=5)
        self.country_filter = ctk.CTkOptionMenu(search_bar, values=["All"] + VALID_COUNTRIES)
        self.country_filter.pack(side="left", padx=5)
        self.country_filter.set("All")

        ctk.CTkLabel(search_bar, text="Type:").pack(side="left", padx=5)
        types = fetch_event_types()
        if types is None:
            types = []
        self.type_filter = ctk.CTkOptionMenu(search_bar, values=["All"] + [t[1] for t in types])
        self.type_filter.pack(side="left", padx=5)
        self.type_filter.set("All")

        ctk.CTkButton(search_bar, text="📥 Export CSV", width=100, fg_color="#34495e", hover_color="#2c3e50",
                      command=self.export_to_csv).pack(side="right", padx=5)

        user_role = self.user.get("role", "viewer").lower()

        # Event Action Bar
        action_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        action_bar.pack(fill="x", pady=5)

        if user_role in ["admin", "analyst"]:
            ctk.CTkButton(action_bar, text="➕ Add Event", width=120,
                          fg_color="#27ae60", command=self.add_event_popup).pack(side="left", padx=5)
            ctk.CTkButton(action_bar, text="📝 Edit Event", width=120,
                          fg_color="#f39c12", command=self.edit_event_popup).pack(side="left", padx=5)
            ctk.CTkButton(action_bar, text="🗑️ Delete", width=120,
                          fg_color="#e74c3c", command=self.delete_event).pack(side="left", padx=5)
        else:
            ctk.CTkLabel(action_bar, text="Remember: Viewer role can only view events.",
                         font=("Roboto", 11, "italic"), text_color="gray").pack(side="left", padx=10)

        # Treeview configuration
        columns = ("ID", "Name", "Location", "Type", "Start Date", "End Date", "Impact", "Actor Countries")
        self.tree = ttk.Treeview(self.content, columns=columns, show="headings")
        col_widths = {"ID": 40, "Name": 160, "Location": 120, "Type": 100,
                      "Start Date": 95, "End Date": 95, "Impact": 70, "Actor Countries": 220}
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.treeview_sort_column(self.tree, c, False))
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center")

        self.tree.pack(fill="both", expand=True, pady=10)
        self.load_events_data()

    def run_search(self):
        term = self.search_entry.get().strip()
        country = self.country_filter.get() if hasattr(self, 'country_filter') else "All"
        event_type = self.type_filter.get() if hasattr(self, 'type_filter') else "All"

        for item in self.tree.get_children():
            self.tree.delete(item)
        from database import fetch_events_filtered
        results = fetch_events_filtered(term, country, event_type)
        if results is None:
            results = []
        for event in results:
            self.tree.insert("", "end", values=event)

    def load_events_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for event in fetch_events():
            self.tree.insert("", "end", values=event)

    def add_event_popup(self):
        EventPopup(self)

    def edit_event_popup(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an event to edit.")
            return
        event_id = self.tree.item(selected[0])['values'][0]
        EventPopup(self, event_id)

    def delete_event(self):
        user_role = self.user.get("role", "viewer").lower()
        if user_role == "viewer":
            messagebox.showerror("Permission Denied", "Viewers do not have delete permissions.")
            return

        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select an event to delete.")
            return

        event_data = self.tree.item(selected[0])["values"]
        event_id = int(event_data[0])   # Treeview values are strings; cast to int
        event_name = event_data[1]

        if messagebox.askyesno("Confirm", f"Permanently delete event: {event_name}?\nThis action will be logged."):
            success = delete_event_from_db(event_id, event_name, self.user["username"])
            if success:
                messagebox.showinfo("Success", "Event archived.")
                self.load_events_data()
            else:
                messagebox.showerror("Error", "Could not delete. Check console for errors.")

    def export_to_csv(self):
        try:
            filename = "worldscope_export.csv"
            file_path = os.path.join(os.getcwd(), filename)
            events = fetch_events()

            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["ID", "Name", "Location", "Type", "Start Date", "End Date", "Impact", "Actor Countries"])
                writer.writerows(events)

            messagebox.showinfo("Exported", f"Events exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {e}")

    # --- USER MANAGEMENT ---

    def show_users(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.content, text="User Management", font=("Roboto", 24, "bold")).pack(pady=10, anchor="w")

        action_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        action_bar.pack(fill="x", pady=5)

        ctk.CTkButton(action_bar, text="➕ Add User", width=120,
                      command=self.add_user_popup).pack(side="left", padx=5)
        ctk.CTkButton(action_bar, text="📝 Edit User", fg_color="#f39c12", hover_color="#d35400", width=120,
                      command=lambda: self.edit_user_popup()).pack(side="left", padx=5)
        ctk.CTkButton(action_bar, text="🗑️ Delete User", fg_color="#e74c3c", hover_color="#c0392b", width=120,
                      command=self.delete_user_action).pack(side="left", padx=5)

        columns = ("ID", "User", "Role", "First Name", "Last Name", "Login Date", "Login Time")
        self.user_tree = ttk.Treeview(self.content, columns=columns, show="headings")

        for col in columns:
            self.user_tree.heading(col, text=col,
                                   command=lambda c=col: self.sort_treeview(self.user_tree, c, False))
            if col == "ID":
                self.user_tree.column(col, anchor="center", width=50)
            elif "Login" in col:
                self.user_tree.column(col, anchor="center", width=150)
            else:
                self.user_tree.column(col, anchor="center", width=120)

        self.user_tree.pack(fill="both", expand=True, pady=10)
        self.refresh_user_list()

    # BUG FIX: The original sort_treeview had a broken for-else indentation.
    # The 'else' was attached to the 'for' loop (running once after the loop)
    # instead of being the else branch of the inner 'if c == col' check.
    # Fixed by using a proper if/else inside the for loop.
    def sort_treeview(self, tree, col, reverse):
        data = [(tree.set(k, col), k) for k in tree.get_children('')]

        try:
            data.sort(key=lambda t: float(t[0]) if t[0] else 0, reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

        for index, (_, k) in enumerate(data):
            tree.move(k, '', index)

        # FIX: was a for-else (else ran once after loop on last 'c' only)
        for c in tree["columns"]:
            if c == col:
                arrow = " ▼" if reverse else " ▲"
                tree.heading(c, text=c + arrow,
                             command=lambda _c=c: self.sort_treeview(tree, _c, not reverse))
            else:
                tree.heading(c, text=c,
                             command=lambda _c=c: self.sort_treeview(tree, _c, False))

    def refresh_user_list(self):
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        from database import fetch_users
        users = fetch_users()
        for u in users:
            l_date = u[5] if (len(u) > 5 and u[5]) else "Never"
            l_time = u[6] if (len(u) > 6 and u[6]) else ""
            self.user_tree.insert("", "end", values=(u[0], u[1], u[2], u[3], u[4], l_date, l_time))

    def add_user_popup(self):
        UserPopup(self)

    def edit_user_popup(self, _=None):
        selected = self.user_tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a user to edit.")
            return
        user_id = self.user_tree.item(selected[0])["values"][0]
        UserPopup(self, user_id)

    def delete_user_action(self):
        selected = self.user_tree.selection()
        if not selected:
            return
        u_data = self.user_tree.item(selected[0])["values"]
        if u_data[1] == self.user["username"]:
            messagebox.showerror("Error", "You cannot delete your own account.")
            return
        if messagebox.askyesno("Confirm", f"Remove user {u_data[1]}?"):
            delete_user(int(u_data[0]))   # Treeview values are strings; cast to int
            self.refresh_user_list()

    def switch_user(self):
        if messagebox.askyesno("Switch User", "Are you sure you want to switch users? Unsaved changes will be lost."):
            self.on_logout(should_restart=True)

    def logout(self):
        response = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if response:
            self.on_logout(should_restart=False)

    def draw_world_map(self, mode="location"):
        self.current_chart_type = "map"
        self.current_map_mode = mode
        self.clear_charts()
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if is_dark else "#dbdbdb"
        text_color = "white" if is_dark else "black"
        map_cmap = 'OrRd' if is_dark else 'YlGnBu'
        border_color = '#333333' if is_dark else '#ffffff'

        if mode == "location":
            event_data = get_events_by_country()
            map_title = "Global Event Heatmap — by Location"
            legend_label = "Events at Location"
        else:
            event_data = get_events_by_actor_country()
            map_title = "Global Event Heatmap — by Actor Country"
            legend_label = "Events as Actor"

        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        try:
            world = gpd.read_file(url)
            world = world[['NAME', 'geometry']].rename(columns={'NAME': 'name'})
        except Exception:
            messagebox.showerror("Map Error", "Could not load map data. Check internet connection.")
            return

        df = pd.DataFrame(event_data, columns=['name', 'event_count'])
        name_corrections = {
            "USA":           "United States of America",
            "US":            "United States of America",
            "United States": "United States of America",
            "UK":            "United Kingdom",
            "Great Britain": "United Kingdom",
            "Russia":        "Russian Federation",
            "South Korea":   "Korea, Republic of",
            "North Korea":   "Dem. Rep. Korea",
            "DRC":           "Dem. Rep. Congo",
        }
        df['name'] = df['name'].replace(name_corrections)
        world = world.merge(df, how="left", left_on="name", right_on="name")

        fig, ax = plt.subplots(figsize=(10, 6), facecolor=bg_color)
        ax.set_facecolor(bg_color)
        world.plot(column='event_count', ax=ax, legend=True,
                   cmap=map_cmap,
                   edgecolor=border_color,
                   linewidth=0.5,
                   missing_kwds={'color': '#444444' if is_dark else '#eeeeee'},
                   legend_kwds={'label': legend_label,
                                'orientation': "horizontal",
                                'shrink': 0.6})
        ax.set_title(map_title, color=text_color, fontsize=15, pad=20)

        axes = fig.get_axes()
        if len(axes) > 1:
            cax = axes[1]
            cax.tick_params(colors=text_color)
            cax.xaxis.label.set_color(text_color)

        ax.axis('off')
        self.render_figure(fig)

    def render_figure(self, fig):
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        plt.close(fig)

    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.load_events_data()

    def treeview_sort_column(self, tv, col, reverse):
        l = [(tv.set(k, col), k) for k in tv.get_children('')]

        if col in ["ID", "Impact"]:
            try:
                l.sort(key=lambda t: float(t[0]), reverse=reverse)
            except ValueError:
                l.sort(reverse=reverse)
        elif col == "Date":
            l.sort(key=lambda t: "-".join(reversed(t[0].split("/"))), reverse=reverse)
        else:
            l.sort(reverse=reverse)

        for index, (_, k) in enumerate(l):
            tv.move(k, '', index)

        for c in tv["columns"]:
            tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))

        arrow = " ▼" if reverse else " ▲"
        tv.heading(col, text=col + arrow, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def show_deleted_events(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Admin: Deleted Events Archive",
                     font=("Roboto", 24, "bold")).pack(pady=10, anchor="w")

        # ── Search / filter bar ────────────────────────────────────────────
        search_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        search_bar.pack(fill="x", pady=5)

        self.del_search_entry = ctk.CTkEntry(
            search_bar, placeholder_text="Search by event name...", width=300
        )
        self.del_search_entry.pack(side="left", padx=5)
        self.del_search_entry.bind("<Return>", lambda e: self.run_deleted_search())

        ctk.CTkButton(search_bar, text="🔍 Search", width=80,
                      command=self.run_deleted_search).pack(side="left", padx=5)
        ctk.CTkButton(search_bar, text="🧹 Clear", width=80,
                      fg_color="#7f8c8d", hover_color="#95a5a6",
                      command=self.clear_deleted_search).pack(side="left", padx=5)

        ctk.CTkLabel(search_bar, text="Deleted by:").pack(side="left", padx=(15, 5))
        options = ["All"] + get_deleted_by_options()
        self.del_by_filter = ctk.CTkOptionMenu(search_bar, values=options, width=130)
        self.del_by_filter.pack(side="left", padx=5)
        self.del_by_filter.set("All")

        # ── Treeview ──────────────────────────────────────────────────────
        columns = ("Log ID", "Orig ID", "Event Name", "Start Date",
                   "End Date", "Ongoing", "Deleted At", "Deleted By")
        self.deleted_tree = ttk.Treeview(self.content, columns=columns, show="headings")

        for col in columns:
            self.deleted_tree.heading(
                col, text=col,
                command=lambda c=col: self.sort_treeview(self.deleted_tree, c, False)
            )
            self.deleted_tree.column(col, width=120, anchor="center")

        self.deleted_tree.pack(fill="both", expand=True, pady=10)

        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="Restore Selected Event",
                      command=self.restore_event,
                      fg_color="#27ae60", hover_color="#219150").pack(side="left", padx=10)

        self.load_deleted_events_data()

    def run_deleted_search(self):
        keyword   = self.del_search_entry.get().strip()
        del_by    = self.del_by_filter.get() if hasattr(self, "del_by_filter") else "All"
        rows      = fetch_deleted_events_filtered(keyword, del_by)
        self._populate_deleted_tree(rows)

    def clear_deleted_search(self):
        self.del_search_entry.delete(0, "end")
        self.del_by_filter.set("All")
        self.load_deleted_events_data()

    def load_deleted_events_data(self):
        from database import fetch_deleted_events
        self._populate_deleted_tree(fetch_deleted_events())

    def _populate_deleted_tree(self, rows):
        for item in self.deleted_tree.get_children():
            self.deleted_tree.delete(item)
        for ev in rows:
            ongoing_text = "Yes" if ev[5] == 1 else "No"
            self.deleted_tree.insert("", "end",
                values=(ev[0], ev[1], ev[2], ev[3], ev[4], ongoing_text, ev[6], ev[7]))

    def restore_event(self):
        selected = self.deleted_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select an event to restore.")
            return

        values = self.deleted_tree.item(selected[0])["values"]
        log_id      = int(values[0])   # Treeview values are strings; cast to int
        original_id = int(values[1])
        name = values[2]

        if messagebox.askyesno("Restore", f"Restore '{name}' to its original ID (#{original_id})?"):
            from database import restore_event_from_db

            if restore_event_from_db(log_id, original_id):
                messagebox.showinfo("Success", f"Event '{name}' restored to position #{original_id}.")
                self.load_deleted_events_data()
            else:
                messagebox.showerror("Error", "Could not restore to original ID. It might already be in use.")


    def show_activity_logs(self):
        """Admin-only view of the database-backed activity log with search and export."""
        self.clear_content()
        ctk.CTkLabel(self.content, text="📋 Activity Logs",
                     font=("Roboto", 24, "bold")).pack(pady=(0, 10), anchor="w")

        # ── Filter bar ────────────────────────────────────────────────────
        filter_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        filter_bar.pack(fill="x", pady=5)

        self.log_search_entry = ctk.CTkEntry(
            filter_bar, placeholder_text="Search actions or usernames...", width=320
        )
        self.log_search_entry.pack(side="left", padx=5)
        self.log_search_entry.bind("<Return>", lambda e: self.run_log_search())

        ctk.CTkButton(filter_bar, text="🔍 Search", width=80,
                      command=self.run_log_search).pack(side="left", padx=5)
        ctk.CTkButton(filter_bar, text="🧹 Clear", width=80,
                      fg_color="#7f8c8d", hover_color="#95a5a6",
                      command=self.clear_log_search).pack(side="left", padx=5)

        ctk.CTkLabel(filter_bar, text="User:").pack(side="left", padx=(15, 5))
        user_opts = ["All"] + get_all_log_usernames()
        self.log_user_filter = ctk.CTkOptionMenu(filter_bar, values=user_opts, width=130)
        self.log_user_filter.pack(side="left", padx=5)
        self.log_user_filter.set("All")

        ctk.CTkButton(filter_bar, text="📥 Export CSV", width=110,
                      fg_color="#34495e", hover_color="#2c3e50",
                      command=self.export_logs_csv).pack(side="right", padx=5)

        # ── Treeview ──────────────────────────────────────────────────────
        columns = ("ID", "Timestamp", "Username", "Action")
        self.log_tree = ttk.Treeview(self.content, columns=columns, show="headings")

        col_widths = {"ID": 50, "Timestamp": 160, "Username": 120, "Action": 500}
        for col in columns:
            self.log_tree.heading(
                col, text=col,
                command=lambda c=col: self.sort_treeview(self.log_tree, c, False)
            )
            self.log_tree.column(col, width=col_widths.get(col, 120), anchor="w")

        self.log_tree.pack(fill="both", expand=True, pady=10)
        self._load_logs()

    def _load_logs(self, keyword: str = "", user_filter: str = "All"):
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
        for row in get_logs_filtered(keyword, user_filter):
            self.log_tree.insert("", "end", values=row)

    def run_log_search(self):
        keyword = self.log_search_entry.get().strip()
        user    = self.log_user_filter.get() if hasattr(self, "log_user_filter") else "All"
        self._load_logs(keyword, user)

    def clear_log_search(self):
        self.log_search_entry.delete(0, "end")
        self.log_user_filter.set("All")
        self._load_logs()

    def export_logs_csv(self):
        try:
            keyword = self.log_search_entry.get().strip()
            user    = self.log_user_filter.get()
            rows    = get_logs_filtered(keyword, user)
            path    = os.path.join(os.getcwd(), "worldscope_logs_export.csv")
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Timestamp", "Username", "Action"])
                writer.writerows(rows)
            messagebox.showinfo("Exported", f"Logs exported to:\n{path}")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))


# --- POPUP CLASSES ---

class EventPopup(ctk.CTkToplevel):
    """
    Add / Edit event form.
    Location Countries — a multi-select listbox of countries where the event
    physically took place, stored in event_locations (3NF junction table).
    Actor Countries — nations involved/participating, stored in event_actors.
    Both are fully separate from the events table itself.
    """
    def __init__(self, parent, event_id=None):
        super().__init__(parent)
        self.parent = parent
        self.event_id = event_id
        self.title("Edit Event" if event_id else "Add New Event")
        self.geometry("560x920")   # Taller to accommodate the location panel
        self.attributes("-topmost", True)
        self.grid_columnconfigure(1, weight=1)

        self.entries = {}
        self.type_options = fetch_event_types()

        # --- Row 0: Event Name ---
        ctk.CTkLabel(self, text="Event Name (*)").grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        self.entries["name"] = ctk.CTkEntry(self, width=280)
        self.entries["name"].grid(row=0, column=1, padx=20, pady=(15, 5))

        # --- Row 1-2: Location Countries (multi-select, mirrors the Actors panel) ---
        ctk.CTkLabel(self, text="📍 Location Countries (*)",
                     font=("Roboto", 13, "bold")).grid(
            row=1, column=0, columnspan=2, padx=20, pady=(10, 0), sticky="w")
        ctk.CTkLabel(self,
                     text="Where the event physically took place (one or more countries)",
                     font=("Roboto", 10), text_color="gray").grid(
            row=2, column=0, columnspan=2, padx=20, sticky="w")

        loc_outer = ctk.CTkFrame(self, fg_color="transparent")
        loc_outer.grid(row=3, column=0, columnspan=2, padx=20, pady=(4, 8), sticky="ew")
        loc_outer.grid_columnconfigure(0, weight=1)

        lb_loc_frame = ctk.CTkFrame(loc_outer, fg_color=("#e8e8e8", "#3a3a3a"), corner_radius=8)
        lb_loc_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.location_listbox = tk.Listbox(
            lb_loc_frame, height=3, selectmode=tk.SINGLE,
            bg="#3a3a3a", fg="white", selectbackground="#3b8ed0",
            relief="flat", bd=0, highlightthickness=0,
            font=("Roboto", 11)
        )
        self.location_listbox.pack(fill="both", expand=True, padx=4, pady=4)

        loc_ctrl = ctk.CTkFrame(loc_outer, fg_color="transparent")
        loc_ctrl.grid(row=1, column=0, columnspan=2, sticky="ew")
        loc_ctrl.grid_columnconfigure(0, weight=1)

        self.location_cb = ctk.CTkComboBox(loc_ctrl, values=VALID_COUNTRIES, width=200)
        self.location_cb.grid(row=0, column=0, padx=(0, 5), sticky="w")
        self.location_cb.bind("<KeyRelease>", self.filter_location_countries)

        ctk.CTkButton(loc_ctrl, text="+ Add", width=70, fg_color="#2980b9",
                      hover_color="#2471a3", command=self.add_location).grid(row=0, column=1, padx=5)
        ctk.CTkButton(loc_ctrl, text="Remove", width=70, fg_color="#e74c3c",
                      hover_color="#c0392b", command=self.remove_location).grid(row=0, column=2)

        # --- Row 4: Event Category ---
        ctk.CTkLabel(self, text="Event Category (*)").grid(row=4, column=0, padx=20, pady=5, sticky="w")
        self.type_var = ctk.StringVar(value="Other")
        self.type_menu = ctk.CTkOptionMenu(
            self, variable=self.type_var,
            values=[t[1] for t in self.type_options], width=280
        )
        self.type_menu.grid(row=4, column=1, padx=20, pady=5)

        # --- Row 5: Start Date ---
        ctk.CTkLabel(self, text="Start Date (*)\n(DD/MM/YYYY)").grid(row=5, column=0, padx=20, pady=5, sticky="w")
        self.entries["start_date"] = ctk.CTkEntry(self, width=280)
        self.entries["start_date"].grid(row=5, column=1, padx=20, pady=5)
        self.entries["start_date"].bind("<KeyRelease>", lambda e: self.apply_date_mask(self.entries["start_date"], e))

        # --- Row 6: Ongoing Checkbox ---
        self.ongoing_var = ctk.BooleanVar(value=False)
        self.ongoing_check = ctk.CTkCheckBox(
            self, text="This event is still ongoing",
            variable=self.ongoing_var, command=self.toggle_ongoing
        )
        self.ongoing_check.grid(row=6, column=1, padx=20, pady=5, sticky="w")

        # --- Row 7: End Date ---
        ctk.CTkLabel(self, text="End Date\n(DD/MM/YYYY)").grid(row=7, column=0, padx=20, pady=5, sticky="w")
        self.entries["end_date"] = ctk.CTkEntry(self, width=280)
        self.entries["end_date"].grid(row=7, column=1, padx=20, pady=5)
        self.entries["end_date"].bind("<KeyRelease>", lambda e: self.apply_date_mask(self.entries["end_date"], e))

        # --- Row 8: Impact ---
        ctk.CTkLabel(self, text="Impact Level (*)").grid(row=8, column=0, padx=20, pady=5, sticky="w")
        self.impact_var = ctk.StringVar(value="Medium")
        self.impact_menu = ctk.CTkOptionMenu(
            self, variable=self.impact_var,
            values=["High", "Medium", "Low"], width=280
        )
        self.impact_menu.grid(row=8, column=1, padx=20, pady=5)

        # --- Row 9: Description ---
        ctk.CTkLabel(self, text="Description").grid(row=9, column=0, padx=20, pady=5, sticky="w")
        self.entries["desc"] = ctk.CTkEntry(self, width=280)
        self.entries["desc"].grid(row=9, column=1, padx=20, pady=5)

        # --- Row 10: Source URL ---
        ctk.CTkLabel(self, text="Source URL").grid(row=10, column=0, padx=20, pady=5, sticky="w")
        self.entries["src"] = ctk.CTkEntry(self, width=280)
        self.entries["src"].grid(row=10, column=1, padx=20, pady=5)

        # --- Row 11-13: Actor Countries ---
        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=11, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 0))

        ctk.CTkLabel(self, text="🌐 Actor Countries", font=("Roboto", 13, "bold")).grid(
            row=12, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")
        ctk.CTkLabel(self,
                     text="Nations involved in this event (can differ from Location)",
                     font=("Roboto", 10), text_color="gray").grid(
            row=13, column=0, columnspan=2, padx=20, sticky="w")

        # Actor listbox (left) + controls (right)
        actor_outer = ctk.CTkFrame(self, fg_color="transparent")
        actor_outer.grid(row=14, column=0, columnspan=2, padx=20, pady=5, sticky="ew")
        actor_outer.grid_columnconfigure(0, weight=1)

        # Listbox to display currently added actors
        lb_frame = ctk.CTkFrame(actor_outer, fg_color=("#e8e8e8", "#3a3a3a"), corner_radius=8)
        lb_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 5))

        self.actor_listbox = tk.Listbox(
            lb_frame, height=4, selectmode=tk.SINGLE,
            bg="#3a3a3a", fg="white", selectbackground="#3b8ed0",
            relief="flat", bd=0, highlightthickness=0,
            font=("Roboto", 11)
        )
        self.actor_listbox.pack(fill="both", expand=True, padx=4, pady=4)

        # Add / Remove controls
        ctrl_frame = ctk.CTkFrame(actor_outer, fg_color="transparent")
        ctrl_frame.grid(row=1, column=0, columnspan=2, sticky="ew")
        ctrl_frame.grid_columnconfigure(0, weight=1)

        self.actor_cb = ctk.CTkComboBox(ctrl_frame, values=VALID_COUNTRIES, width=200)
        self.actor_cb.grid(row=0, column=0, padx=(0, 5), sticky="w")

        ctk.CTkButton(ctrl_frame, text="+ Add", width=70, fg_color="#27ae60",
                      hover_color="#219150", command=self.add_actor).grid(row=0, column=1, padx=5)
        ctk.CTkButton(ctrl_frame, text="Remove", width=70, fg_color="#e74c3c",
                      hover_color="#c0392b", command=self.remove_actor).grid(row=0, column=2)

        # --- Row 15: Save Button ---
        ctk.CTkButton(self, text="💾 Save Event", command=self.save,
                      fg_color="#2ecc71", hover_color="#27ae60", height=40)\
            .grid(row=15, column=0, columnspan=2, pady=20)

        if self.event_id:
            self.load_data()

    # --- Location Country Helpers ---

    def add_location(self):
        country = self.location_cb.get().strip()
        if not country or country not in VALID_COUNTRIES:
            messagebox.showwarning("Invalid", "Please select a valid country from the list.")
            return
        existing = list(self.location_listbox.get(0, tk.END))
        if country in existing:
            messagebox.showwarning("Duplicate", f"{country} is already listed as a location.")
            return
        self.location_listbox.insert(tk.END, country)

    def remove_location(self):
        selected = self.location_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection", "Please click on a country in the list to select it first.")
            return
        self.location_listbox.delete(selected[0])

    def filter_location_countries(self, event):
        typed = self.location_cb.get().lower()
        filtered = [c for c in VALID_COUNTRIES if typed in c.lower()]
        self.location_cb.configure(values=filtered if filtered else VALID_COUNTRIES)

    # --- Actor Country Helpers ---

    def add_actor(self):
        country = self.actor_cb.get().strip()
        if not country or country not in VALID_COUNTRIES:
            messagebox.showwarning("Invalid", "Please select a valid country from the list.")
            return
        existing = list(self.actor_listbox.get(0, tk.END))
        if country in existing:
            messagebox.showwarning("Duplicate", f"{country} is already listed as an actor.")
            return
        self.actor_listbox.insert(tk.END, country)

    def remove_actor(self):
        selected = self.actor_listbox.curselection()
        if not selected:
            messagebox.showwarning("Selection", "Please click on a country in the list to select it first.")
            return
        self.actor_listbox.delete(selected[0])

    # --- Logic Methods ---

    def toggle_ongoing(self):
        if self.ongoing_var.get():
            self.entries["end_date"].delete(0, "end")
            self.entries["end_date"].configure(state="disabled", fg_color="#d3d3d3")
        else:
            self.entries["end_date"].configure(state="normal", fg_color=["#F9F9FA", "#343638"])

    def get_selected_type_id(self):
        selected_name = self.type_var.get()
        for t_id, t_name in self.type_options:
            if t_name == selected_name:
                return t_id
        return None

    def load_data(self):
        """Loads existing event data into the form for editing."""
        if self.event_id is None:
            return
        eid = int(self.event_id)
        event = fetch_event_by_id(eid)
        if event:
            # event tuple: (name, type_id, start_date, end_date, is_ongoing, impact, description, source)
            self.entries["name"].insert(0, event[0])
            type_name = next((name for id, name in self.type_options if id == event[1]), None)
            if type_name:
                self.type_var.set(type_name)
            self.entries["start_date"].insert(0, event[2])
            if event[4]:  # is_ongoing
                self.ongoing_var.set(True)
                self.toggle_ongoing()
            else:
                self.entries["end_date"].insert(0, event[3])
            self.impact_var.set(event[5])
            self.entries["desc"].insert(0, event[6] or "")
            self.entries["src"].insert(0, event[7] or "")

            # Load location countries from event_locations (3NF source)
            for loc in fetch_event_locations(eid):
                self.location_listbox.insert(tk.END, loc)

            # Load actor countries from event_actors
            for actor in fetch_event_actors(eid):
                self.actor_listbox.insert(tk.END, actor)

    def validate_real_date(self, value: str):
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return None

    def apply_date_mask(self, entry, event):
        if event.keysym == "BackSpace":
            return
        text = ''.join(filter(str.isdigit, entry.get()))
        formatted = ""
        for i, char in enumerate(text):
            if i in (2, 4):
                formatted += "/"
            formatted += char
        entry.delete(0, "end")
        entry.insert(0, formatted[:10])

    def save(self):
        data = {
            "name":    self.entries["name"].get().strip(),
            "type_id": self.get_selected_type_id(),
            "start":   self.entries["start_date"].get().strip(),
            "end":     self.entries["end_date"].get().strip(),
            "ongoing": 1 if self.ongoing_var.get() else 0,
            "impact":  self.impact_var.get(),
            "desc":    self.entries["desc"].get().strip(),
            "src":     self.entries["src"].get().strip()
        }

        # Collect location and actor countries from their listboxes
        location_countries = list(self.location_listbox.get(0, tk.END))
        actor_countries    = list(self.actor_listbox.get(0, tk.END))

        errors = []

        if not data["name"]:
            errors.append("• Event name is required.")
        elif event_name_exists(data["name"], exclude_id=self.event_id):
            errors.append(f"• An event named '{data['name']}' already exists. Please use a unique name.")

        if not location_countries:
            errors.append("• At least one location country is required.")

        start_obj = self.validate_real_date(data["start"])
        if not start_obj:
            errors.append("• Start date must be a valid date (DD/MM/YYYY).")

        if not self.ongoing_var.get():
            end_obj = self.validate_real_date(data["end"])
            if not end_obj:
                errors.append("• End date is required (or mark as ongoing).")
            elif start_obj and end_obj < start_obj:
                errors.append("• End date cannot be earlier than the start date.")
        else:
            data["end"] = "Ongoing"

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        # 8-field payload — no country column on events table
        payload = (
            data["name"], data["type_id"],
            data["start"], data["end"], data["ongoing"],
            data["impact"], data["desc"], data["src"]
        )

        try:
            if self.event_id:
                update_event(self.event_id, payload)
                set_event_locations(self.event_id, location_countries)
                set_event_actors(self.event_id, actor_countries)
            else:
                new_id = insert_event(payload)
                if new_id:
                    set_event_locations(new_id, location_countries)
                    set_event_actors(new_id, actor_countries)

            self.parent.load_events_view()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Database Error", f"Could not save event: {e}")


class UserPopup(ctk.CTkToplevel):
    def __init__(self, parent, user_id=None):
        super().__init__(parent)
        self.parent = parent
        self.user_id = user_id
        self.title("User Details" if not user_id else "Edit User")
        self.geometry("400x550")
        self.attributes("-topmost", True)
        self.grid_columnconfigure(0, weight=1)

        fields = [("Username", "u"), ("First Name", "fn"), ("Last Name", "ln"), ("Password", "p")]
        self.entries = {}

        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(self, text=label).grid(row=i * 2, column=0, pady=(10, 0), padx=30, sticky="w")
            p_text = "Enter new password to reset" if user_id and key == "p" else ""
            show_char = "*" if key == "p" else ""

            entry = ctk.CTkEntry(self, width=300, placeholder_text=p_text, show=show_char)
            entry.grid(row=i * 2 + 1, column=0, padx=30, pady=5)
            self.entries[key] = entry

        ctk.CTkLabel(self, text="Role").grid(row=8, column=0, pady=(10, 0), padx=30, sticky="w")
        self.role_var = ctk.StringVar(value="viewer")
        ctk.CTkOptionMenu(self, variable=self.role_var, values=["viewer", "analyst", "admin"],
                          width=300).grid(row=9, column=0, padx=30, pady=5)

        if user_id:
            self.load_user_data()

        ctk.CTkButton(self, text="Save User", command=self.user_save, height=40).grid(row=10, column=0, pady=30)

        # BUG FIX: protocol set for all modes (not just new user inside user_save)
        self.protocol("WM_DELETE_WINDOW", self.close_popup)

    def load_user_data(self):
        all_u = fetch_users()
        user_data = next((u for u in all_u if u[0] == self.user_id), None)
        if user_data:
            self.entries["u"].insert(0, user_data[1])
            self.role_var.set(user_data[2])
            self.entries["fn"].insert(0, user_data[3])
            self.entries["ln"].insert(0, user_data[4])

    def user_save(self):
        u, fn, ln, p = (self.entries["u"].get(), self.entries["fn"].get(),
                        self.entries["ln"].get(), self.entries["p"].get())
        role = self.role_var.get()

        if not all([u, fn, ln]) or (not self.user_id and not p):
            messagebox.showerror("Error", "All fields except password (for edits) are required.")
            return

        if self.user_id:
            if update_user(self.user_id, u, role, fn, ln):
                if p.strip():
                    admin_reset_password(self.user_id, p)
                messagebox.showinfo("Success", "User database updated.")
                self.parent.refresh_user_list()
                self.destroy()
            else:
                messagebox.showerror("Error", "Username likely taken.")
        else:
            if user_exists(u):
                messagebox.showerror("Error", "Username already exists.")
                return
            create_user(u, p, role, fn, ln)
            messagebox.showinfo("Success", "User created.")
            self.parent.refresh_user_list()
            self.destroy()

    def close_popup(self):
        self.grab_release()
        self.parent.refresh_user_list()
        self.destroy()