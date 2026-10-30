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


def install_all_modifiers():
    runtime, _ = load_module("ap_load.script")
    captured = {}
    runtime.globals().addModifier = lambda kind, fn: captured.__setitem__(kind, fn)
    runtime.globals().data().runFn(None, None)
    return runtime, captured


def test_street_templates_lose_their_end_year_but_keep_the_first_year():
    runtime, captured = install_all_modifiers()
    template = runtime.table_from({"availability": runtime.table_from({"yearFrom": 0, "yearTo": 1940})})
    result = captured["loadStreetTemplate"]("::/infrastructure/street/country/country_old_small.street_template", template)
    assert result["availability"]["yearTo"] == 0 and result["availability"]["yearFrom"] == 0


def test_street_template_without_availability_does_not_fail():
    runtime, captured = install_all_modifiers()
    assert captured["loadStreetTemplate"]("x", runtime.table_from({"cost": 1}))["cost"] == 1


def test_only_infrastructure_constructions_lose_their_end_year():
    runtime, captured = install_all_modifiers()

    def construction():
        return runtime.table_from({"availability": runtime.table_from({"yearFrom": 1925, "yearTo": 1980})})

    road = captured["loadConstruction"]("::/infrastructure/street_construction/roundabout.con", construction())
    house = captured["loadConstruction"]("::/buildings/house.con", construction())
    assert road["availability"]["yearTo"] == 0
    assert house["availability"]["yearTo"] == 1980


def test_construction_without_availability_does_not_fail():
    runtime, captured = install_all_modifiers()
    assert captured["loadConstruction"]("::/infrastructure/signal/a.con", runtime.table_from({"x": 1}))["x"] == 1
