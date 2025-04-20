import tkinter as tk
from tkinter import ttk
import datetime
import os
import sys

class AboutWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("About PyQuick")
        self.window.resizable(False, False)
        
        # Calculate remaining days
        self.remin = (datetime.datetime(2025, 8, 13) - datetime.datetime.now()).days
        
        # Create main frame
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add image if exists (without Pillow)
        if os.path.exists("magic.png"):
            try:
                self.photo = tk.PhotoImage(file="magic.png")
                img_label = ttk.Label(main_frame, image=self.photo)
                img_label.pack(pady=5)
            except:
                pass  # Skip image if not supported format
        
        # Add title and version info
        ttk.Label(main_frame, text="PyQuick", font=('Helvetica', 14, 'bold')).pack(pady=5)
        ttk.Label(main_frame, text="Version: Dev (App build:2020)").pack()
        ttk.Label(main_frame, text=f"Expiration time: 2025.8.13 ({self.remin} days)").pack()
        
        # Add license info
        ttk.Label(main_frame, text="\nGNU GENERAL PUBLIC LICENSE:", font=('Helvetica', 10)).pack()
        
        # Add license text
        license_text = tk.Text(main_frame, height=10, width=50, wrap=tk.WORD)
        license_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Read license file if exists
        if os.path.exists("gpl3.txt"):
            try:
                with open("gpl3.txt", "r") as f:
                    license_text.insert(tk.END, f.read())
            except:
                license_text.insert(tk.END, "License text not available")
        
        license_text.config(state=tk.DISABLED)
        
        # Add warning if close to expiration
        if self.remin <= 14:
            ttk.Label(main_frame, 
                     text="⚠️ This Version Will Expire SOON! Please Upgrade this quickly.",
                     foreground="red").pack()
        
        # Add dev warning
        ttk.Label(main_frame, text="⚠️ The Dev version is not stable.", foreground="red").pack()
        ttk.Label(main_frame, 
                 text="If there is any problem, please post the problem immediately to the issues.",
                 foreground="red").pack()
        
        # Add copyright
        ttk.Label(main_frame, text="\n®Pyquick™ 2025. All rights reserved.", font=('Helvetica', 8)).pack()
        
        # Add OK button
        ttk.Button(main_frame, text="OK", command=self.window.destroy).pack(pady=10)

def show(parent=None):
    if parent is None:
        parent = tk.Tk()
        parent.withdraw()
    
    about_window = AboutWindow(parent)
    parent.wait_window(about_window.window)
    
    if parent.winfo_viewable():
        parent.deiconify()
    
    return about_window

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    show(root)
    root.mainloop()