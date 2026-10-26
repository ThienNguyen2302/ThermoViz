import sqlite3

import pandas as pd
import pytest


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


def test_component_deletion_removes_owned_relationships_and_measurements(database):
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
    assert database.get_measurements_for_component(component_id) == []
    assert database.delete_measurement(measurement_id) is False
    assert database.delete_component(component_id) is False
