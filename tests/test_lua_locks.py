from lua_helpers import from_lua, load_module, to_lua

CATALOG = {
    "eras": {"B": 1920, "C": 1960},
    "modes": {
        "road": {"menu": ["::/depots/road/road_depot/road_depot.con@0"], "vehicles": [
            {"path": "::/vehicle/bus/a.mdl", "year": 1890},
            {"path": "::/vehicle/bus/b.mdl", "year": 1930},
            {"path": "::/vehicle/bus/c.mdl", "year": 1970},
        ]},
        "rail": {"menu": ["::/depots/rail/rail_depot.con@0", "::/depots/rail/rail_depot.con@1"], "vehicles": [
            {"path": "::/vehicle/train/a.mdl", "year": 1885},
            {"path": "::/vehicle/train/b.mdl", "year": 1925},
            {"path": "::/vehicle/train/c.mdl", "year": 1965},
        ]},
        "tram": {"menu": ["::/depots/road/tram_depot/tram_depot.con@0"], "vehicles": []},
    },
}


def compute(items, catalog=CATALOG):
    runtime, locks = load_module("ap_locks")
    result = locks.compute_locks(to_lua(runtime, items), to_lua(runtime, catalog))
    return from_lua(result["menu"]), from_lua(result["vehicles"])


def test_unreceived_mode_locks_menu_and_vehicles():
    menu, vehicles = compute({})
    assert "::/depots/rail/rail_depot.con@0" in menu
    assert "::/depots/road/tram_depot/tram_depot.con@0" in menu
    assert "::/vehicle/train/a.mdl" in vehicles


def test_received_mode_unlocks_menu():
    menu, _ = compute({"Rail Transport": 1})
    assert "::/depots/rail/rail_depot.con@0" not in menu
    assert "::/depots/road/tram_depot/tram_depot.con@0" in menu


def test_vehicle_tiers_follow_progressive_count():
    base = {"Rail Transport": 1}
    _, none = compute({**base})
    _, one = compute({**base, "Progressive Rail Vehicles": 1})
    _, two = compute({**base, "Progressive Rail Vehicles": 2})
    assert "::/vehicle/train/a.mdl" not in none
    assert "::/vehicle/train/b.mdl" in none and "::/vehicle/train/c.mdl" in none
    assert "::/vehicle/train/b.mdl" not in one and "::/vehicle/train/c.mdl" in one
    assert not [path for path in two if "train" in path]


def test_road_is_unlocked_at_start_but_later_tiers_are_not():
    menu, vehicles = compute({})
    assert "::/depots/road/road_depot/road_depot.con@0" not in menu
    assert "::/vehicle/bus/a.mdl" not in vehicles
    assert "::/vehicle/bus/b.mdl" in vehicles and "::/vehicle/bus/c.mdl" in vehicles
    _, with_items = compute({"Progressive Road Vehicles": 2})
    assert not [path for path in with_items if "bus" in path]


def test_lists_have_no_duplicates_and_are_sorted():
    catalog = {
        "eras": {"B": 1920, "C": 1960},
        "modes": {
            "rail": {"menu": ["x@1", "x@0"], "vehicles": [{"path": "v", "year": 1900}]},
            "tram": {"menu": ["x@0", "y"], "vehicles": [{"path": "v", "year": 1900}]},
        },
    }
    menu, vehicles = compute({}, catalog)
    assert menu == ["x@0", "x@1", "y"]
    assert vehicles == ["v"]


def test_unknown_item_is_ignored():
    assert compute({"Mystery Item": 3}) == compute({})


def test_vehicle_without_year_counts_as_first_tier():
    catalog = {"eras": {"B": 1920, "C": 1960}, "modes": {"rail": {"menu": [], "vehicles": [{"path": "v"}]}}}
    _, vehicles = compute({"Rail Transport": 1}, catalog)
    assert vehicles == []


def test_deep_equal():
    runtime, locks = load_module("ap_locks")
    same = locks.deep_equal(to_lua(runtime, {"a": ["x", "y"], "b": {"c": 1}}), to_lua(runtime, {"a": ["x", "y"], "b": {"c": 1}}))
    other = locks.deep_equal(to_lua(runtime, {"a": ["x", "y"]}), to_lua(runtime, {"a": ["x", "z"]}))
    assert same is True and other is False


