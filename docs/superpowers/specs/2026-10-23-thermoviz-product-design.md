# ThermoViz Product Specification

## Purpose

ThermoViz is a local desktop application for exploring tabular
thermodynamic data, initially centered on the Ideal Gas Law. It provides a
simple workflow for importing Excel data, inspecting it, plotting selected
variables, and preserving experimental runs in a local SQLite database.

This specification describes the current product contract evidenced by the
repository. It is a product baseline, not a roadmap for unimplemented
simulation, modeling, or visualization features.

## Scope

### In scope

- Excel workbook import (`.xlsx` and `.xls`).
- Tabular inspection of the active pandas DataFrame.
- Scatter plotting of two selected DataFrame columns.
- Saving, listing, loading, and deleting experimental runs.
- Per-user SQLite persistence under `~/.thermoviz/thermoviz.db`.
- Persistence APIs for network components, directed relationships,
  measurements, and JSON application state.
- A Tkinter desktop interface with Plot, Data, and Database tabs.
- Validation of database and database-independent application behavior.

### Out of scope

- Automated interaction with Tkinter widgets.
- GUI automation tooling or platform-specific desktop drivers.
- Network simulation or numerical modeling.
- A user-facing network modeling workflow.
- Machine learning, advanced statistical analysis, or additional plot types.
- SQL-server integration or replacement of SQLite.
- An ORM or migration framework.
- Unrelated refactoring of the current GUI structure.

## User Contract

A user can:

1. Start the desktop application.
2. Load an Excel workbook.
3. Inspect its rows and columns in the Data tab.
4. Choose X and Y columns and render a scatter plot.
5. Save the active DataFrame as a named experimental run.
6. Browse saved runs in the Database tab.
7. Load a saved run back into the active table and plot.
8. Delete a saved run.

The application does not require a server or network connection. The active
DataFrame is transient until explicitly saved.

Network components, relationships, measurements, and application state are
available through the database layer but are not currently exposed as GUI
workflows.

## Architecture

### Presentation boundary

`IdealGasApp` owns the Tkinter window, controls, dialogs, tabs, Treeviews,
and embedded Matplotlib canvas. User actions are translated into load,
display, plot, save, load, refresh, and delete operations.

### Data-processing and display path

pandas represents the active workbook or loaded run as a DataFrame. Column
names populate the X/Y selectors. Plotting reads the selected Series and
renders a scatter plot. The active DataFrame is the session's working state
and is not automatically persisted.

### Persistence boundary

`ThermoVizDatabase` owns SQLite schema initialization and CRUD operations.
It stores run metadata and DataFrame JSON, network component and relationship
records, measurements, and JSON application state.

### Primary data flow

```text
Excel file
    -> pandas DataFrame
    -> table and column selectors
    -> Matplotlib scatter plot

DataFrame + description + source path
    -> SQLite run

SQLite run
    -> pandas DataFrame
    -> table and plot
```

Database listings are ordered newest-first. Deleting the currently loaded run
clears the active UI state.

## Database Flow

On startup, `ThermoVizDatabase` resolves the default database path to
`Path.home() / ".thermoviz" / "thermoviz.db"`, creates the directory, opens
SQLite connections per operation, and creates missing tables and indexes
idempotently.

When saving a run, the active DataFrame is serialized using split-oriented
JSON. Description, source file path, column names, shape, and an ISO timestamp
are stored as metadata. The returned run ID becomes the active run ID and the
Database tab is refreshed.

When loading a run, the database reconstructs the DataFrame, updates the
table and column selectors, and marks the run active. When deleting a run,
the durable record is removed. If it was active, the UI clears the DataFrame,
plot, selectors, title, and active ID.

Network measurements are owned by runs and are intended to cascade on run
deletion. Optional originating-run and component references are intended to
become null according to the schema contract.

## Database Entities

### `runs`

Stores a durable DataFrame snapshot and its metadata:

- Generated ID.
- ISO timestamp.
- Optional description.
- Optional source file path.
- Split-oriented JSON data.
- JSON column list.
- JSON shape.

### `network_components`

Stores named physical or instrumentation elements such as tanks, valves,
sensors, pipes, or pumps:

- ID.
- Name.
- Component type.
- Optional JSON properties.
- Optional originating run ID.

### `network_relationships`

Stores directed connections between distinct components:

