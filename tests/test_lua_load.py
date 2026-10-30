from lua_helpers import load_module, new_runtime


def install_modifier():
    """Run the load script's runFn with a stub addModifier and return the captured model modifier."""
    runtime, module = load_module("ap_load.script")
    captured = {}
    runtime.globals().addModifier = lambda kind, fn: captured.__setitem__(kind, fn)
    runtime.execute("function data_unused() end")
    table = runtime.globals().data()
    table.runFn(None, None)
    return runtime, captured["loadModel"]


def model(runtime, **parts):
    return runtime.table_from({key: runtime.table_from(value) if isinstance(value, dict) else value for key, value in parts.items()})


def test_vehicle_end_year_is_removed():
    runtime, modifier = install_modifier()
    data = runtime.table_from({"metadata": runtime.table_from({
        "transportVehicle": runtime.table_from({"x": 1}),
        "availability": runtime.table_from({"yearFrom": 1930, "yearTo": 1950}),
    })})
    result = modifier("vehicle/train/a.mdl", data)
    assert result["metadata"]["availability"]["yearTo"] == 0
    assert result["metadata"]["availability"]["yearFrom"] == 1930  # the first year stays: tiers are built on it


def test_non_vehicle_models_are_untouched():
    runtime, modifier = install_modifier()
    data = runtime.table_from({"metadata": runtime.table_from({
        "availability": runtime.table_from({"yearFrom": 1930, "yearTo": 1950}),
    })})
    assert modifier("buildings/house.mdl", data)["metadata"]["availability"]["yearTo"] == 1950


def test_vehicle_without_availability_does_not_fail():
    runtime, modifier = install_modifier()
    data = runtime.table_from({"metadata": runtime.table_from({"transportVehicle": runtime.table_from({"x": 1})})})
    assert modifier("vehicle/train/b.mdl", data)["metadata"]["transportVehicle"]["x"] == 1


def test_model_without_metadata_does_not_fail():
    runtime, modifier = install_modifier()
    data = runtime.table_from({"lods": 1})
    assert modifier("x.mdl", data)["lods"] == 1
