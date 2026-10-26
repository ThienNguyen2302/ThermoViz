import importlib


def test_ideal_gas_app_imports_without_creating_a_root():
    module = importlib.import_module("ideal_gas_app")

    assert hasattr(module, "IdealGasApp")
