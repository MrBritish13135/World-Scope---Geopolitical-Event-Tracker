import customtkinter as ctk
from database import setup_database
from auth import LoginWindow
from dashboard import DashboardFrame

# THEME CONFIGURATION
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def launch_dashboard(user):
    # This creates the new main window for the dashboard
    root = ctk.CTk()
    root.title("WorldScope | Global Event Intelligence Dashboard")
    root.geometry("1600x900")

    app_state = {"restart": False}
    
    def handle_logout(should_restart=False):
        app_state["restart"] = should_restart
        root.quit()
        
    
    app = DashboardFrame(root, user, on_logout=handle_logout)
    app.pack(fill="both", expand=True)
    root.mainloop()
    root.destroy()

    if app_state["restart"]:
        start_login()

def start_login():
    # Setup DB on first run
    setup_database()
    
    # Login Window Loop
    app = LoginWindow(on_login_success=launch_dashboard)
    app.mainloop()

if __name__ == "__main__":
    try:
        start_login()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"Application crashed: {e}")