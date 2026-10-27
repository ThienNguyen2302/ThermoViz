# Ideal Gas Law Explorer with Database Integration

A desktop application to import Excel files, visualize relationships between physical components, and store/retrieve data from a local SQLite database, starting with the Ideal Gas Law (PV = nRT) explorer.

## Features

- Import data from Excel files (.xlsx, .xls)
- Interactive plotting of selected columns (scatter plots)
- Data table view for inspecting imported data
- Local SQLite database for saving and loading experimental runs
- Application state persistence (last used columns, etc.)
- Database browser tab to view, load, and delete saved runs
- Simple and intuitive Tkinter-based GUI

## Requirements

- Python 3.14 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Required packages:
  - pandas
  - matplotlib
  - openpyxl
  - tkinter (usually comes with Python)

## Installation

1. Clone or download this repository.
2. Install the project dependencies with `uv`:
   ```bash
   uv sync
   ```

## Usage

1. Run the application:
   ```bash
   uv run ideal_gas_app.py
   ```
2. Click "Load Excel File" to select your Excel file.
3. Choose X and Y columns from the dropdown menus.
4. Click "Plot Data" to visualize the relationship.
5. Use the "Database" tab to:
   - Save current data to the database with a description
   - Load previously saved runs
   - Delete unwanted runs
   - Refresh the runs list
6. Switch between the "Plot", "Data", and "Database" tabs to view different aspects of your work.

## Sample Data

The project includes a `sample_data.xlsx` file generated from the Ideal Gas Law:
- Temperature (K) from 200 to 400
- Volume (m³) from 0.001 to 0.01
- Pressure (Pa) calculated as P = nRT/V (with n=1 mol, R=8.314462618 J/(mol·K))

## Database Storage

The application uses a local SQLite database stored in your user directory:
- Windows: `C:\Users\<username>\.thermoviz\thermoviz.db`
- macOS/Linux: `~/.thermoviz/thermoviz.db`

The database stores:
- Experimental runs with timestamps, descriptions, and file origins
- The actual data (as JSON) for small to medium datasets
- Application state (like last used column selections)

## Validation

Set up the supported Python environment and run the automated checks with:

```bash
uv sync
uv run pytest
uv run python test_imports.py
```

The pytest suite uses temporary SQLite database files and is headless-friendly;
it does not modify the persistent database under `~/.thermoviz`. The
`test_imports.py` command checks both Python dependencies and whether Tkinter
can create a display root. It reports display/Tk availability separately from
dependency import errors, so it may require a desktop environment.

For the manual desktop check, launch the application with:

```bash
uv run ideal_gas_app.py
```

Load `sample_data.xlsx`, choose two columns, plot them, save the active data
as a run, reload the run from the Database tab, and delete it. The manual
check uses the per-user database under the `.thermoviz` directory documented
above and should complete without an application traceback.

## Extending the Project

This application can be extended to:
- Import data from SQL databases (beyond the local SQLite)
- Model more complex physical networks using networkx
- Add advanced visualization options (line plots, bar charts, etc.)
- Incorporate machine learning for predictive modeling
- Add data analysis tools (statistics, curve fitting, etc.)

## License

MIT