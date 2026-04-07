import customtkinter as ctk
from tkinter import messagebox
import database_p2 as db

class AuthWindow(ctk.CTk):
    def __init__(self, on_success):
        super().__init__()
        self.on_success = on_success
        self.title("WorldScope P2 | Authentication")
        self.geometry("400x500")
        
        self.tabs = ctk.CTkTabview(self)
        self.tabs.pack(padx=20, pady=20, fill="both", expand=True)
        self.tab_login = self.tabs.add("Sign In")
        self.tab_signup = self.tabs.add("Sign Up")
        
        self.setup_login()
        self.setup_signup()

    def setup_login(self):
        ctk.CTkLabel(self.tab_login, text="Welcome Back", font=("Roboto", 24)).pack(pady=20)
        self.u_login = ctk.CTkEntry(self.tab_login, placeholder_text="Username", width=250)
        self.u_login.pack(pady=10)
        self.p_login = ctk.CTkEntry(self.tab_login, placeholder_text="Password", show="*", width=250)
        self.p_login.pack(pady=10)
        ctk.CTkButton(self.tab_login, text="Login", command=self.attempt_login).pack(pady=20)

    def setup_signup(self):
        ctk.CTkLabel(self.tab_signup, text="Create Account", font=("Roboto", 24)).pack(pady=20)
        self.u_signup = ctk.CTkEntry(self.tab_signup, placeholder_text="New Username", width=250)
        self.u_signup.pack(pady=10)
        self.p_signup = ctk.CTkEntry(self.tab_signup, placeholder_text="New Password", show="*", width=250)
        self.p_signup.pack(pady=10)
        ctk.CTkButton(self.tab_signup, text="Register", command=self.attempt_signup).pack(pady=20)

    def attempt_login(self):
        user = db.login_user(self.u_login.get(), self.p_login.get())
        if user:
            self.destroy()
            self.on_success(user[1]) # Pass username back to main
        else:
            messagebox.showerror("Error", "Invalid Credentials")

    def attempt_signup(self):
        if not self.u_signup.get() or not self.p_signup.get():
            messagebox.showwarning("Input Error", "All fields required")
            return
        if db.create_user(self.u_signup.get(), self.p_signup.get()):
            messagebox.showinfo("Success", "Account Created! Please Sign In.")
            self.tabs.set("Sign In")
        else:
            messagebox.showerror("Error", "Username already exists.")