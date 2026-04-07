import customtkinter as ctk
from database import setup_database
from auth import LoginWindow
from dashboard import DashboardFrame

# ─── Theme Configuration ──────────────────────────────────────────────────────
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


def launch_dashboard(user: dict) -> None:
    """
    Creates the main dashboard window for an authenticated user.
    BUG FIX: Added root.minsize() so the window cannot be shrunk to the point
             where the layout breaks.
    BUG FIX: Added platform-aware window maximise so it opens full-screen on
             both Windows (state zoomed) and other platforms (attributes zoomed).
    """
    root = ctk.CTk()
    root.title("WorldScope | Global Event Intelligence Dashboard")
    root.geometry("1600x900")
    root.minsize(1100, 650)   # Prevents the layout collapsing if resized small

    # Maximise on start — works on Windows; falls back gracefully elsewhere
    try:
        root.state("zoomed")
    except Exception:
        try:
            root.attributes("-zoomed", True)
        except Exception:
            pass  # Leave at the geometry() size on unsupported platforms

    app_state = {"restart": False}

    def handle_logout(should_restart: bool = False) -> None:
        app_state["restart"] = should_restart
        root.quit()

    app = DashboardFrame(root, user, on_logout=handle_logout)
    app.pack(fill="both", expand=True)
    root.mainloop()

    # Safely destroy after the event loop exits
    try:
        root.destroy()
    except Exception:
        pass

    if app_state["restart"]:
        start_login()


def start_login() -> None:
    """Sets up the database (first run only) then shows the login window."""
    setup_database()
    app = LoginWindow(on_login_success=launch_dashboard)
    app.mainloop()


if __name__ == "__main__":
    try:
        start_login()
    except KeyboardInterrupt:
        # Graceful exit when the user presses Ctrl+C in the terminal
        print("\nApplication closed via keyboard interrupt.")
    except Exception as e:
        # BUG FIX: Show the full traceback in the terminal so errors are not
        # silently swallowed, making debugging much easier during development.
        import traceback
        print("Application crashed with an unhandled exception:")
        traceback.print_exc()