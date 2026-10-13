import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import os
from database import ThermoVizDatabase

class IdealGasApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ideal Gas Law Explorer")
        self.root.geometry("1000x700")
        
        # Initialize database
        self.db = ThermoVizDatabase()
        
        self.df = None
        self.current_run_id = None
        
        # Create main frames
        self.control_frame = ttk.Frame(root, padding="10")
        self.control_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.display_frame = ttk.Frame(root)
        self.display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Control widgets
        ttk.Button(self.control_frame, text="Load Excel File", command=self.load_excel).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Save to Database", command=self.save_to_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Load from Database", command=self.load_from_database_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Plot Data", command=self.plot_data).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(self.control_frame, text="X-axis:").pack(side=tk.LEFT, padx=(20,2))
        self.x_var = tk.StringVar()
        self.x_combo = ttk.Combobox(self.control_frame, textvariable=self.x_var, state="readonly", width=15)
        self.x_combo.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self.control_frame, text="Y-axis:").pack(side=tk.LEFT, padx=(10,2))
        self.y_var = tk.StringVar()
        self.y_combo = ttk.Combobox(self.control_frame, textvariable=self.y_var, state="readonly", width=15)
        self.y_combo.pack(side=tk.LEFT, padx=2)
        
        # Display area for plot and data table
        self.notebook = ttk.Notebook(self.display_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Plot tab
        self.plot_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.plot_tab, text="Plot")
        
        # Data tab
        self.data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text="Data")
        
        # Database tab
        self.db_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.db_tab, text="Database")
        
        # Initialize plot area
        self.figure = plt.Figure(figsize=(8,5), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, self.plot_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Initialize data table (using Treeview)
        self.tree = ttk.Treeview(self.data_tab, show="headings")
        self.tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Scrollbars for treeview
        vsb = ttk.Scrollbar(self.data_tab, orient="vertical", command=self.tree.yview)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb = ttk.Scrollbar(self.data_tab, orient="horizontal", command=self.tree.xview)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Initialize database runs table
        self.setup_database_tab()

    def setup_database_tab(self):
        """Setup the database tab with runs list and controls."""
        # Controls frame
        db_control_frame = ttk.Frame(self.db_tab)
        db_control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(db_control_frame, text="Refresh List", command=self.refresh_runs_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(db_control_frame, text="Load Selected", command=self.load_selected_run).pack(side=tk.LEFT, padx=5)
        ttk.Button(db_control_frame, text="Delete Selected", command=self.delete_selected_run).pack(side=tk.LEFT, padx=5)
        
        # Runs list frame
        list_frame = ttk.Frame(self.db_tab)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create Treeview for runs
        self.runs_tree = ttk.Treeview(list_frame, columns=("ID", "Timestamp", "Description", "File Path", "Shape"), show="headings")
        self.runs_tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        # Define headings
        self.runs_tree.heading("ID", text="ID")
        self.runs_tree.heading("Timestamp", text="Timestamp")
        self.runs_tree.heading("Description", text="Description")
        self.runs_tree.heading("File Path", text="File Path")
        self.runs_tree.heading("Shape", text="Shape (Rows x Cols)")
        
        # Define column widths
        self.runs_tree.column("ID", width=50)
        self.runs_tree.column("Timestamp", width=150)
        self.runs_tree.column("Description", width=200)
        self.runs_tree.column("File Path", width=200)
        self.runs_tree.column("Shape", width=100)
        
        # Scrollbars for runs tree
        vsb_runs = ttk.Scrollbar(list_frame, orient="vertical", command=self.runs_tree.yview)
        vsb_runs.pack(side=tk.RIGHT, fill=tk.Y)
        hsb_runs = ttk.Scrollbar(list_frame, orient="horizontal", command=self.runs_tree.xview)
        hsb_runs.pack(side=tk.BOTTOM, fill=tk.X)
        self.runs_tree.configure(yscrollcommand=vsb_runs.set, xscrollcommand=hsb_runs.set)
        
        # Initial population
        self.refresh_runs_list()
    
    def refresh_runs_list(self):
        """Refresh the list of runs in the database tab."""
        # Clear existing items
        for item in self.runs_tree.get_children():
            self.runs_tree.delete(item)
        
        # Get all runs and populate
        runs = self.db.get_all_runs()
        for run_id, timestamp, description, file_path, shape in runs:
            # Format timestamp for display (trim microseconds)
            display_timestamp = timestamp.split('.')[0] if '.' in timestamp else timestamp
            shape_str = f"{shape[0]} x {shape[1]}"
            self.runs_tree.insert("", tk.END, values=(run_id, display_timestamp, description or "", file_path, shape_str))
    
    def load_excel(self):
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls")]
        )
        if not file_path:
            return
        try:
            self.df = pd.read_excel(file_path)
            self.update_comboboxes()
            self.display_data()
            messagebox.showinfo("Success", f"Loaded {len(self.df)} rows from {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load Excel file: {e}")
    
    def update_comboboxes(self):
        if self.df is not None:
            cols = list(self.df.columns)
            self.x_combo['values'] = cols
            self.y_combo['values'] = cols
            if len(cols) >= 2:
                self.x_var.set(cols[0])
                self.y_var.set(cols[1])
    
    def display_data(self):
        if self.df is None:
            return
        # Clear existing data
        for i in self.tree.get_children():
            self.tree.delete(i)
        # Set columns
        self.tree["columns"] = list(self.df.columns)
        for col in self.df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor=tk.CENTER)
        # Insert rows
        for _, row in self.df.iterrows():
            self.tree.insert("", tk.END, values=list(row))
    
    def plot_data(self):
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first")
            return
        x_col = self.x_var.get()
        y_col = self.y_var.get()
        if not x_col or not y_col:
            messagebox.showwarning("Warning", "Please select X and Y columns")
            return
        try:
            x = self.df[x_col]
            y = self.df[y_col]
            # Clear previous plot
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.scatter(x, y, alpha=0.7)
            ax.set_xlabel(x_col)
            ax.set_ylabel(y_col)
            ax.set_title(f"{y_col} vs {x_col}")
            ax.grid(True, linestyle='--', alpha=0.5)
            self.canvas.draw()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to plot: {e}")

    def save_to_database(self):
        """Save the current DataFrame to the database."""
        if self.df is None:
            messagebox.showwarning("Warning", "Please load data first")
            return
        
        # Ask for description
        description = tk.simpledialog.askstring("Save to Database", "Enter a description for this run:", parent=self.root)
        if description is None:  # User cancelled
            return
        
        # Get the file path from the last load operation
        file_path = getattr(self, 'last_file_path', "")
        
        try:
            run_id = self.db.add_run(self.df, description=description, file_path=file_path)
            self.current_run_id = run_id
            messagebox.showinfo("Success", f"Saved to database with ID: {run_id}")
            self.refresh_runs_list()  # Update the database tab
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save to database: {e}")

    def load_from_database_dialog(self):
        """Show a dialog to select and load a run from the database."""
        runs = self.db.get_all_runs()
        if not runs:
            messagebox.showinfo("Info", "No runs found in database")
            return
        
        # Create a simple selection dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Load Run from Database")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Select a run to load:").pack(pady=10)
        
        # Listbox for runs
        listbox_frame = ttk.Frame(dialog)
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        listbox = tk.Listbox(listbox_frame)
        listbox.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        scrollbar.pack(fill=tk.Y, side=tk.RIGHT)
        listbox.config(yscrollcommand=scrollbar.set)
        
        # Store run IDs corresponding to listbox items
        run_ids = []
        for run_id, timestamp, description, file_path, shape in runs:
            display_text = f"ID {run_id}: {timestamp.split('.')[0]} - {description or '(no description)'} [{shape[0]}x{shape[1]}]"
            listbox.insert(tk.END, display_text)
            run_ids.append(run_id)
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def on_load():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select a run")
                return
            idx = selection[0]
            run_id = run_ids[idx]
            dialog.destroy()
            self.load_run_by_id(run_id)
        
        def on_cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Load", command=on_load).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=on_cancel).pack(side=tk.LEFT, padx=5)
        
        # Double-click to load
        def on_double_click(event):
            on_load()
        
        listbox.bind("<Double-1>", on_double_click)
    
    def load_run_by_id(self, run_id):
        """Load a specific run by ID into the current application state."""
        df, description, file_path = self.db.get_run(run_id)
        if df is None:
            messagebox.showerror("Error", f"Run with ID {run_id} not found")
            return
        
        self.df = df
        self.current_run_id = run_id
        self.update_comboboxes()
        self.display_data()
        
        # Update window title to show current run
        self.root.title(f"Ideal Gas Law Explorer - Run {run_id}")
        
        messagebox.showinfo("Success", f"Loaded run ID {run_id} from database")
    
    def load_selected_run(self):
        """Load the currently selected run in the database tab."""
        selection = self.runs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a run from the list")
            return
        
        item = self.runs_tree.item(selection[0])
        run_id = int(item['values'][0])  # First column is ID
        self.load_run_by_id(run_id)
    
    def delete_selected_run(self):
        """Delete the currently selected run from the database."""
        selection = self.runs_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a run from the list")
            return
        
        item = self.runs_tree.item(selection[0])
        run_id = int(item['values'][0])
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete run ID {run_id}?"):
            if self.db.delete_run(run_id):
                messagebox.showinfo("Success", f"Deleted run ID {run_id}")
                self.refresh_runs_list()
                # If we deleted the currently loaded run, clear it
                if self.current_run_id == run_id:
                    self.df = None
                    self.current_run_id = None
                    self.update_comboboxes()
                    self.display_data()
                    self.figure.clear()
                    self.canvas.draw()
                    self.root.title("Ideal Gas Law Explorer")
            else:
                messagebox.showerror("Error", f"Failed to delete run ID {run_id}")

if __name__ == "__main__":
    root = tk.Tk()
    app = IdealGasApp(root)
    root.mainloop()