- ID.
- Source component ID.
- Target component ID.
- Relationship type.
- Optional JSON properties.
- Optional originating run ID.

Self-loops are invalid.

### `measurements`

Stores time-series or parametric numeric observations:

- ID.
- Required run ID.
- Optional component ID.
- Timestamp.
- Measurement type.
- Numeric value.
- Optional unit.

Measurements are ordered by timestamp when retrieved.

### `app_state`

Stores JSON-encoded application state by unique key. Saving an existing key
replaces its prior value.

## SQLite Tables and Indexes

The schema contains these tables:

| Table | Purpose |
| --- | --- |
| `runs` | DataFrame snapshots and run metadata |
| `network_components` | Physical and instrumentation components |
| `network_relationships` | Directed component connections |
| `measurements` | Numeric observations |
| `app_state` | JSON-encoded application state |

The schema declares these indexes:

- `idx_measurements_run_component` on `(run_id, component_id)`.
- `idx_measurements_type_time` on
  `(run_id, measurement_type, timestamp)`.
- `idx_components_type` on `(component_type)`.

Schema creation uses `CREATE TABLE IF NOT EXISTS` and
`CREATE INDEX IF NOT EXISTS` so initialization is idempotent.

## SQL and Integrity Requirements

The persistence layer uses Python's `sqlite3` module and SQLite-compatible
SQL.

- Use `?` placeholders for all supplied values; never interpolate values into
  SQL.
- Keep JSON serialization and deserialization at the Python boundary.
- Preserve primary keys, foreign keys, `NOT NULL` constraints, the
  relationship self-loop `CHECK`, and declared `CASCADE`/`SET NULL` actions.
- Enable `PRAGMA foreign_keys = ON` for every connection when lifecycle
  guarantees depend on enforcement.
- Scope transactions to individual operations with explicit commits.
- Propagate failed operations as errors; never report success after failure.
- Use an explicit migration strategy for future schema changes.

No ORM or migration framework is required by this current-state contract.

## Desktop UX

The main window is titled `Ideal Gas Law Explorer` and defaults to a
1000x700 layout. It provides controls for loading Excel files, saving and
loading database runs, plotting, and selecting X/Y columns.

The required tabs are:

- **Plot:** an embedded Matplotlib scatter chart with axis labels, a title,
  grid, and semi-transparent points.
- **Data:** a scrollable Treeview showing the active DataFrame.
- **Database:** a refreshable run list with load-selected and delete-selected
  actions.

Canceling file or description dialogs performs no operation. Actions without
required data or a selection show warnings and do not mutate persistence.
Excel, plotting, database, and reconstruction errors show an error dialog with
operation context. Successful operations show confirmation feedback and
refresh dependent views.

Tkinter display availability is an environment prerequisite. Automated
validation remains headless-friendly by testing imports, data paths, and
persistence separately from the manual GUI launch.

## Runtime and Commands

The supported runtime is Python 3.14 or newer, managed with `uv`.

```text
uv sync
uv run ideal_gas_app.py
uv run python test_imports.py
uv run pytest
```

The manual desktop check should load `sample_data.xlsx`, select two columns,
plot them, save a run, reload it, and delete it.

## Validation and Acceptance

Automated validation must:

- Import `ideal_gas_app` without constructing a Tk root.
- Create all five tables and three documented indexes idempotently.
- Verify run metadata, DataFrame JSON, columns, shape, and empty or
  multi-column DataFrame round trips.
- Verify run listing, newest-first ordering, retrieval, and deletion.
- Verify component, relationship, measurement, neighbor, degree, and
  application-state operations.
- Reject self-loops and invalid foreign-key references explicitly.
- Verify cascade and set-null lifecycle behavior.
- Use temporary database paths and never modify the user's persistent
  `~/.thermoviz/thermoviz.db`.
- Document the distinction between automated checks and the manual GUI check.

The acceptance baseline is met when the automated suite passes in a clean
`uv` environment, the import/dependency smoke check passes where Tk is
available, and the manual desktop workflow completes without an application
traceback.

## Non-Goals of This Specification

This document does not require implementation of network visualization,
physical simulation, machine-learning prediction, advanced statistics,
additional plot types, export/report generation, SQL-server support, GUI
automation, or architectural refactoring. Those capabilities may be
considered separately after the current product contract is validated.
