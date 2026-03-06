import tkinter as tk
import database
from ui_login import LoginWindow
from ui_dashboard import DashboardFrame

class MainApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Worldscope System")
        self.root.geometry("600x500")
        self.root.withdraw() # Hide main window until login

        # Initialize Database
        database.initialize_db()

        # Show Login
        self.show_login()

    def show_login(self):
        self.login_screen = LoginWindow(self.root, self.enter_dashboard)

    def enter_dashboard(self):
        self.root.deiconify() # Show main window
        self.dashboard = DashboardFrame(self.root)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApp()
    app.run()