TYPES_CATALOG = {
    "eras": {"B": 1920, "C": 1960},
    "modes": {
        "road": {"menu": [], "vehicles": [], "type_item": "Progressive Road Types", "types": [
            {"tag": "street_old", "year": 0}, {"tag": "street_town", "year": 1910},
            {"tag": "street_new", "year": 1940}, {"tag": "highway", "year": 1980},
        ]},
        "rail": {"menu": ["rail_depot"], "vehicles": [], "type_item": "Progressive Rail Tracks", "types": [
            {"tag": "track_simple", "year": 0}, {"tag": "track_standard", "year": 1930},
            {"tag": "track_fast", "year": 1980},
        ]},
    },
}


def test_road_types_follow_the_progressive_road_types_item():
    none, _ = compute({}, TYPES_CATALOG)
    one, _ = compute({"Progressive Road Types": 1}, TYPES_CATALOG)
    two, _ = compute({"Progressive Road Types": 2}, TYPES_CATALOG)
    assert [t for t in none if t.startswith("street") or t == "highway"] == ["highway", "street_new"]
    assert [t for t in one if t.startswith("street") or t == "highway"] == ["highway"]
    assert not [t for t in two if t.startswith("street") or t == "highway"]


def test_rail_tracks_stay_locked_with_the_rail_mode_then_follow_their_item():
    locked, _ = compute({}, TYPES_CATALOG)
    assert {"track_simple", "track_standard", "track_fast", "rail_depot"} <= set(locked)
    with_mode, _ = compute({"Rail Transport": 1}, TYPES_CATALOG)
    assert "track_simple" not in with_mode and "rail_depot" not in with_mode
    assert "track_standard" in with_mode and "track_fast" in with_mode
    one, _ = compute({"Rail Transport": 1, "Progressive Rail Tracks": 1}, TYPES_CATALOG)
    assert "track_standard" not in one and "track_fast" in one
    two, _ = compute({"Rail Transport": 1, "Progressive Rail Tracks": 2}, TYPES_CATALOG)
    assert not [t for t in two if t.startswith("track")]


def test_a_types_entry_without_an_item_name_only_allows_the_first_tier():
    catalog = {"eras": {"B": 1920, "C": 1960}, "modes": {"road": {"menu": [], "vehicles": [], "types": [
        {"tag": "a", "year": 0}, {"tag": "b", "year": 1940}]}}}
    menu, _ = compute({"Progressive Road Types": 2}, catalog)
    assert menu == ["b"]


def test_type_tags_are_merged_without_duplicates_with_the_mode_menu():
    catalog = {"eras": {"B": 1920, "C": 1960}, "modes": {"rail": {"menu": ["x", "t"], "vehicles": [],
        "type_item": "Progressive Rail Tracks", "types": [{"tag": "t", "year": 0}, {"tag": "x", "year": 1980}]}}}
    menu, _ = compute({}, catalog)
    assert menu == ["t", "x"]


TOOLS_CATALOG = {
    "eras": {"B": 1920, "C": 1960},
    "modes": {
        "road": {"menu": [], "vehicles": [], "tools": [
            {"item": "Tool: Bus Lanes", "tags": ["bus_lane_tool"]},
            {"item": "Tool: Noise Barriers", "tags": ["barrier_a", "barrier_b"]},
        ]},
        "rail": {"menu": ["rail_depot"], "vehicles": [], "tools": [
            {"item": "Tool: Rail Signals", "tags": ["signal_a"]},
            {"item": "Tool: Electrification", "tags": ["electrify"]},
        ]},
    },
}


def test_a_tool_is_locked_until_its_item_is_received():
    menu, _ = compute({}, TOOLS_CATALOG)
    assert {"bus_lane_tool", "barrier_a", "barrier_b"} <= set(menu)
    menu, _ = compute({"Tool: Bus Lanes": 1}, TOOLS_CATALOG)
    assert "bus_lane_tool" not in menu and "barrier_a" in menu


def test_a_tool_of_a_locked_mode_stays_locked_even_with_its_item():
    menu, _ = compute({"Tool: Rail Signals": 1}, TOOLS_CATALOG)
    assert "signal_a" in menu  # the rail mode is not unlocked
    menu, _ = compute({"Tool: Rail Signals": 1, "Rail Transport": 1}, TOOLS_CATALOG)
    assert "signal_a" not in menu and "electrify" in menu and "rail_depot" not in menu


