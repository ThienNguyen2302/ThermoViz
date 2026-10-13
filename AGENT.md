# ThermoViz Agent Documentation

This file provides essential information for AI agents working on the ThermoViz project.

## Project Overview

ThermoViz is a desktop application designed to integrate SQL databases with physical network models, beginning with an Ideal Gas Law explorer. The application allows users to import experimental data from Excel files, visualize relationships between variables, and will eventually support database storage and network modeling of physical systems.

## Current State

The application currently includes:
- Excel file import functionality
- Interactive data plotting (scatter plots)
- Tabular data display
- Sample ideal gas law data for immediate testing
- Basic GUI built with Tkinter

## Tech Stack Summary

**Language**: Python 3.14.7  
**GUI**: Tkinter  
**Data Processing**: pandas, openpyxl  
**Visualization**: matplotlib  
**Planned**: networkx for network modeling, SQLite for data storage  
**Environment**: Virtual environment (venv) with pinned dependencies

## Key Files

- `ideal_gas_app.py` - Main application logic
- `sample_data.xlsx` - Test dataset (ideal gas law calculations)
- `test_imports.py` - Dependency verification script
- `skills/thermoviz-stack.md` - Detailed technology stack documentation
- `README.md` - User-focused project overview
- `.gitignore` - Standard Python/git exclusions

## Development Guidelines

1. **Virtual Environment**: Always work within the activated venv
   ```bash
   # Windows
   venv\Scripts\activate
   # Unix/macOS
   source venv/bin/activate
   ```

2. **Dependencies**: Core packages are pandas, matplotlib, openpyxl. 
   Additional planned packages: networkx, (optional) SQLAlchemy

3. **Code Structure**: 
   - Keep GUI logic separate from data processing where possible
   - Use classes for modularity (current app uses IdealGasApp class)
   - Add new features as additional methods or classes
   - For database work, consider creating a separate database module

4. **UI Patterns**:
   - Main window uses ttk.Notebook for tabbed interface
   - Data displayed in ttk.Treeview for tabular data
   - Plots embedded via FigureCanvasTkAgg from matplotlib
   - Controls use standard ttk widgets (Buttons, Comboboxes, Labels)

## Immediate Next Steps for Development

1. **Database Integration**:
   - Add SQLite database connection/storage capabilities
   - Create schema for storing experimental data
   - Implement save/load/query GUI controls

2. **Network Modeling**:
   - Integrate networkx for graph creation
   - Add network visualization tab
   - Implement node/edge creation and editing

3. **Enhanced Features**:
   - Additional plot types (line, bar, etc.)
   - Data analysis tools (statistics, fitting)
   - Export capabilities (images, reports)

## Running the Application

```bash
cd /d/ThermoViz
# Activate environment if not already active
venv\Scripts\activate  # Windows
# or source venv/bin/activate  # Unix/macOS
python ideal_gas_app.py
```

## Testing

Run dependency verification:
```bash
python test_imports.py
```

This should confirm all required packages are available and Tkinter is functional.

## Contact

For questions about extending or modifying this application, refer to the detailed technology stack in `skills/thermoviz-stack.md` or the user instructions in `README.md`.

---
*This document helps AI agents quickly understand the ThermoViz project structure and contribute effectively to its development.*