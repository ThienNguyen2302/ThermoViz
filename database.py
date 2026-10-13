import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

class ThermoVizDatabase:
    def __init__(self, db_path=None):
        if db_path is None:
            # Store in user's home directory under .thermoviz
            self.db_dir = Path.home() / ".thermoviz"
            self.db_dir.mkdir(exist_ok=True)
            db_path = self.db_dir / "thermoviz.db"
        self.db_path = str(db_path)
        self.init_database()
    
    def init_database(self):
        """Create tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Table for storing experimental runs
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    description TEXT,
                    file_path TEXT,  -- Original Excel file path
                    data_json TEXT,  -- JSON representation of the data (for small to medium datasets)
                    columns_json TEXT,  -- List of column names
                    shape_json TEXT     -- [rows, columns] shape of the data
                )
            ''')
            
            # Table for storing user sessions/application state (optional)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_state (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,  -- JSON string
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.commit()
    
    def add_run(self, df, description="", file_path=""):
        """
        Add a DataFrame to the database as a new run.
        
        Args:
            df (pd.DataFrame): The data to store
            description (str): User description of the run
            file_path (str): Original file path of the Excel file
            
        Returns:
            int: The ID of the inserted run
        """
        # Convert DataFrame to JSON for storage
        data_json = df.to_json(orient='split')
        columns_json = json.dumps(list(df.columns))
        shape_json = json.dumps(list(df.shape))
        
        timestamp = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO runs (timestamp, description, file_path, data_json, columns_json, shape_json)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (timestamp, description, file_path, data_json, columns_json, shape_json))
            conn.commit()
            return cursor.lastrowid
    
    def get_run(self, run_id):
        """
        Retrieve a run by ID and return as a DataFrame.
        
        Args:
            run_id (int): The ID of the run
            
        Returns:
            tuple: (df, description, file_path) or (None, None, None) if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_json, description, file_path, columns_json, shape_json
                FROM runs WHERE id = ?
            ''', (run_id,))
            row = cursor.fetchone()
            
            if row is None:
                return None, None, None
            
            data_json, description, file_path, columns_json, shape_json = row
            # Reconstruct DataFrame using StringIO to avoid file path interpretation issues
            import io
            try:
                df = pd.read_json(io.StringIO(data_json), orient='split')
            except AttributeError:
                # Fallback for older pandas versions
                df = pd.read_json(data_json, orient='split')
            return df, description, file_path
    
    def get_all_runs(self):
        """
        Get a list of all runs with metadata.
        
        Returns:
            list of tuples: (id, timestamp, description, file_path, shape)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, description, file_path, shape_json
                FROM runs
                ORDER BY timestamp DESC
            ''')
            rows = cursor.fetchall()
            # Parse shape_json back to list
            result = []
            for row in rows:
                id_, timestamp, description, file_path, shape_json = row
                shape = json.loads(shape_json)
                result.append((id_, timestamp, description, file_path, shape))
            return result
    
    def delete_run(self, run_id):
        """Delete a run by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM runs WHERE id = ?', (run_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def save_app_state(self, key, value):
        """Save a piece of application state (as JSON)."""
        value_json = json.dumps(value)
        updated_at = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO app_state (id, key, value, updated_at)
                VALUES (
                    (SELECT id FROM app_state WHERE key = ?),
                    ?, 
                    ?, 
                    ?
                )
            ''', (key, key, value_json, updated_at))
            # If the row didn't exist, the above won't insert, so we do:
            if cursor.rowcount == 0:
                cursor.execute('''
                    INSERT INTO app_state (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, value_json, updated_at))
            conn.commit()
    
    def load_app_state(self, key):
        """Load a piece of application state."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT value FROM app_state WHERE key = ?
            ''', (key,))
            row = cursor.fetchone()
            if row is None:
                return None
            value_json = row[0]
            return json.loads(value_json)

# Example usage (for testing)
if __name__ == "__main__":
    db = ThermoVizDatabase()
    # Create a test DataFrame
    import pandas as pd
    import numpy as np
    df = pd.DataFrame({
        'A': np.random.randn(5),
        'B': np.random.randn(5),
        'C': np.random.randint(0, 10, 5)
    })
    run_id = db.add_run(df, description="Test run", file_path="test.xlsx")
    print(f"Added run with ID: {run_id}")
    
    # Retrieve it
    df2, desc, fpath = db.get_run(run_id)
    print(f"Retrieved DataFrame:\n{df2}")
    print(f"Description: {desc}")
    print(f"File path: {fpath}")
    
    # List all runs
    runs = db.get_all_runs()
    print(f"All runs: {runs}")
    
    # Test app state
    db.save_app_state("last_used_column", "A")
    state = db.load_app_state("last_used_column")
    print(f"Loaded app state: {state}")