def test_tool_tags_are_merged_without_duplicates():
    catalog = {"eras": {"B": 1920, "C": 1960}, "modes": {"road": {"menu": ["t"], "vehicles": [], "tools": [
        {"item": "Tool: Bus Lanes", "tags": ["t", "u"]}]}}}
    menu, _ = compute({}, catalog)
    assert menu == ["t", "u"]


def vehicle(path, classes, year=1900):
    return {"path": path, "year": year, "classes": classes}


CLASS_CATALOG = {
    "eras": {"B": 1920, "C": 1960},
    "modes": {
        "road": {"menu": [], "vehicles": [
            vehicle("bulk_truck", ["BULK"]),
            vehicle("goods_truck", ["GOODS"]),
            vehicle("universal_truck", ["UNIVERSAL"]),
            vehicle("coach", ["PASSENGERS"]),
            vehicle("mixed", ["PASSENGERS", "UNIVERSAL"]),
            vehicle("loco", []),
            vehicle("old_style", None),
            vehicle("multi_ship", ["BULK", "FLATBED", "GOODS"]),
        ]},
    },
}


def test_specialised_freight_vehicles_wait_for_their_class_item():
    _, vehicles = compute({}, CLASS_CATALOG)
    assert {"bulk_truck", "goods_truck", "multi_ship"} <= set(vehicles)
    _, vehicles = compute({"Cargo Class: Bulk": 1}, CLASS_CATALOG)
    assert "bulk_truck" not in vehicles and "goods_truck" in vehicles


def test_a_vehicle_with_several_classes_is_released_by_any_of_them():
    for item in ("Cargo Class: Bulk", "Cargo Class: Flatbed", "Cargo Class: Goods"):
        _, vehicles = compute({item: 1}, CLASS_CATALOG)
        assert "multi_ship" not in vehicles, item
    _, vehicles = compute({"Cargo Class: Liquid": 1}, CLASS_CATALOG)
    assert "multi_ship" in vehicles


def test_universal_passenger_and_cargo_less_vehicles_are_never_class_gated():
    _, vehicles = compute({}, CLASS_CATALOG)
    assert not {"universal_truck", "coach", "mixed", "loco", "old_style"} & set(vehicles)


def test_a_class_item_does_not_bypass_the_year_tier_or_the_mode():
    catalog = {"eras": {"B": 1920, "C": 1960}, "modes": {
        "road": {"menu": [], "vehicles": [vehicle("late_bulk", ["BULK"], year=1970)]},
        "rail": {"menu": [], "vehicles": [vehicle("rail_bulk", ["BULK"], year=1900)]},
    }}
    _, vehicles = compute({"Cargo Class: Bulk": 1}, catalog)
    assert "late_bulk" in vehicles  # tier C still waits for its progressive items
    assert "rail_bulk" in vehicles  # the rail mode is still locked
    _, vehicles = compute({"Cargo Class: Bulk": 1, "Rail Transport": 1, "Progressive Road Vehicles": 2}, catalog)
    assert not vehicles


VARIANTS_CATALOG = {
    "eras": {"B": 1920, "C": 1960},
    "modes": {
        "road": {"menu": [], "vehicles": [], "variants": [
            {"tag": "depot@0", "year": 1900}, {"tag": "depot@1", "year": 1940}, {"tag": "depot@2", "year": 1980},
        ]},
        "rail": {"menu": ["rail_depot@0"], "vehicles": [], "variants": [
            {"tag": "rail_depot@0", "year": 1900}, {"tag": "rail_depot@1", "year": 1960},
        ]},
    },
}


def test_the_era_variants_of_a_building_follow_the_vehicle_tiers():
    menu, _ = compute({}, VARIANTS_CATALOG)
    assert "depot@0" not in menu and "depot@1" in menu and "depot@2" in menu
    menu, _ = compute({"Progressive Road Vehicles": 1}, VARIANTS_CATALOG)
    assert "depot@1" not in menu and "depot@2" in menu
    menu, _ = compute({"Progressive Road Vehicles": 2}, VARIANTS_CATALOG)
    assert not [tag for tag in menu if tag.startswith("depot")]


def test_the_variants_of_a_locked_mode_stay_locked_whatever_the_tier():
    menu, _ = compute({"Progressive Rail Vehicles": 2}, VARIANTS_CATALOG)
    assert "rail_depot@0" in menu and "rail_depot@1" in menu
    menu, _ = compute({"Rail Transport": 1}, VARIANTS_CATALOG)
    assert "rail_depot@0" not in menu and "rail_depot@1" in menu
