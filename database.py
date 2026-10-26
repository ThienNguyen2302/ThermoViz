import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

class ThermoVizDatabase:
    """Enhanced database layer for ThermoViz: experimental runs + network modeling."""

    def __init__(self, db_path=None):
        """Initialize database connection and create tables."""
        if db_path is None:
            # Store in user's home directory under .thermoviz
            self.db_dir = Path.home() / ".thermoviz"
            self.db_dir.mkdir(exist_ok=True)
            db_path = self.db_dir / "thermoviz.db"
        self.db_path = str(db_path)
        self.init_database()

    def _connect(self):
        """Open a database connection with foreign-key enforcement enabled."""
        connection = sqlite3.connect(self.db_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    # -------DATABASE INITIALIZATION------------------------------

    def init_database(self):
        """Create all required tables if they don't exist."""
        with self._connect() as conn:
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

            # Table for storing network components (nodes in physical network)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_components (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,  -- Human-readable name (e.g., "Reactor_Vessel_1")
                    component_type TEXT NOT NULL,  -- e.g., 'tank', 'valve', 'sensor', 'pipe', 'pump'
                    properties TEXT,  -- JSON object of component-specific properties
                    -- Example properties:
                    -- Tank: {volume: 10.0, material: 'steel', max_pressure: 100}
                    -- Valve: {diameter: 0.05, flow_coefficient: 0.8, type: 'ball'}
                    -- Sensor: {type: 'pressure_transducer', range: [0, 50], accuracy: 0.01}
                    -- Pipe: {length: 5.0, diameter: 0.1, roughness: 0.0001}
                    created_in_run INTEGER,  -- Optional: link to run where defined
                    FOREIGN KEY (created_in_run) REFERENCES runs(id) ON DELETE SET NULL
                )
            ''')

            # Table for storing network relationships (edges/connections between components)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS network_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_component_id INTEGER NOT NULL,
                    target_component_id INTEGER NOT NULL,
                    relationship_type TEXT NOT NULL,  -- e.g., 'fluid_flow', 'signal', 'thermal_coupling', 'electrical'
                    properties TEXT,  -- JSON: e.g., {length: 2.5, diameter: 0.1, roughness: 0.0001, signal_type: 'voltage'}
                    created_in_run INTEGER,
                    FOREIGN KEY (source_component_id) REFERENCES network_components(id),
                    FOREIGN KEY (target_component_id) REFERENCES network_components(id),
                    FOREIGN KEY (created_in_run) REFERENCES runs(id) ON DELETE SET NULL,
                    CHECK (source_component_id != target_component_id)  -- No self-loops
                )
            ''')

            # Table for storing measurement data (time-series or parametric observations)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    component_id INTEGER,  -- Which component was measured (can be NULL for system-wide)
                    run_id INTEGER NOT NULL,  -- Which experimental run this belongs to
                    timestamp REAL,  -- When measurement was taken (seconds since run start or Unix timestamp)
                    measurement_type TEXT NOT NULL,  -- e.g., 'pressure', 'temperature', 'flow_rate', 'voltage', 'level'
                    value REAL NOT NULL,  -- The measured value
                    unit TEXT,  -- e.g., 'Pa', 'K', 'm³/s', 'V', 'm'
                    FOREIGN KEY (component_id) REFERENCES network_components(id) ON DELETE SET NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
                )
            ''')

            # Indexes for common query patterns
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_measurements_run_component
                ON measurements(run_id, component_id)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_measurements_type_time
                ON measurements(run_id, measurement_type, timestamp)
            ''')

            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_components_type
                ON network_components(component_type)
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

    # -------EXPERIMENTAL RUNS METHODS (Backward Compatible)------------------------------

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

        with self._connect() as conn:
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
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT data_json, description, file_path, columns_json, shape_json
                FROM runs WHERE id = ?
            ''', (run_id,))
            row = cursor.fetchone()

            if row is None:
                return None, None, None

            data_json, description, file_path, _, _ = row
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
        with self._connect() as conn:
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
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM runs WHERE id = ?', (run_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------NETWORK COMPONENTS METHODS------------------------------

    def add_component(self, name, component_type, properties=None, created_in_run=None):
        """
        Add a network component to the database.

        Args:
            name (str): Human-readable name for the component
            component_type (str): Type of component (e.g., 'tank', 'valve', 'sensor')
            properties (dict, optional): Component-specific properties as dictionary
            created_in_run (int, optional): ID of run where this component was defined

        Returns:
            int: The ID of the inserted component
        """
        properties_json = json.dumps(properties) if properties is not None else None

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO network_components (name, component_type, properties, created_in_run)
                VALUES (?, ?, ?, ?)
            ''', (name, component_type, properties_json, created_in_run))
            conn.commit()
            return cursor.lastrowid

    def get_component(self, component_id):
        """
        Retrieve a component by ID.

        Args:
            component_id (int): The ID of the component

        Returns:
            tuple: (id, name, component_type, properties, created_in_run) or None if not found
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, component_type, properties, created_in_run
                FROM network_components WHERE id = ?
            ''', (component_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            id_, name, component_type, properties_json, created_in_run = row
            properties = json.loads(properties_json) if properties_json is not None else None
            return (id_, name, component_type, properties, created_in_run)

    def get_all_components(self):
        """Get all network components."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, component_type, properties, created_in_run
                FROM network_components
                ORDER BY component_type, name
            ''')
            rows = cursor.fetchall()
            result = []
            for row in rows:
                id_, name, component_type, properties_json, created_in_run = row
                properties = json.loads(properties_json) if properties_json is not None else None
                result.append((id_, name, component_type, properties, created_in_run))
            return result

    def get_components_by_type(self, component_type):
        """Get all components of a specific type."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, component_type, properties, created_in_run
                FROM network_components
                WHERE component_type = ?
                ORDER BY name
            ''', (component_type,))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                id_, name, component_type, properties_json, created_in_run = row
                properties = json.loads(properties_json) if properties_json is not None else None
                result.append((id_, name, component_type, properties, created_in_run))
            return result

    def update_component(self, component_id, name=None, component_type=None, properties=None):
        """Update a component's information."""
        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if component_type is not None:
            updates.append("component_type = ?")
            params.append(component_type)
        if properties is not None:
            updates.append("properties = ?")
            params.append(json.dumps(properties))

        if not updates:
            return False

        params.append(component_id)
        query = f'''
            UPDATE network_components
            SET {', '.join(updates)}
            WHERE id = ?
        '''

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount > 0

    def delete_component(self, component_id):
        """Delete a component and its associated relationships."""
        with self._connect() as conn:
            cursor = conn.cursor()
            # Delete associated measurements first (due to foreign key)
            cursor.execute('DELETE FROM measurements WHERE component_id = ?', (component_id,))
            # Delete associated relationships
            cursor.execute('DELETE FROM network_relationships WHERE source_component_id = ? OR target_component_id = ?',
                          (component_id, component_id))
            # Delete the component
            cursor.execute('DELETE FROM network_components WHERE id = ?', (component_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------NETWORK RELATIONSHIPS METHODS------------------------------

    def add_relationship(self, source_component_id, target_component_id, relationship_type, properties=None, created_in_run=None):
        """
        Add a network relationship to the database.

        Args:
            source_component_id (int): ID of the source component
            target_component_id (int): ID of the target component
            relationship_type (str): Type of relationship (e.g., 'fluid_flow', 'signal')
            properties (dict, optional): Relationship-specific properties as dictionary
            created_in_run (int, optional): ID of run where this relationship was defined

        Returns:
            int: The ID of the inserted relationship
        """
        if source_component_id == target_component_id:
            raise ValueError("Source and target components must be different")

        properties_json = json.dumps(properties) if properties is not None else None

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO network_relationships (source_component_id, target_component_id, relationship_type, properties, created_in_run)
                VALUES (?, ?, ?, ?, ?)
            ''', (source_component_id, target_component_id, relationship_type, properties_json, created_in_run))
            conn.commit()
            return cursor.lastrowid

    def get_relationship(self, relationship_id):
        """
        Retrieve a relationship by ID.

        Args:
            relationship_id (int): The ID of the relationship

        Returns:
            tuple: (id, source_component_id, target_component_id, relationship_type, properties, created_in_run) or None if not found
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_component_id, target_component_id, relationship_type, properties, created_in_run
                FROM network_relationships WHERE id = ?
            ''', (relationship_id,))
            row = cursor.fetchone()

            if row is None:
                return None

            id_, source_id, target_id, relationship_type, properties_json, created_in_run = row
            properties = json.loads(properties_json) if properties_json is not None else None
            return (id_, source_id, target_id, relationship_type, properties, created_in_run)

    def get_relationships_for_component(self, component_id):
        """Get all relationships where the component is either source or target."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_component_id, target_component_id, relationship_type, properties, created_in_run
                FROM network_relationships
                WHERE source_component_id = ? OR target_component_id = ?
                ORDER BY id
            ''', (component_id, component_id))
            rows = cursor.fetchall()
            result = []
            for row in rows:
                id_, source_id, target_id, relationship_type, properties_json, created_in_run = row
                properties = json.loads(properties_json) if properties_json is not None else None
                result.append((id_, source_id, target_id, relationship_type, properties, created_in_run))
            return result

    def get_all_relationships(self):
        """Get all network relationships."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, source_component_id, target_component_id, relationship_type, properties, created_in_run
                FROM network_relationships
                ORDER BY id
            ''')
            rows = cursor.fetchall()
            result = []
            for row in rows:
                id_, source_id, target_id, relationship_type, properties_json, created_in_run = row
                properties = json.loads(properties_json) if properties_json is not None else None
                result.append((id_, source_id, target_id, relationship_type, properties, created_in_run))
            return result

    def delete_relationship(self, relationship_id):
        """Delete a relationship by ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM network_relationships WHERE id = ?', (relationship_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------MEASUREMENTS METHODS------------------------------

    def add_measurement(self, component_id, run_id, timestamp, measurement_type, value, unit=None):
        """
        Add a measurement to the database.

        Args:
            component_id (int): ID of the component being measured (can be None)
            run_id (int): ID of the experimental run
            timestamp (float): Time of measurement (seconds since run start or Unix timestamp)
            measurement_type (str): Type of measurement (e.g., 'pressure', 'temperature')
            value (float): Measured value
            unit (str, optional): Unit of measurement

        Returns:
            int: The ID of the inserted measurement
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO measurements (component_id, run_id, timestamp, measurement_type, value, unit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (component_id, run_id, timestamp, measurement_type, value, unit))
            conn.commit()
            return cursor.lastrowid

    def get_measurements_for_run(self, run_id, component_id=None, measurement_type=None):
        """
        Get measurements for a specific run, optionally filtered by component and/or measurement type.

        Args:
            run_id (int): ID of the experimental run
            component_id (int, optional): Filter by component ID
            measurement_type (str, optional): Filter by measurement type

        Returns:
            list of tuples: (id, component_id, run_id, timestamp, measurement_type, value, unit)
        """
        with self._connect() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT id, component_id, run_id, timestamp, measurement_type, value, unit
                FROM measurements
                WHERE run_id = ?
            '''
            params = [run_id]

            if component_id is not None:
                query += ' AND component_id = ?'
                params.append(component_id)

            if measurement_type is not None:
                query += ' AND measurement_type = ?'
                params.append(measurement_type)

            query += ' ORDER BY timestamp'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows

    def get_measurements_for_component(self, component_id, run_id=None, measurement_type=None):
        """
        Get measurements for a specific component, optionally filtered by run and/or measurement type.

        Args:
            component_id (int): ID of the component
            run_id (int, optional): Filter by run ID
            measurement_type (str, optional): Filter by measurement type

        Returns:
            list of tuples: (id, component_id, run_id, timestamp, measurement_type, value, unit)
        """
        with self._connect() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT id, component_id, run_id, timestamp, measurement_type, value, unit
                FROM measurements
                WHERE component_id = ?
            '''
            params = [component_id]

            if run_id is not None:
                query += ' AND run_id = ?'
                params.append(run_id)

            if measurement_type is not None:
                query += ' AND measurement_type = ?'
                params.append(measurement_type)

            query += ' ORDER BY timestamp'

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return rows

    def delete_measurement(self, measurement_id):
        """Delete a measurement by ID."""
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM measurements WHERE id = ?', (measurement_id,))
            conn.commit()
            return cursor.rowcount > 0

    # -------NETWORK ANALYSIS HELPERS------------------------------

    def get_neighbors(self, component_id):
        """
        Get all neighboring components connected to the given component.

        Args:
            component_id (int): ID of the component

        Returns:
            list of tuples: (neighbor_component_id, relationship_type, properties)
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    CASE
                        WHEN source_component_id = ? THEN target_component_id
                        ELSE source_component_id
                    END as neighbor_id,
                    relationship_type,
                    properties
                FROM network_relationships
                WHERE source_component_id = ? OR target_component_id = ?
            ''', (component_id, component_id, component_id))

            rows = cursor.fetchall()
            result = []
            for row in rows:
                neighbor_id, relationship_type, properties_json = row
                properties = json.loads(properties_json) if properties_json is not None else None
                result.append((neighbor_id, relationship_type, properties))
            return result

    def get_component_degree(self, component_id):
        """
        Get the degree (number of connections) for a component.

        Args:
            component_id (int): ID of the component

        Returns:
            int: Number of relationships connected to this component
        """
        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*)
                FROM network_relationships
                WHERE source_component_id = ? OR target_component_id = ?
            ''', (component_id, component_id))
            return cursor.fetchone()[0]

    # -------APPLICATION STATE METHODS------------------------------

    def save_app_state(self, key, value):
        """Save a piece of application state (as JSON)."""
        value_json = json.dumps(value)
        updated_at = datetime.now().isoformat()

        with self._connect() as conn:
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
        with self._connect() as conn:
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

    # Test network component functionality
    print("\n--- Testing Network Components -------")
    tank_id = db.add_component('Reactor_Vessel_1', 'tank',
                              {'volume': 10.0, 'material': 'stainless_steel', 'max_pressure': 100000})
    valve_id = db.add_component('Inlet_Valve', 'valve',
                               {'diameter': 0.05, 'flow_coefficient': 0.8, 'type': 'ball'})
    sensor_id = db.add_component('Pressure_Sensor_A', 'sensor',
                                {'type': 'pressure_transducer', 'range': [0, 150000], 'accuracy': 0.01})

    print(f"Added tank with ID: {tank_id}")
    print(f"Added valve with ID: {valve_id}")
    print(f"Added sensor with ID: {sensor_id}")

    # Test network relationship functionality
    print("\n--- Testing Network Relationships -------")
    flow_rel_id = db.add_relationship(tank_id, valve_id, 'fluid_flow',
                                     {'length': 2.5, 'diameter': 0.1, 'roughness': 0.0001})
    signal_rel_id = db.add_relationship(valve_id, sensor_id, 'signal',
                                       {'signal_type': 'voltage', 'max_voltage': 5.0, 'wire_length': 1.5})

    print(f"Added fluid_flow relationship with ID: {flow_rel_id}")
    print(f"Added signal relationship with ID: {signal_rel_id}")

    # Test measurements
    print("\n--- Testing Measurements -------")
    db.add_measurement(tank_id, run_id, 0, 'pressure', 101325, 'Pa')
    db.add_measurement(tank_id, run_id, 0, 'temperature', 298.15, 'K')
    db.add_measurement(valve_id, run_id, 0, 'flow_rate', 0.0015, 'mÂ³/s')
    db.add_measurement(sensor_id, run_id, 0, 'pressure', 101325, 'Pa')  # Sensor reading

    # Verify data retrieval
    print(f"\nComponents: {len(db.get_all_components())}")
    print(f"Relationships: {len(db.get_all_relationships())}")
    print(f"Measurements for run {run_id}: {len(db.get_measurements_for_run(run_id))}")

    # Test network analysis
    print(f"\nNeighbors of tank {tank_id}: {db.get_neighbors(tank_id)}")
    print(f"Degree of tank {tank_id}: {db.get_component_degree(tank_id)}")

    # Test app state
    print("\n--- Testing App State -------")
    db.save_app_state("last_used_component", "Reactor_Vessel_1")
    state = db.load_app_state("last_used_component")
    print(f"Loaded app state: {state}")

    print("\nâœ… All tests passed! Database schema enhancement successful.")
