import tkinter as tk
from tkinter import ttk, messagebox
import database

class LoginWindow(tk.Toplevel):
    def __init__(self, parent, on_success):
        super().__init__(parent)
        self.parent = parent
        self.on_success = on_success
        self.title("Worldscope - Login")
        self.geometry("300x200")
        
    
        self.grab_set() 

        tk.Label(self, text="Username").pack(pady=5)
        self.ent_user = ttk.Entry(self)
        self.ent_user.pack()

        tk.Label(self, text="Password").pack(pady=5)
        self.ent_pass = ttk.Entry(self, show="*")
        self.ent_pass.pack()

        ttk.Button(self, text="Login", command=self.attempt_login).pack(pady=20)

    def attempt_login(self):
        user = database.verify_login(self.ent_user.get(), self.ent_pass.get())
        if user:
            messagebox.showinfo("Login", f"Welcome back, {user[1]}!")
            self.destroy()
            self.on_success()
        else:
            messagebox.showerror("Error", "Invalid username or password")