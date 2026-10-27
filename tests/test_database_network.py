import sqlite3

import pandas as pd
import pytest

from database import ThermoVizDatabase


def test_components_support_json_crud_and_type_filtering(database):
    run_id = database.add_run(pd.DataFrame({"value": [1]}))
    component_id = database.add_component(
        "Tank 1",
        "tank",
        {"volume": 10.0},
        created_in_run=run_id,
    )

    assert database.get_component(component_id) == (
        component_id,
        "Tank 1",
        "tank",
        {"volume": 10.0},
        run_id,
    )
    assert database.get_components_by_type("tank")[0][0] == component_id
    assert database.update_component(
        component_id,
        name="Tank A",
        properties={"volume": 12.5},
    )
    assert database.get_component(component_id)[1:4] == (
        "Tank A",
        "tank",
        {"volume": 12.5},
    )


def test_relationships_reject_self_loops_and_support_analysis(database):
    source_id = database.add_component("Tank", "tank")
    target_id = database.add_component("Valve", "valve")
    relationship_id = database.add_relationship(
        source_id,
        target_id,
        "fluid_flow",
        {"diameter": 0.1},
    )

    assert database.get_relationship(relationship_id)[4] == {"diameter": 0.1}
    assert len(database.get_relationships_for_component(source_id)) == 1
    assert database.get_neighbors(source_id) == [
        (target_id, "fluid_flow", {"diameter": 0.1})
    ]
    assert database.get_component_degree(source_id) == 1
    with pytest.raises(ValueError, match="different"):
        database.add_relationship(source_id, source_id, "invalid")


def test_measurements_filter_and_order_by_run_and_component(database):
    run_id = database.add_run(pd.DataFrame({"value": [1]}))
    component_id = database.add_component("Sensor", "sensor")
    first_id = database.add_measurement(
        component_id, run_id, 2.0, "temperature", 301.0, "K"
    )
    second_id = database.add_measurement(
        component_id, run_id, 1.0, "temperature", 300.0, "K"
    )
    database.add_measurement(None, run_id, 3.0, "pressure", 101325.0, "Pa")

    by_run = database.get_measurements_for_run(run_id)
    assert [row[0] for row in by_run] == [second_id, first_id, by_run[2][0]]
    assert database.get_measurements_for_run(
        run_id, component_id=component_id, measurement_type="temperature"
    ) == [by_run[0], by_run[1]]
    assert database.get_measurements_for_component(component_id, run_id) == [
        by_run[0],
        by_run[1],
    ]


def test_app_state_replaces_existing_json_value(database):
    database.save_app_state("plot", {"x": "temperature", "y": "pressure"})
    database.save_app_state("plot", {"x": "volume", "y": "pressure"})

    assert database.load_app_state("plot") == {"x": "volume", "y": "pressure"}
    assert database.load_app_state("missing") is None


def test_foreign_keys_are_enforced_for_relationships_and_measurements(database):
    with pytest.raises(sqlite3.IntegrityError):
        database.add_relationship(999, 1000, "fluid_flow")
    with pytest.raises(sqlite3.IntegrityError):
        database.add_measurement(None, 999, 0.0, "pressure", 1.0)


def test_run_deletion_cascades_measurements_and_nulls_originating_links(database):
    run_id = database.add_run(pd.DataFrame({"value": [1]}))
    component_id = database.add_component(
        "Tank", "tank", created_in_run=run_id
    )
    relationship_id = database.add_relationship(
        component_id,
        database.add_component("Valve", "valve"),
        "fluid_flow",
        created_in_run=run_id,
    )
    database.add_measurement(component_id, run_id, 0.0, "pressure", 1.0)

    assert database.delete_run(run_id)
    assert database.get_measurements_for_component(component_id) == []
    assert database.get_component(component_id)[4] is None
    assert database.get_relationship(relationship_id)[5] is None


def test_component_deletion_removes_relationships_and_nulls_measurement_component(
    database,
):
    run_id = database.add_run(pd.DataFrame({"value": [1]}))
    component_id = database.add_component("Sensor", "sensor")
    other_id = database.add_component("Tank", "tank")
    relationship_id = database.add_relationship(
        component_id, other_id, "signal"
    )
    measurement_id = database.add_measurement(
        component_id, run_id, 0.0, "temperature", 300.0
    )

    assert database.delete_component(component_id)
    assert database.get_relationship(relationship_id) is None
    assert database.get_measurements_for_run(run_id) == [
        (measurement_id, None, run_id, 0.0, "temperature", 300.0, None)
    ]
    assert database.delete_component(component_id) is False


def test_legacy_relationship_schema_is_migrated_on_initialization(database_path):
    with sqlite3.connect(database_path) as connection:
        connection.executescript(
            """
            CREATE TABLE runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                description TEXT,
                file_path TEXT,
                data_json TEXT,
                columns_json TEXT,
                shape_json TEXT
            );
            CREATE TABLE network_components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                component_type TEXT NOT NULL,
                properties TEXT,
                created_in_run INTEGER,
                FOREIGN KEY (created_in_run) REFERENCES runs(id) ON DELETE SET NULL
            );
            CREATE TABLE network_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_component_id INTEGER NOT NULL,
                target_component_id INTEGER NOT NULL,
                relationship_type TEXT NOT NULL,
                properties TEXT,
                created_in_run INTEGER,
                FOREIGN KEY (source_component_id) REFERENCES network_components(id),
                FOREIGN KEY (target_component_id) REFERENCES network_components(id),
                FOREIGN KEY (created_in_run) REFERENCES runs(id),
                CHECK (source_component_id != target_component_id)
            );
            CREATE TABLE measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                component_id INTEGER,
                run_id INTEGER NOT NULL,
                timestamp REAL,
                measurement_type TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                FOREIGN KEY (component_id) REFERENCES network_components(id) ON DELETE SET NULL,
                FOREIGN KEY (run_id) REFERENCES runs(id) ON DELETE CASCADE
            );
            CREATE TABLE app_state (
                id INTEGER PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT,
                updated_at TEXT NOT NULL
            );
            """
        )

    database = ThermoVizDatabase(database_path)
    run_id = database.add_run(pd.DataFrame({"value": [1]}))
    source_id = database.add_component("Tank", "tank", created_in_run=run_id)
    target_id = database.add_component("Valve", "valve")
    relationship_id = database.add_relationship(
        source_id, target_id, "fluid_flow", created_in_run=run_id
    )

    assert database.delete_run(run_id)
    assert database.get_relationship(relationship_id)[5] is None
