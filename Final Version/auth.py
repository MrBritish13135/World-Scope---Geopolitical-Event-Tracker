import customtkinter as ctk
from tkinter import messagebox
from database import (
    validate_login, user_exists, create_user,
    update_last_login, log_activity
)


class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.title("WorldScope | Secure Login")
        self.geometry("400x550")
        self.resizable(False, False)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="🌐", font=("Roboto", 80)).grid(row=0, column=0, pady=(40, 0))

        ctk.CTkLabel(self, text="World-Scope", font=("Roboto", 32, "bold"),
                     text_color="#3b8ed0").grid(row=1, column=0, pady=(10, 5))

        ctk.CTkLabel(self, text="Global Event Tracker",
                     font=("Roboto", 14), text_color="gray").grid(row=2, column=0, pady=(0, 30))

        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=280, height=40)
        self.username_entry.grid(row=3, column=0, pady=10)

        self.password_entry = ctk.CTkEntry(
            self, placeholder_text="Password", show="*", width=280, height=40
        )
        self.password_entry.grid(row=4, column=0, pady=10)
        self.password_entry.bind("<Return>", lambda e: self.check_login())

        self.show_pass_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self, text="Show Password", variable=self.show_pass_var,
                        command=self.toggle_password,
                        font=("Roboto", 12)).grid(row=5, column=0, pady=10)

        ctk.CTkButton(
            self, text="Sign In", command=self.check_login,
            width=280, height=45, font=("Roboto", 16, "bold")
        ).grid(row=6, column=0, pady=(20, 10))

        ctk.CTkButton(
            self, text="Create Account", fg_color="transparent", border_width=2,
            command=self.open_signup, width=280, height=40
        ).grid(row=7, column=0, pady=10)

    def toggle_password(self):
        self.password_entry.configure(show="" if self.show_pass_var.get() else "*")

    def check_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()

        if not u or not p:
            messagebox.showerror("Login Failed", "Please enter both a username and password.")
            return

        user = validate_login(u, p)
        if user:
            update_last_login(u)
            log_activity(u, "login")
            user_info = {"username": u, "role": user[0]}
            self.quit()
            self.destroy()
            self.on_login_success(user_info)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            self.password_entry.delete(0, "end")

    def open_signup(self):
        # Store reference to prevent garbage collection
        self._signup_window = SignupWindow(self)


class SignupWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("WorldScope | Registration")
        self.geometry("400x640")   # Taller to fit the confirm password field
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Create Account",
                     font=("Roboto", 20, "bold")).grid(row=0, column=0, pady=20)

        self.u  = ctk.CTkEntry(self, placeholder_text="Username",     width=250)
        self.fn = ctk.CTkEntry(self, placeholder_text="First Name",   width=250)
        self.ln = ctk.CTkEntry(self, placeholder_text="Last Name",    width=250)
        self.p  = ctk.CTkEntry(self, placeholder_text="Password",     show="*", width=250)
        # FEATURE: Confirm password field
        self.p2 = ctk.CTkEntry(self, placeholder_text="Confirm Password", show="*", width=250)

        for i, field in enumerate([self.u, self.fn, self.ln, self.p, self.p2]):
            field.grid(row=i + 1, column=0, pady=8)

        ctk.CTkLabel(self, text="Assign Role:").grid(row=6, column=0, pady=(10, 0))
        self.role_var = ctk.StringVar(value="viewer")
        ctk.CTkOptionMenu(
            self, variable=self.role_var,
            values=["viewer", "analyst", "admin"], width=250
        ).grid(row=7, column=0, pady=8)

        ctk.CTkButton(
            self, text="Register", command=self.register,
            fg_color="#27ae60", hover_color="#219150", width=250
        ).grid(row=8, column=0, pady=25)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def register(self):
        u  = self.u.get().strip()
        fn = self.fn.get().strip()
        ln = self.ln.get().strip()
        p  = self.p.get().strip()
        p2 = self.p2.get().strip()
        r  = self.role_var.get()

        if not u:
            messagebox.showerror("Error", "Username is required.")
            return
        if not fn or not ln:
            messagebox.showerror("Error", "First and last name are required.")
            return
        if not p:
            messagebox.showerror("Error", "Password is required.")
            return
        if len(p) < 6:
            messagebox.showerror("Error", "Password must be at least 6 characters long.")
            return
        # FEATURE: Confirm password check
        if p != p2:
            messagebox.showerror("Error", "Passwords do not match. Please try again.")
            self.p.delete(0, "end")
            self.p2.delete(0, "end")
            return
        if user_exists(u):
            messagebox.showerror("Error", "That username is already taken.")
            return

        create_user(u, p, r, fn, ln)
        messagebox.showinfo("Success", f"Account '{u}' created! You can now log in.")
        self._on_close()

    def _on_close(self):
        if hasattr(self.parent, '_signup_window'):
            self.parent._signup_window = None
        self.destroy()