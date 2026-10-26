import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from database import ThermoVizDatabase


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "thermoviz.db"


@pytest.fixture
def database(database_path):
    return ThermoVizDatabase(database_path)
