import customtkinter as ctk
from tkinter import messagebox
from database import validate_login, user_exists, create_user, update_last_login

class LoginWindow(ctk.CTk):
    def __init__(self, on_login_success):
        super().__init__()
        self.on_login_success = on_login_success
        self.title("WorldScope | Secure Login")
        self.geometry("400x550")
        self.grid_columnconfigure(0, weight=1)

        # Visual Replacement for Image
        ctk.CTkLabel(self, text="🌐", font=("Roboto", 80)).grid(row=0, column=0, pady=(40, 0))
        
        ctk.CTkLabel(self, text="World-Scope", font=("Roboto", 32, "bold"), 
                     text_color="#3b8ed0").grid(row=1, column=0, pady=(10, 5))
        
        ctk.CTkLabel(self, text="Global Event Tracker", 
                     font=("Roboto", 14), text_color="gray").grid(row=2, column=0, pady=(0, 30))
                     
        self.username_entry = ctk.CTkEntry(self, placeholder_text="Username", width=280, height=40)
        self.username_entry.grid(row=3, column=0, pady=10)
        self.username_entry.insert(0, "admin") 

        self.password_entry = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=280, height=40)
        self.password_entry.grid(row=4, column=0, pady=10)

        self.show_pass_var = ctk.BooleanVar()
        ctk.CTkCheckBox(self, text="Show Password", variable=self.show_pass_var, 
                        command=self.toggle_password, font=("Roboto", 12)).grid(row=5, column=0, pady=10)

        ctk.CTkButton(self, text="Sign In", command=self.check_login, width=280, height=45, font=("Roboto", 16, "bold")).grid(row=6, column=0, pady=(20, 10))
        
        ctk.CTkButton(self, text="Create Account", fg_color="transparent", border_width=2, 
                      command=self.open_signup, width=280, height=40).grid(row=7, column=0, pady=10)

    def toggle_password(self):
        self.password_entry.configure(show="" if self.show_pass_var.get() else "*")

    def check_login(self):
        u = self.username_entry.get().strip()
        p = self.password_entry.get().strip()
        
        user = validate_login(u, p)
        if user:
           update_last_login(u)
           user_info = {
               "username": u,
               "role": user[0],
           }
           self.quit()
           self.destroy()
           self.on_login_success(user_info)
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
            

    def open_signup(self):
        SignupWindow(self)
        

class SignupWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("WorldScope | Registration")
        self.geometry("400x580")
        self.attributes("-topmost", True)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Create Account", font=("Roboto", 20, "bold")).grid(row=0, column=0, pady=20)

        self.u = ctk.CTkEntry(self, placeholder_text="Username", width=250)
        self.fn = ctk.CTkEntry(self, placeholder_text="First Name", width=250)
        self.ln = ctk.CTkEntry(self, placeholder_text="Last Name", width=250)
        self.p = ctk.CTkEntry(self, placeholder_text="Password", show="*", width=250)
        
        fields = [self.u, self.fn, self.ln, self.p]
        for i, field in enumerate(fields):
            field.grid(row=i+1, column=0, pady=10)

        ctk.CTkLabel(self, text="Assign Role:").grid(row=5, column=0, pady=(10, 0))
        self.role_var = ctk.StringVar(value="viewer")
        ctk.CTkOptionMenu(self, variable=self.role_var, values=["viewer", "analyst", "admin"], width=250).grid(row=6, column=0, pady=10)

        ctk.CTkButton(self, text="Register", command=self.register, fg_color="#27ae60", hover_color="#219150", width=250).grid(row=7, column=0, pady=30)

    def register(self):
        u, p, r, fn, ln = self.u.get(), self.p.get(), self.role_var.get(), self.fn.get(), self.ln.get()
        if not all([u, p, fn, ln]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return
        if user_exists(u):
            messagebox.showerror("Error", "Username taken.")
            return
        create_user(u, p, r, fn, ln)
        messagebox.showinfo("Success", "Account created!")
        self.destroy()