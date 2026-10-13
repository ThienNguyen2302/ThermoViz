import sys
import os

# Add the current directory to the path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Try to import the necessary modules
    import tkinter as tk
    from tkinter import ttk
    import pandas as pd
    import matplotlib
    print("All imports successful")
    
    # Try to create a Tkinter root and destroy it (without showing)
    root = tk.Tk()
    root.withdraw()  # Hide the window
    root.destroy()
    print("Tkinter root created and destroyed successfully")
    
except Exception as e:
    print(f"Error during test: {e}")
    sys.exit(1)