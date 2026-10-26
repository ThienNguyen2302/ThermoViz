import sys
import os

# Add the current directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import tkinter as tk
    from tkinter import ttk
    import pandas as pd
    import matplotlib
except Exception as e:
    print(f"Error importing dependencies: {e}")
    sys.exit(1)

print("All imports successful")

try:
    root = tk.Tk()
    root.withdraw()
    root.destroy()
except tk.TclError as e:
    print(f"Tkinter display unavailable: {e}")
    sys.exit(2)

print("Tkinter root created and destroyed successfully")