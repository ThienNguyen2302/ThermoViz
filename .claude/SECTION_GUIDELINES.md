# Section Organization Guidelines for ThermoViz

## Section Separator Format
Use the exact format: `---SECTION NAME----------------------------` on a single line to group related functions.

## Guidelines
1. Each section should contain functions that are logically related to the section's theme
2. Section separators should be placed before the first function in that section
3. Use descriptive, concise section names that clearly indicate the purpose/functionality group
4. Maintain backward compatibility - do not change existing function signatures or behavior
5. Follow the existing code patterns and naming conventions within each section

## Examples from database.py:
```
---DATABASE INITIALIZATION----------------------------
def init_database(self):
    # Creates all required tables

---EXPERIMENTAL RUNS METHODS (Backward Compatible)----------------------------
def add_run(self, df, description="", file_path=""):
    # Adds a DataFrame as a new run
    
def get_run(self, run_id):
    # Retrieves a run by ID

---NETWORK COMPONENTS METHODS----------------------------
def add_component(self, name, component_type, properties=None, created_in_run=None):
    # Adds a network component
    
def get_component(self, component_id):
    # Retrieves a component by ID
```

## Purpose
This organization makes it easier for developers and agents to:
- Locate related functionality quickly
- Understand the code structure at a glance
- Maintain and extend the codebase consistently
- Preserve backward compatibility while adding new features