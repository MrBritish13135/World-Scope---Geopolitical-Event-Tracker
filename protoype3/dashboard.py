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
    user_exists, fetch_event_types, get_events_by_country, get_events_by_type, 
    get_events_by_impact, backup_database,
)
import re
# Country List for dropdown - ideally this should be dynamic based on the map data or a reliable source
from countries  import VALID_COUNTRIES
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

        for text, cmd in menu_items:
            btn = ctk.CTkButton(self.sidebar, text=text, font=("Roboto", 13),
                                fg_color="transparent", text_color=("gray10", "gray90"),
                                hover_color=("#dbdbdb", "#2b2b2b"), anchor="w", command=cmd)
            btn.pack(fill="x", padx=15, pady=5)

        # Switch User 
        self.switch_button = ctk.CTkButton(self.sidebar, text="🔄 Switch User", fg_color="#8e44ad", border_width=1,command=self.switch_user
                                            , hover_color="#732d91")
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
        # """Container for the statistics submenu and charts."""
        self.clear_content()
        
        # Header & Submenu Bar
        header_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header_frame, text="Global Event Data Dashboard", font=("Roboto", 28, "bold")).pack(side="left")
        
        # Submenu Buttons
        nav_bar = ctk.CTkFrame(self.content, height=40)
        nav_bar.pack(fill="x", pady=(0, 10))
        
        ctk.CTkButton(nav_bar, text="Types of Events Compared", width=100, command=self.draw_type_chart).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(nav_bar, text="Impact Levels", width=100, command=self.draw_impact_chart).pack(side="left", padx=5, pady=5)
        ctk.CTkButton(nav_bar, text="Global Event Heat Map", width=100, command=self.draw_world_map).pack(side="left", padx=5, pady=5)

        # 2. Chart Container (This is where the charts will be rendered)
        self.chart_container = ctk.CTkFrame(self.content, fg_color="#2b2b2b", corner_radius=15)
        self.chart_container.pack(fill="both", expand=True)
        
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
        for widget in self.chart_container.winfo_children():    
                widget.destroy()
        self.clear_charts()
        data = get_events_by_type()
        if not data: return
        
        types, counts = zip(*data)
        fig, ax = plt.subplots(figsize=(7, 5), facecolor='#2b2b2b')
        ax.bar(types, counts, color='#3b8ed0')
        ax.set_title("Events by Category", color='white', pad=15)
        ax.tick_params(colors='white')
        ax.set_facecolor('#2b2b2b')
        
        self.render_figure(fig)
    def draw_type_chart(self):
        self.current_chart_type = "type"
        self.clear_charts()
        data = get_events_by_type()
        if not data: return
        
        colors = self.get_theme_colors()
        types, counts = zip(*data)
        
        # Use the dynamic colors for facecolor and text
        fig, ax = plt.subplots(figsize=(7, 5), facecolor=colors["bg"])
        ax.set_facecolor(colors["bg"])
        
        ax.bar(types, counts, color='#3b8ed0')
        ax.set_title("Events by Category", color=colors["text"], pad=15)
        ax.tick_params(colors=colors["text"])
        
        # Spines (borders) color
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

        autotexts = ax.pie(
            counts, 
            labels=impacts, 
            autopct='%1.1f%%', 
            startangle=140,
            textprops={'color': colors["text"], 'fontsize': 10},
            colors=chart_colours,
            pctdistance=0.85
        )[2]
        
        for autotext in autotexts:
            autotext.set_weight('bold')

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
            
            # Backup Button
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
                            self.draw_world_map()
            except (tk.TclError, AttributeError):
                pass



    def change_password_action(self):  
        from database import verify_user_password, update_own_password

        old = self.old_pwd.get().strip()
        new = self.new_pwd.get().strip()
        # Basic validation
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
    # Use database function to perform the backup
     success, message = backup_database() 
     if success:
        from database import log_activity # Ensure this is imported
        log_activity(self.user['username'], f"Database Backup Created: {message}")
        
        confirm = messagebox.askyesno("Success", 
            f"Backup created successfully!\n\nWould you like to open the backups folder?")
        
        if confirm:
            # Get the absolute path to the backups folder
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
            
            # DEFENSIVE CHECK: Create the folder if it somehow disappeared
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            
            # Open the folder in Windows Explorer
            os.startfile(backup_path) 
     else:
        messagebox.showerror("Backup Failed", f"Error: {message}")



    # --- EVENTS VIEW ---

    def load_events_view(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Global Event Logs", font=("Roboto", 24, "bold")).pack(pady=(0,10), anchor="w")
        
        # Search Bar
        search_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        search_bar.pack(fill="x", pady=5)

        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text="Search by name, country, or description...", width=400)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.run_search())

        ctk.CTkButton(search_bar, text="🔍 Search", width=80, command=self.run_search).pack(side="left", padx=5)

        ctk.CTkButton(search_bar, text="🧹 Clear", width=80, fg_color="#7f8c8d", hover_color="#95a5a6",command=self.clear_search).pack(side="left", padx=5)

        ctk.CTkButton(search_bar, text="📥 Export CSV", width=100, fg_color="#34495e", hover_color="#2c3e50", command=self.export_to_csv).pack(side="right", padx=5) 

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
        columns = ("ID", "Name", "Country", "Type", "Start Date", "End Date", "Impact")
        self.tree = ttk.Treeview(self.content, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col,command=lambda c=col: self.treeview_sort_column(self.tree, c, False))
        
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

        for event in results:
            self.tree.insert("", "end", values=event)



    def load_events_data(self):
        for row in self.tree.get_children(): self.tree.delete(row)
        for event in fetch_events(): self.tree.insert("", "end", values=event)

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
        event_id = event_data[0]
        event_name = event_data[1]
        current_admin = self.user.get("username", "Unknown")
        if messagebox.askyesno("Confirm", f"Permanently delete event: {event_name}?\nThis action will be logged."):
            success = delete_event_from_db(event_id, event_name, self.user["username"])
            if success:
                messagebox.showinfo("Success", "Event archived.")
                self.load_events_data()
            else:
                messagebox.showerror("Error", "Could not delete. Check console for 'Locked' errors.")

    def export_to_csv(self):
        try:
            filename = "worldscope_export.csv"
            file_path = os.path.join(os.getcwd(), filename)
            events = fetch_events()

            with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                 writer = csv.writer(file)
                 writer.writerow(["ID", "Name", "Country", "Type", "Date", "Impact"])
                 writer.writerows(events)

            messagebox.showinfo("Exported", f"Events exported to {file_path}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"An error occurred: {e}")


    # --- USER MANAGEMENT ---

    def show_users(self):
        for widget in self.content.winfo_children():
            widget.destroy()

        ctk.CTkLabel(self.content, text="User Management", font=("Roboto", 24, "bold")).pack(pady=10, anchor="w")
        
        # Action bars
        action_bar = ctk.CTkFrame(self.content, fg_color="transparent")
        action_bar.pack(fill="x", pady=5)

        ctk.CTkButton(action_bar, text="➕ Add User", width=120,
                      command=self.add_user_popup).pack(side="left", padx=5)
        
        ctk.CTkButton(action_bar, text="📝 Edit User", fg_color="#f39c12", hover_color="#d35400", width=120,
                      command=lambda: self.edit_user_popup()).pack(side="left", padx=5)

        ctk.CTkButton(action_bar, text="🗑️ Delete User", fg_color="#e74c3c", hover_color="#c0392b", width=120,
                      command=self.delete_user_action).pack(side="left", padx=5)

        # Treeview setup
        columns = ("ID", "User", "Role", "First Name", "Last Name", "Login Date", "Login Time")
        self.user_tree = ttk.Treeview(self.content, columns=columns, show="headings")


        for col in columns:
            self.user_tree.heading(col, text=col, 
                                   command=lambda c=col: self.sort_treeview(c, False))
            
            
            if col == "ID":
                self.user_tree.column(col, anchor="center", width=50)
            elif "Login" in col:
                self.user_tree.column(col, anchor="center", width=150) # Give more room for date/time
            else:
                self.user_tree.column(col, anchor="center", width=120)

        self.user_tree.pack(fill="both", expand=True, pady=10)
        self.refresh_user_list()

    def sort_treeview(self, tree, col, reverse):

        data = [(tree.set(k, col), k) for k in tree.get_children('')]
    
    # 2. Sort: try numeric first (for IDs), then string
        try:
            data.sort(key=lambda t: float(t[0]) if t[0] else 0, reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0].lower(), reverse=reverse)

    # 3. Rearrange the rows
        for index, (_, k) in enumerate(data):
            tree.move(k, '', index)

        all_cols = tree["columns"]
        for c in all_cols:
           if c == col:
            arrow = " ▼" if reverse else " ▲"
            tree.heading(c, text=c + arrow, 
                         command=lambda _c=c: self.sort_treeview(tree, _c, not reverse))
        else:
            # Remove arrows from other columns
            tree.heading(c, text=c, 
                         command=lambda _c=c: self.sort_treeview(tree, _c, False))

    def refresh_user_list(self):

        for item in self.user_tree.get_children():
            self.user_tree.delete(item)


        from database import fetch_users
        users = fetch_users() # This should return cur.fetchall()
        
        # 
        for u in users:

            # u[0]: ID, u[1]: Username, u[2]: Role, u[3]: First, u[4]: Last, u[5]: Date, u[6]: Time
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
        if not selected: return
        u_data = self.user_tree.item(selected[0])["values"]
        if u_data[1] == self.user["username"]:
            messagebox.showerror("Error", "You cannot delete your own account.")
            return
        if messagebox.askyesno("Confirm", f"Remove user {u_data[1]}?"):
            delete_user(u_data[0])
            self.refresh_user_list()

    def switch_user(self):
        if messagebox.askyesno("Switch User", "Are you sure you want to switch users? Unsaved changes will be lost."):
            self.on_logout(should_restart=True)


    def logout(self):
        response = messagebox.askyesno("Logout", "Are you sure you want to log out?")
        if response:
            self.on_logout(should_restart=False)

    def draw_world_map(self):
        self.current_chart_type = "map"
        self.clear_charts()
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2b2b2b" if is_dark else "#dbdbdb"
        text_color = "white" if is_dark else "black"    

        map_cmap = 'OrRd' if is_dark else 'YlGnBu'
        border_color = '#333333' if is_dark else '#ffffff'

        



        event_data = get_events_by_country()
        url = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"
        try:
            world = gpd.read_file(url)
            world = world[['NAME', 'geometry']].rename(columns={'NAME': 'name'})
        except Exception as e:
            messagebox.showerror("Map Error", "Could not load map data. Check internet connection.")
            return
        df = pd.DataFrame(event_data, columns=['name', 'event_count'])
   
        name_corrections = {
        "USA": "United States of America",
            "US": "United States of America",
            "United States": "United States of America",
            "UK": "United Kingdom",
            "Great Britain": "United Kingdom",
            "Russia": "Russian Federation",
            "South Korea": "Korea, Republic of",
            "North Korea": "Dem. Rep. Korea",
            "DRC": "Dem. Rep. Congo"
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
                   legend_kwds={'label': "Number of Events", 
                                'orientation': "horizontal", 
                                'shrink': 0.6})
        ax.set_title("Global Event Heatmap", color=text_color, fontsize=16, pad=20)

        cax = fig.get_axes()[1]
        cax.tick_params(colors=text_color)
        cax.xaxis.label.set_color(text_color)

        ax.axis('off')
        self.render_figure(fig)


    def render_figure(self, fig):
        """Helper to draw the matplotlib figure onto the CustomTkinter frame"""
        canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=20)
        plt.close(fig) # Memory management

    # clear search results and reload all data
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
            # Sort by date: convert dd/mm/yyyy to yyyy-mm-dd for string comparison
            l.sort(key=lambda t: "-".join(reversed(t[0].split("/"))), reverse=reverse)
        else:
            # Standard string sort for Name, Type, etc.
            l.sort(reverse=reverse)

        for index, (_, k) in enumerate(l):
            tv.move(k, '', index)

        # Reset all headings to plain text
        for c in tv["columns"]:
            tv.heading(c, text=c, command=lambda _c=c: self.treeview_sort_column(tv, _c, False))
        
        # Add arrow to active column
        arrow = " ▼" if reverse else " ▲"
        tv.heading(col, text=col + arrow, command=lambda: self.treeview_sort_column(tv, col, not reverse))

    def show_deleted_events(self):
        self.clear_content()
        ctk.CTkLabel(self.content, text="Admin: Deleted Events Archive", font=("Roboto", 24, "bold")).pack(pady=10)

        # Treeview setup for deleted events
        columns = ("Log ID", "Orig ID", "Event Name", "Start Date", "End Date", "Ongoing", "Deleted At", "Deleted By")
        self.deleted_tree = ttk.Treeview(self.content, columns=columns, show="headings")
        
        # Adding sorting functionality to headers
        for col in columns:
            self.deleted_tree.heading(col, text=col,command=lambda c=col: self.sort_treeview(self.deleted_tree, c, False))
            self.deleted_tree.column(col, width=120, anchor="center")
            
        self.deleted_tree.pack(fill="both", expand=True, pady=10)

        # Restore button
        btn_frame = ctk.CTkFrame(self.content, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        ctk.CTkButton(btn_frame, text="Restore Selected Event", 
                      command=self.restore_event, 
                      fg_color="#27ae60", hover_color="#219150").pack(side="left", padx=10)

        self.load_deleted_events_data()

    def load_deleted_events_data(self):
        for item in self.deleted_tree.get_children():
            self.deleted_tree.delete(item)

        from database import fetch_deleted_events
        # Call the function and store result in a uniquely named variable
        fetched_rows = fetch_deleted_events()

        for ev in fetched_rows:
            ongoing_text = "Yes" if ev[5] == 1 else "No"
            # Ensure indices match the SELECT order in database.py
            display_row = (ev[0], ev[1], ev[2], ev[3], ev[4], ongoing_text, ev[6], ev[7])
            self.deleted_tree.insert("", "end", values=display_row)
    def restore_event(self):
        selected = self.deleted_tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select an event to restore.")
            return

        values = self.deleted_tree.item(selected[0])["values"]
        log_id = values[0]       
        original_id = values[1] 
        name = values[2]         # Event Name

        if messagebox.askyesno("Restore", f"Restore '{name}' to its original ID (#{original_id})?"):
            from database import restore_event_from_db
            
            # Pass BOTH IDs to the function
            if restore_event_from_db(log_id, original_id):
                messagebox.showinfo("Success", f"Event '{name}' restored to position #{original_id}.")
                self.load_deleted_events_data()
            else:
                messagebox.showerror("Error", "Could not restore to original ID. It might already be in use.")
        
# --- POPUP CLASSES ---

class EventPopup(ctk.CTkToplevel):
    def __init__(self, parent, event_id=None):
        super().__init__(parent)
        self.parent = parent
        self.event_id = event_id
        self.title("Edit Event" if event_id else "Add New Event")
        self.geometry("500x650")
        self.attributes("-topmost", True)
        self.grid_columnconfigure(1, weight=1)

        self.entries = {}
        self.type_options = fetch_event_types() # Assuming this returns [(id, name), ...]

        # --- UI Fields ---
        
        # Event Name
        ctk.CTkLabel(self, text="Event Name (*)").grid(row=0, column=0, padx=20, pady=(15, 5), sticky="w")
        self.entries["name"] = ctk.CTkEntry(self, width=250)
        self.entries["name"].grid(row=0, column=1, padx=20, pady=(15, 5))

        # Country
        ctk.CTkLabel(self, text="Country (*)").grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.country_cb = ctk.CTkComboBox(self, values=VALID_COUNTRIES, width=250)
        self.country_cb.grid(row=1, column=1, padx=20, pady=5)
        self.country_cb.bind("<KeyRelease>", self.filter_countries)

        # Category
        ctk.CTkLabel(self, text="Event Category (*)").grid(row=2, column=0, padx=20, pady=5, sticky="w")
        self.type_var = ctk.StringVar(value="Other")
        self.type_menu = ctk.CTkOptionMenu(
            self,
            variable=self.type_var,
            values=[t[1] for t in self.type_options],
            width=250
        )
        self.type_menu.grid(row=2, column=1, padx=20, pady=5)

        # Start Date
        ctk.CTkLabel(self, text="Start Date (*) (DD/MM/YYYY)").grid(row=3, column=0, padx=20, pady=5, sticky="w")
        self.entries["start_date"] = ctk.CTkEntry(self, width=250)
        self.entries["start_date"].grid(row=3, column=1, padx=20, pady=5)
        self.entries["start_date"].bind("<KeyRelease>", lambda e: self.apply_date_mask(self.entries["start_date"], e))

        # Ongoing Checkbox
        self.ongoing_var = ctk.BooleanVar(value=False)
        self.ongoing_check = ctk.CTkCheckBox(
            self,
            text="This event is still ongoing",
            variable=self.ongoing_var,
            command=self.toggle_ongoing
        )
        self.ongoing_check.grid(row=4, column=1, padx=20, pady=5, sticky="w")

        # End Date
        ctk.CTkLabel(self, text="End Date (DD/MM/YYYY)").grid(row=5, column=0, padx=20, pady=5, sticky="w")
        self.entries["end_date"] = ctk.CTkEntry(self, width=250)
        self.entries["end_date"].grid(row=5, column=1, padx=20, pady=5)
        self.entries["end_date"].bind("<KeyRelease>", lambda e: self.apply_date_mask(self.entries["end_date"], e))

        # Impact
        ctk.CTkLabel(self, text="Impact Level (*)").grid(row=6, column=0, padx=20, pady=5, sticky="w")
        self.impact_var = ctk.StringVar(value="Medium")
        self.impact_menu = ctk.CTkOptionMenu(
            self,
            variable=self.impact_var,
            values=["High", "Medium", "Low"],
            width=250
        )
        self.impact_menu.grid(row=6, column=1, padx=20, pady=5)

        # Description & Source
        ctk.CTkLabel(self, text="Description").grid(row=7, column=0, padx=20, pady=5, sticky="w")
        self.entries["desc"] = ctk.CTkEntry(self, width=250)
        self.entries["desc"].grid(row=7, column=1, padx=20, pady=5)

        ctk.CTkLabel(self, text="Source URL").grid(row=8, column=0, padx=20, pady=5, sticky="w")
        self.entries["src"] = ctk.CTkEntry(self, width=250)
        self.entries["src"].grid(row=8, column=1, padx=20, pady=5)

        # Save Button
        ctk.CTkButton(self, text="Save Event", command=self.save, fg_color="#2ecc71", hover_color="#27ae60")\
            .grid(row=9, column=0, columnspan=2, pady=30)

        if self.event_id:
            self.load_data()

    # --- Logic Methods ---

    def toggle_ongoing(self):
        """Disables and clears end date if event is ongoing."""
        if self.ongoing_var.get():
            self.entries["end_date"].delete(0, "end")
            self.entries["end_date"].configure(state="disabled", fg_color="#d3d3d3")
        else:
            self.entries["end_date"].configure(state="normal", fg_color=["#F9F9FA", "#343638"])

    def get_selected_type_id(self):
        """Maps selected category name back to its ID."""
        selected_name = self.type_var.get()
        for t_id, t_name in self.type_options:
            if t_name == selected_name:
                return t_id
        return None

    def validate_real_date(self, value: str):
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return None

    def filter_countries(self, event):
        typed = self.country_cb.get().lower()
        filtered = [c for c in VALID_COUNTRIES if typed in c.lower()]
        if filtered:
            self.country_cb.configure(values=filtered)
        else:
            self.country_cb.configure(values=VALID_COUNTRIES)

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
            "name": self.entries["name"].get().strip(),
            "country": self.country_cb.get(),
            "type_id": self.get_selected_type_id(),
            "start": self.entries["start_date"].get().strip(),
            "end": self.entries["end_date"].get().strip(),
            "ongoing": 1 if self.ongoing_var.get() else 0,
            "impact": self.impact_var.get(),
            "desc": self.entries["desc"].get().strip(),
            "src": self.entries["src"].get().strip()
        }

        errors = []

        # Required Fields
        if not data["name"]:
            errors.append("• Event name is required.")
        if data["country"] not in VALID_COUNTRIES:
            errors.append("• Please select a valid country from the list.")
        
        # Date Logic
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
            data["end"] = "Ongoing" # Placeholder for database if needed

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        payload = (
            data["name"], data["country"], data["type_id"],
            data["start"], data["end"], data["ongoing"],
            data["impact"], data["desc"], data["src"]
        )

        try:
            if self.event_id:
                update_event(self.event_id, payload)
            else:
                insert_event(payload)
            
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

        # Fields
        fields = [("Username", "u"), ("First Name", "fn"), ("Last Name", "ln"), ("Password", "p")]
        self.entries = {}

        for i, (label, key) in enumerate(fields):
            ctk.CTkLabel(self, text=label).grid(row=i*2, column=0, pady=(10, 0), padx=30, sticky="w")
            p_text = "Enter new password to reset" if user_id and key == "p" else ""
            show_char = "*" if key == "p" else ""
            
            entry = ctk.CTkEntry(self, width=300, placeholder_text=p_text, show=show_char)
            entry.grid(row=i*2+1, column=0, padx=30, pady=5)
            self.entries[key] = entry

        # Role Dropdown
        ctk.CTkLabel(self, text="Role").grid(row=8, column=0, pady=(10, 0), padx=30, sticky="w")
        self.role_var = ctk.StringVar(value="viewer")
        ctk.CTkOptionMenu(self, variable=self.role_var, values=["viewer", "analyst", "admin"], width=300).grid(row=9, column=0, padx=30, pady=5)

        if user_id: self.load_user_data()

        ctk.CTkButton(self, text="Save User", command=self.user_save, height=40).grid(row=10, column=0, pady=30)

    def load_user_data(self):
        all_u = fetch_users()
        # Search for user in the list by ID (index 0)
        user_data = next((u for u in all_u if u[0] == self.user_id), None)
        if user_data:
            self.entries["u"].insert(0, user_data[1])
            self.role_var.set(user_data[2])
            self.entries["fn"].insert(0, user_data[3])
            self.entries["ln"].insert(0, user_data[4])

    def user_save(self):
        u, fn, ln, p = self.entries["u"].get(), self.entries["fn"].get(), self.entries["ln"].get(), self.entries["p"].get()
        role = self.role_var.get()

        if not all([u, fn, ln]) or (not self.user_id and not p):
            messagebox.showerror("Error", "All fields except password (for edits) are required.")
            return

        if self.user_id:
            # Update user info
            if update_user(self.user_id, u, role, fn, ln):
                # If a password was typed, reset it
                if p.strip():
                    admin_reset_password(self.user_id, p)
                messagebox.showinfo("Success", "User database updated.")
                self.parent.refresh_user_list()
                self.destroy()
            else:
                messagebox.showerror("Error", "Username likely taken.")
        else:
            # Create new user
            if user_exists(u):
                messagebox.showerror("Error", "Username already exists.")
                return
            create_user(u, p, role, fn, ln)
            messagebox.showinfo("Success", "User created.")

            self.protocol("WM_DELETE_WINDOW", self.close_popup)
    def close_popup(self):
        self.grab_release() # Releases focus
        self.parent.refresh_user_list()

        self.destroy()