# ThermoViz

ThermoViz is a Python desktop application for loading experimental data, exploring relationships between variables, and storing runs in SQLite. The current interface is a Tkinter-based Ideal Gas Law explorer with a database-backed run browser, and the underlying data model is already designed for broader physical-network work.

## What it does

- Import Excel files (`.xlsx`, `.xls`)
- Display the loaded dataset in a table
- Plot selected columns with Matplotlib
- Save and reload experimental runs in a local SQLite database
- View saved runs in a Database tab and delete them when needed

## Project architecture

The codebase is organized around a simple split:

- `ideal_gas_app.py` contains the Tkinter UI. The `IdealGasApp` class owns the loaded DataFrame, the plot canvas, the data table, and the database actions.
- `database.py` contains the durable storage layer. `ThermoVizDatabase` manages runs, network components, relationships, measurements, and app state.
- `tests/` contains automated checks for database behavior, migration edge cases, and import/Tkinter smoke coverage.
- `sample_data.xlsx` is the default dataset for quick validation and manual app testing.

The runtime flow is: Excel file -> pandas DataFrame -> database persistence -> DataFrame reconstruction for plotting and table display.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Required packages:
  - pandas
  - matplotlib
  - openpyxl
  - tkinter (bundled with Python on most environments)

## Setup

```bash
uv sync
```

## Running the app

```bash
uv run ideal_gas_app.py
```

Then:

1. Click `Load Excel File`
2. Choose the X and Y columns
3. Click `Plot Data`
4. Save or reload runs in the `Database` tab as needed

## Database storage

When no explicit database path is supplied, the app stores its SQLite database in the user profile under:

- Windows: `C:\Users\<username>\.thermoviz\thermoviz.db`
- macOS/Linux: `~/.thermoviz/thermoviz.db`

The database is used for:
- saved experimental runs
- metadata such as description and source file path
- component and relationship data for physical-network modeling
- measurement records and persisted app state

## Validation

Run the suite with:

```bash
uv run pytest
```

Run a single file or a single test with:

```bash
uv run pytest tests/test_database_runs.py -q
uv run pytest tests/test_database_network.py -k component_deletion -q
```

Run the dependency and Tkinter smoke check:

```bash
uv run python test_imports.py
```

The pytest suite uses temporary SQLite files and does not rely on the user-level database; `test_imports.py` checks both dependency imports and the ability to create a Tkinter root.

## Manual smoke test

A short validation flow for the desktop app is:

```bash
uv run ideal_gas_app.py
```

Then:

- load `sample_data.xlsx`
- select two columns
- plot the data
- save the current dataset as a run
- reload it from the Database tab
- delete the run

## License

MIT