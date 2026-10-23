# ThermoViz Application Validation Design

## Purpose

Create a repeatable validation layer that establishes whether the current
ThermoViz application is healthy enough for continued development. The
validation targets application readiness: database correctness plus
database-independent application/import behavior, with a documented manual
check for the Tkinter desktop UI.

The design is additive. Existing database and GUI behavior must remain
unchanged unless a test exposes a defect that prevents the documented
contract from working.

## Scope

### In scope

- Automated tests for the public `ThermoVizDatabase` interface.
- Verification of SQLite schema creation, indexes, persistence, and
  referential behavior.
- Backward-compatibility tests for experimental run storage and retrieval.
- Network component, relationship, measurement, and analysis-helper tests.
- A headless-friendly application import/data-path smoke check.
- Documentation of automated and manual validation commands.

### Out of scope

- Automated interaction with Tkinter widgets.
- GUI automation tooling or platform-specific desktop drivers.
- Network simulation, numerical modeling, or new user-facing network UI.
- Replacing the existing SQLite implementation or introducing an ORM.
- Unrelated refactoring of the application.

## Validation Architecture

Add a pytest test suite under `tests/`, using temporary SQLite database paths
for every test or fixture. Tests will use the existing public methods on
`ThermoVizDatabase`; they will not depend on private implementation details.
The existing `test_imports.py` script remains an environment/dependency smoke
check and will be documented separately from the automated suite.

If application logic cannot be tested without constructing a Tkinter root,
extract only the smallest GUI-independent operation needed for the smoke
test. Do not add a GUI abstraction solely to increase test coverage.

## Test Matrix

### Database initialization

- Construct an in-memory or temporary-file database.
- Assert that `runs`, `network_components`, `network_relationships`,
  `measurements`, and `app_state` exist.
- Assert that the documented indexes exist.
- Reopen a file-backed database to verify initialization is idempotent and
  data persists.

### Backward compatibility

- Store a representative pandas DataFrame with `add_run`.
- Retrieve it with `get_run` and assert values, columns, shape, description,
  and file path.
- Verify run listing and deletion.
- Include an empty DataFrame and a multi-column DataFrame; any incompatibility
  is a backward-compatibility defect to resolve with a regression test.

### Network model

- Create, retrieve, update, list, filter, and delete components, including
  JSON properties.
- Create and retrieve relationships, reject self-loops, list relationships
  for a component, and delete relationships.
- Add measurements and verify run, component, and measurement-type filters.
- Verify `get_neighbors` and `get_component_degree` for directed stored
  relationships.
- Verify app-state save/load round-trips.

### Integrity and lifecycle

- Test invalid foreign-key references explicitly. If the current connections
  do not enforce the declared foreign keys, enable enforcement as the
  smallest production change needed to make the schema contract reliable.
- Verify run deletion and component deletion match the schema's declared
  cascade/set-null behavior.
- Ensure temporary database files are cleaned up by test fixtures.

### Application smoke checks

- Import `ideal_gas_app` without constructing a GUI.
- Run `test_imports.py` in an environment with Tk support.
- Document a manual `uv run ideal_gas_app.py` launch check for a desktop
  environment and require that it starts without an application traceback.

## Failure Handling

Tests must assert observable behavior and fail on missing schema objects,
malformed JSON, changed tuple shapes, incorrect filtering or ordering,
broken lifecycle behavior, and import errors. Tests must not catch broad
exceptions to convert failures into passes.

The manual GUI check must report display/Tk availability separately from
application errors. A headless environment may prevent the manual launch
check, but it must not prevent the automated database and import checks from
running.

## Documentation

Update `README.md` with a Validation section containing:

1. Environment setup using the project's supported Python/uv workflow.
2. The automated pytest command.
3. The `python test_imports.py` dependency and Tk smoke command.
4. The manual desktop launch command.
5. A short distinction between automated checks and the manual GUI check.

## Acceptance Criteria

- The automated test suite runs from a clean environment and passes.
- Database initialization creates all expected tables and indexes.
- Existing run save/load behavior passes unchanged.
- Network CRUD, filtering, relationship analysis, and lifecycle behavior
  pass with representative data.
- `ideal_gas_app` imports without constructing a GUI or raising an import
  error.
- `test_imports.py` passes where Tk is available.
- README documents the commands and expected validation boundaries.
- No new test writes to the user's persistent `~/.thermoviz` database.

## Implementation Notes

Use the smallest test and documentation changes that satisfy this contract.
Production changes are not expected unless a test demonstrates that the
current public contract cannot be validated or that an existing behavior is
broken. Any such change must be covered by a regression test.
