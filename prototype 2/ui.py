import customtkinter as ctk
from tkinter import messagebox
import database_p2 as db

class Prototype2App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("WorldScope P2 - Modern Iteration")
        self.geometry("700x500")
        
        # UI Elements: Tabview for better organization than P1
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tabview.add("View Events")
        self.tabview.add("Add Event")
        
        self.setup_add_tab()
        
    def setup_add_tab(self):
        # Using CTk elements instead of standard tkinter
        self.label = ctk.CTkLabel(self.tabview.tab("Add Event"), text="New Event Entry", font=("Arial", 20))
        self.label.pack(pady=10)
        
        self.entry_name = ctk.CTkEntry(self.tabview.tab("Add Event"), placeholder_text="Event Name")
        self.entry_name.pack(pady=10)
        
        self.btn_save = ctk.CTkButton(self.tabview.tab("Add Event"), text="Save to Database", command=self.save_data)
        self.btn_save.pack(pady=20)

    def save_data(self):
        # Implementation of saving logic
        messagebox.showinfo("P2 Tech", "Data handling separated from UI logic!")

if __name__ == "__main__":
    db.init_db()
    app = Prototype2App()
    app.mainloop()