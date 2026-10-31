from lupa import LuaRuntime

from lua_helpers import from_lua, load_module, to_lua


def costs():
    return load_module("ap_costs")


def normalised(file_name, year, cost, maintenance=None):
    runtime, module = costs()
    data = {"availability": {"yearFrom": year}, "cost": cost}
    if maintenance is not None:
        data["maintenanceCost"] = maintenance
    table = to_lua(runtime, data)
    module.normalise(file_name, table)
    return from_lua(table)


def test_the_era_coefficient_follows_the_first_year_of_the_model():
    _, module = costs()
    assert [module.era_coefficient(year) for year in (1850, 1939, 1940, 1979, 1980, 2020)] == [1, 1, 3, 3, 9, 9]


def test_a_modern_depot_is_brought_back_to_the_price_of_the_first_era():
    result = normalised("::/depots/road/road_depot/road_depot.con", 1990, [1_620_000, -1], [270_000, -1])
    assert result["cost"] == [180_000, -1]
    assert result["maintenanceCost"] == [30_000, -1]


def test_a_mid_era_station_is_divided_by_three():
    result = normalised("::/stations/rail/modular_station/modular_station.con", 1950, [594_000, 13_140_000])
    assert result["cost"] == [198_000, 4_380_000]


def test_the_first_era_is_left_alone():
    assert normalised("::/depots/rail/rail_depot.con", 1900, [600_000, -1])["cost"] == [600_000, -1]


def test_constructions_without_an_era_coefficient_are_never_changed():
    assert normalised("::/stations/street/small_stops/small_new.con", 1990, [30_000, -1])["cost"] == [30_000, -1]
    assert normalised("::/industries/steel_mill/steel_mill.con", 1990, [900_000, -1])["cost"] == [900_000, -1]


def test_a_construction_without_a_year_or_a_cost_is_left_alone():
    runtime, module = costs()
    for data in ({"cost": [900_000, -1]}, {"availability": {"yearFrom": 1990}}, {}):
        table = to_lua(runtime, data)
        module.normalise("::/depots/road/road_depot/road_depot.con", table)
        assert from_lua(table) == data or from_lua(table) == [] and data == {}


def test_free_and_unpriced_entries_stay_as_they_are():
    result = normalised("::/depots/water/water_depot.con", 1990, [0, -1])
    assert result["cost"] == [0, -1]


def templated(file_name, templates):
    runtime, module = costs()
    data = {"availability": {}, "constructionTemplates": [
        {"availability": {"yearFrom": year, "yearTo": 0},
         "description": {"attributes": {"cost": cost, "maintenanceCost": upkeep}}}
        for year, cost, upkeep in templates]}
    table = to_lua(runtime, data)
    module.normalise(file_name, table)
    return from_lua(table)["constructionTemplates"]


def test_each_template_of_a_depot_is_divided_by_its_own_era_coefficient():
    result = templated("::/depots/road/road_depot/road_depot.con.lua", [
        (1900, [180_000, -1], [30_000, -1]),
        (1940, [540_000, -1], [90_000, -1]),
        (1980, [1_620_000, -1], [270_000, -1]),
    ])
    assert [t["description"]["attributes"]["cost"] for t in result] == [[180_000, -1]] * 3
    assert [t["description"]["attributes"]["maintenanceCost"] for t in result] == [[30_000, -1]] * 3


def test_templates_of_constructions_without_an_era_coefficient_are_left_alone():
    result = templated("::/stations/street/small_stops/small_new.con.lua", [(1990, [30_000, -1], [5_000, -1])])
    assert result[0]["description"]["attributes"]["cost"] == [30_000, -1]


def test_a_template_without_a_year_or_attributes_does_not_break_the_others():
    runtime, module = costs()
    table = to_lua(runtime, {"availability": {}, "constructionTemplates": [
        {"description": {}},
        {"availability": {"yearFrom": 1990}},
        {"availability": {"yearFrom": 1990}, "description": {"attributes": {"cost": [900_000, -1]}}},
    ]})
    module.normalise("::/depots/road/road_depot/road_depot.con.lua", table)
    assert from_lua(table)["constructionTemplates"][2]["description"]["attributes"]["cost"] == [100_000, -1]
