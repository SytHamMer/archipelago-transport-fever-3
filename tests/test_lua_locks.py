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
