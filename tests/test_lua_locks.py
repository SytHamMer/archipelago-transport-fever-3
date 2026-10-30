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
