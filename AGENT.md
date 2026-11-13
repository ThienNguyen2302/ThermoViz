# ThermoViz agent guide

## What this project is

ThermoViz is a Python desktop application for exploring experimental datasets and, in the current codebase, storing them in SQLite. The UI is Tkinter-based and centered around loading Excel files, plotting columns, and saving/loading runs. The database layer also includes a richer network-modeling schema for components, relationships, and measurements.

## Repository layout

- `ideal_gas_app.py`: Tkinter app entry point and UI logic.
- `database.py`: SQLite data layer (`ThermoVizDatabase`).
- `tests/`: pytest coverage for database behavior and import smoke checks.
- `README.md`: project overview and user-facing workflow.
- `sample_data.xlsx`: sample Ideal Gas Law dataset.
- `test_imports.py`: import and Tkinter availability smoke test.

## Working commands

Use the repo-managed environment via `uv`.

- Install dependencies: `uv sync`
- Run the app: `uv run ideal_gas_app.py`
- Run the full suite: `uv run pytest`
- Run a single file: `uv run pytest tests/test_database_runs.py -q`
- Run one specific test: `uv run pytest tests/test_database_network.py -k component_deletion -q`
- Run the import/Tkinter check: `uv run python test_imports.py`

There is no dedicated lint configuration in the repository right now; the active validation path is pytest plus `test_imports.py`.

## Architecture and data flow

The important picture is:

1. Excel file is read with pandas.
2. The DataFrame is displayed and plotted in the Tkinter UI.
3. The app persists runs through `ThermoVizDatabase.add_run()`.
4. `database.py` stores JSON payloads for data, columns, and shape, along with metadata like description and file path.
5. The database layer also supports network entities (`network_components`, `network_relationships`, `measurements`, `app_state`).

Keep this separation intact: UI logic belongs in `ideal_gas_app.py`; persistence, schema, migration, and query logic belong in `database.py`.

## Conventions specific to this repo

- Prefer `ThermoVizDatabase` over ad hoc SQLite code in the UI.
- Treat the app as a DataFrame-centric desktop tool, not a web app; most state is local and in-memory until saved.
- Keep new tests isolated from the default home-directory database. The fixtures in `tests/conftest.py` deliberately use `tmp_path`.
- Preserve the existing JSON-backed storage layout (`data_json`, `columns_json`, `shape_json`, `properties`).
- When changing schemas or migrations, validate both the current behavior and the legacy migration tests in `tests/test_database_network.py`.
- The app is local-first and writes to `~/.thermoviz/thermoviz.db` when a custom path is not provided.

## Environment and compatibility

- Python requirement: `>=3.14` per `pyproject.toml`.
- The project uses `uv` with `package = false`, so run commands through `uv run ...` instead of expecting an installed project package.
- Tkinter must work in the environment; the import smoke test checks this separately from dependency import failures.

## Editing guidance

- Update the database layer before adding new persistence behavior in the UI.
- Keep `IdealGasApp` methods focused on orchestrating interactions, not on raw SQL statements.
- Favor small, targeted tests for any database contract change or UI regression.
- If you need to validate manually, load `sample_data.xlsx`, choose two columns, plot them, save a run, reload it, and delete it.

## Summary

This repo is a compact Python desktop + SQLite project with a clear separation between the Tkinter UI and the persistence layer. The best way to work safely here is to keep the app logic thin, reuse `ThermoVizDatabase`, and validate with the existing pytest tests and `test_imports.py` smoke check.