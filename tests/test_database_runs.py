import sqlite3

import pandas as pd
from pandas.testing import assert_frame_equal

from database import ThermoVizDatabase


def test_initialization_creates_expected_tables_and_indexes(database_path):
    ThermoVizDatabase(database_path)

    with sqlite3.connect(database_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        indexes = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
            )
        }

    assert {
        "runs",
        "network_components",
        "network_relationships",
        "measurements",
        "app_state",
    } <= tables
    assert {
        "idx_measurements_run_component",
        "idx_measurements_type_time",
        "idx_components_type",
    } <= indexes

    ThermoVizDatabase(database_path)


def test_run_round_trip_preserves_data_and_metadata(database):
    frame = pd.DataFrame(
        {"temperature": [300.0, 325.5], "pressure": [101325.0, 110000.0]}
    )

    run_id = database.add_run(
        frame,
        description="baseline run",
        file_path="sample_data.xlsx",
    )

    loaded, description, file_path = database.get_run(run_id)

    assert_frame_equal(
        loaded.reset_index(drop=True),
        frame.reset_index(drop=True),
        check_dtype=False,
    )
    assert description == "baseline run"
    assert file_path == "sample_data.xlsx"


def test_empty_and_multi_column_runs_round_trip(database):
    frames = [
        pd.DataFrame(columns=["temperature", "pressure"]),
        pd.DataFrame(
            {
                "temperature": [300, 310],
                "volume": [0.01, 0.02],
                "pressure": [24943.4, 12886.4],
            }
        ),
    ]

    for frame in frames:
        run_id = database.add_run(frame)
        loaded, _, _ = database.get_run(run_id)
        assert_frame_equal(
            loaded.reset_index(drop=True),
            frame.reset_index(drop=True),
            check_dtype=False,
        )
        assert loaded.shape == frame.shape
        assert list(loaded.columns) == list(frame.columns)


def test_runs_are_listed_newest_first_and_delete_is_idempotent(database):
    first_id = database.add_run(pd.DataFrame({"value": [1]}))
    second_id = database.add_run(pd.DataFrame({"value": [2]}))

    runs = database.get_all_runs()

    assert [run[0] for run in runs] == [second_id, first_id]
    assert database.delete_run(first_id) is True
    assert database.delete_run(first_id) is False
    assert database.get_run(first_id) == (None, None, None)
