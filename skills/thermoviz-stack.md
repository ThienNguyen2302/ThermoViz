# ThermoViz Tech Stack Skill

This skill documents the technology stack used in the ThermoViz project for integrating SQL databases with physical network models, starting with the Ideal Gas Law explorer.

## Overview

ThermoViz is a desktop application built to import experimental data (Excel), visualize relationships, and eventually integrate with SQL databases and physical network modeling. The current implementation provides a foundation for data import, plotting, and extensibility.

## Core Technologies

- **Language**: Python 3.14.7
- **GUI Framework**: Tkinter (standard with Python)
- **Data Handling**: 
  - pandas (data manipulation, Excel import/export)
  - openpyxl (Excel file support for pandas)
- **Visualization**:
  - matplotlib (plotting, embedded in Tkinter via FigureCanvasTkAgg)
  - networkx (for physical network modeling - planned)
- **Database** (planned integration):
  - SQLite (lightweight, file-based SQL database)
  - SQLAlchemy or sqlite3 module for ORM/raw queries
- **Project Management**:
  - Virtual environment (`venv`) for dependency isolation
  - pip for package management
  - Git for version control

## Current Features (Ideal Gas Law Explorer)

1. **Excel Import**: Load `.xlsx`/`.xls` files via file dialog
2. **Data Table View**: Display imported data in a sortable tabular format (Treeview)
3. **Interactive Plotting**: 
   - Select X/Y columns from dropdowns
   - Render scatter plots with matplotlib
   - Grid, labels, and titles auto-generated
4. **Tabbed Interface**: 
   - Plot tab for visualizations
   - Data tab for raw data inspection
5. **Sample Data**: Auto-generated ideal gas law dataset (PV=nRT) for immediate testing

## Planned Extensions

### SQL Database Integration
- Create SQLite database to store:
  - Experimental runs (metadata: timestamp, conditions, file source)
  - Component properties (for physical network models)
  - Measurement data (time-series or parametric sweeps)
  - Relationships between components (edges in network model)
- Implement CRUD operations via GUI:
  - Save current Excel data to database
  - Load data from database into application
  - Query and filter stored data
  - Export query results to Excel or CSV

### Physical Network Modeling
- Use networkx to create graphs where:
  - Nodes = physical components (e.g., valves, tanks, sensors)
  - Edges = relationships (e.g., fluid flow, signal transmission, thermal coupling)
- Visualize network graphs alongside data plots
- Allow users to:
  - Add/edit/delete nodes and edges
  - Assign properties to nodes/edges
  - Run simulations or analyses on the network
- Store network topology and properties in SQL database

### Enhanced Visualization
- Multiple plot types (line, bar, heatmap) based on data characteristics
- Network graph rendering with matplotlib/networkx
- Interactive annotations and tooltips
- Export plots as images (PNG, SVG)

### Data Analysis & Modeling
- Basic statistical analysis (mean, std, correlation)
- Curve fitting for physical laws (e.g., verify ideal gas constant)
- Machine learning integration for predictive modeling (future)

## Directory Structure

```
/ThermoViz
├── ideal_gas_app.py          # Main application entry point
├── README.md                 # Project overview and instructions
├── sample_data.xlsx          # Generated ideal gas law test data
├── test_imports.py           # Dependency verification script
├── .gitignore                # Git exclusion rules
├── venv/                     # Python virtual environment
│   ├── bin/                  # Activation scripts
│   └── lib/                  # Installed packages
├── skills/                   # (Optional) Hermes agent skills documentation
│   └── thermoviz-stack.md    # This file
└── agent.md                  # Agent-specific documentation (this file)
```

## Setup Instructions for Other Agents/Developers

1. **Clone Repository**: 
   ```bash
   git clone <repository-url>
   cd ThermoViz
   ```

2. **Activate Virtual Environment**:
   ```bash
   # Windows
   venv\Scripts\activate
   # Unix/macOS
   source venv/bin/activate
   ```

3. **Install Dependencies** (if not already in venv):
   ```bash
   pip install pandas matplotlib openpyxl networkx
   ```

4. **Run Application**:
   ```bash
   python ideal_gas_app.py
   ```

5. **Run Tests**:
   ```bash
   python test_imports.py
   ```

## Extending the Application

When adding new features:
1. Follow the MVC-ish pattern in `ideal_gas_app.py` (separate GUI logic from data handling)
2. Add new tabs to the `ttk.Notebook` for additional views
3. Use pandas DataFrames as the primary data structure for tabular data
4. For database operations, create a separate module (e.g., `database.py`) to encapsulate SQL logic
5. Keep GUI updates responsive by using threading for long-running operations (TODO)

## Known Limitations

- Current implementation loads entire Excel files into memory (suitable for modest datasets)
- Networkx integration not yet implemented
- SQLite database schema not yet created
- No data validation beyond basic type conversion in pandas
- Error handling could be improved for edge cases

## Future Considerations

- Switch to customtkinter or PyQt for modern UI aesthetics
- Implement configuration file (JSON/YAML) for user preferences
- Add unit tests with pytest
- Create executable builds with PyInstaller
- Integrate with hardware interfaces for real-time data acquisition

---

*This skill enables other Hermes agents to quickly understand the ThermoViz tech stack and contribute effectively to its development.*