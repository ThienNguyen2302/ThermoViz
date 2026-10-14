# Plan: Database Schema Enhancement for Network Modeling

**Source PRD**: Conversational request
**Selected Milestone**: Next implementation step
**Complexity**: Medium

## Summary
Enhance the ThermoViz database schema to properly support physical network modeling while maintaining backward compatibility with existing ideal gas law explorer functionality. This will involve adding tables for network components, relationships, and measurements, and updating the database interface to support these new capabilities.

## Patterns to Mirror
| Category | Source | Pattern |
|---|---|---|
| Naming | `database.py:17` | `ThermoVizDatabase` class with snake_case methods |
| Errors | `database.py:66` | Try/except blocks with connection context managers |
| Data access | `database.py:19-32` | SQL CREATE TABLE IF NOT EXISTS patterns |
| Tests | `test_imports.py:7-20` | Import verification and basic functionality tests |

## Files to Change
| File | Action | Why |
|---|---|---|
| `database.py` | UPDATE | Enhance schema and add methods for network modeling |
| `ideal_gas_app.py` | UPDATE | Integrate new network modeling features with UI |
| `README.md` | UPDATE | Document new database capabilities and usage |

## Tasks
### Task 1: Enhance Database Schema
- **Action**: Add tables for network components, relationships, and measurements to support physical network modeling
- **Mirror**: Follow the SQL pattern from `database.py:19-32` for table creation
- **Validate**: Run enhanced database initialization and verify table creation

### Task 2: Update Database Interface Methods
- **Action**: Add methods to `ThermoVizDatabase` for managing network components, relationships, and measurements
- **Mirror**: Follow the CRUD pattern from `database.py:47-73` (add_run) and `database.py:75-104` (get_run)
- **Validate**: Test all new methods with sample data

### Task 3: Maintain Backward Compatibility
- **Action**: Ensure existing ideal gas law explorer functionality continues to work unchanged
- **Mirror**: Preserve the existing `runs` table structure and `ThermoVizDatabase` public interface
- **Validate**: Verify that existing save/load/run management still works

### Task 4: Add Network Modeling Helper Methods
- **Action**: Add utility methods for common network operations (get neighbors, calculate degrees, etc.)
- **Mirror**: Follow the helper method pattern from `database.py:137-159` (app_state methods)
- **Validate**: Test network analysis methods with sample network data

### Task 5: Update Application Integration
- **Action**: Modify `ideal_gas_app.py` to utilize new network modeling capabilities
- **Mirror**: Follow the UI integration pattern from `ideal_gas_app.py:17-18` (database initialization)
- **Validate**: Verify new network features work with GUI

## Validation
```bash
# Test database initialization
python -c "from database import ThermoVizDatabase; db = ThermoVizDatabase(':memory:'); print('Database initialized')"

# Test basic run functionality (backward compatibility)
python -c "
from database import ThermoVizDatabase
import pandas as pd
import numpy as np
db = ThermoVizDatabase(':memory:')
df = pd.DataFrame({'P': [1, 2, 3], 'V': [3, 2, 1], 'T': [300, 300, 300]})
run_id = db.add_run(df, 'test')
df2, desc, path = db.get_run(run_id)
assert len(df2) == 3
print('Backward compatibility test passed')
"

# Test network component functionality
python -c "
from database import ThermoVizDatabase
db = ThermoVizDatabase(':memory:')
comp_id = db.add_component('Test_Tank', 'tank', {'volume': 10.0})
comp = db.get_component(comp_id)
assert comp[1] == 'Test_Tank'
assert comp[2] == 'tank'
print('Network component test passed')
"

# Test relationship functionality
python -c "
from database import ThermoVizDatabase
db = ThermoVizDatabase(':memory:')
comp1_id = db.add_component('Tank1', 'tank', {})
comp2_id = db.add_component('Valve1', 'valve', {})
rel_id = db.add_relationship(comp1_id, comp2_id, 'fluid_flow', {'diameter': 0.1})
rels = db.get_relationships_for_component(comp1_id)
assert len(rels) == 1
print('Network relationship test passed')
"
```

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Breaking existing functionality | Medium | Maintain backward compatibility by preserving existing table structure and API |
| Over-engineering for current needs | Low | Start with minimal viable network model, extend as needed |
| Performance degradation with complex queries | Medium | Add appropriate indexes and test with realistic data sizes |
| Schema migration complexity | Low | Using IF NOT EXISTS in CREATE TABLE allows safe evolution |

## Acceptance
- [ ] All tasks complete
- [ ] Validation passes
- [ ] Patterns mirrored, not reinvented
- [ ] Backward compatibility maintained for existing ideal gas law explorer
- [ ] New network modeling capabilities properly integrated and testable

**WAITING FOR CONFIRMATION**: Proceed with this plan? (yes/no/modify)