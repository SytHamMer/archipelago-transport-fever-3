from lua_helpers import from_lua, load_module, to_lua

CONFIG = {
    "goals": {"population": 2500, "company_level": 0, "passengers": 0, "cargo": 0},
    "checks": {
        "population": [500, 1000], "company_level": [2, 3], "passengers": [100, 200], "cargo": [50],
        "first_line": True, "delivery": [100, 500],
    },
}


def evaluate(readings, config=CONFIG):
    runtime, checks = load_module("ap_checks")
    result = checks.evaluate(to_lua(runtime, config), to_lua(runtime, readings))
    return from_lua(result["checks"]), from_lua(result["goals"])


def test_population_thresholds_use_experience():
    assert "population:1" not in evaluate({"experience": 499})[0]
    reached, _ = evaluate({"experience": 500})
    assert "population:1" in reached and "population:2" not in reached
    assert "population:2" in evaluate({"experience": 1000})[0]


def test_company_level_ids_use_the_level_number():
    reached, _ = evaluate({"earned_level": 2})
    assert "company_level:2" in reached and "company_level:3" not in reached
    assert not [c for c in reached if c.startswith("company_level:1")]


def test_passengers_and_cargo_ladders():
    reached, _ = evaluate({"passengers": 150, "cargo": 50})
    assert "passengers:1" in reached and "passengers:2" not in reached
    assert "cargo:1" in reached


def test_line_modes_map_to_check_ids():
    cases = {2: "line:road", 3: "line:road", 4: "line:road", 5: "line:tram", 6: "line:tram", 7: "line:rail",
             8: "line:rail", 9: "line:air", 11: "line:air", 13: "line:air", 10: "line:water", 12: "line:water"}
    for index, expected in cases.items():
        reached, _ = evaluate({"line_modes": {index: True}})
        assert [c for c in reached if c.startswith("line:")] == [expected], index
    assert not [c for c in evaluate({"line_modes": {}})[0] if c.startswith("line:")]


def test_person_and_cargo_modes_are_not_lines():
    reached, _ = evaluate({"line_modes": {0: True, 1: True}})
    assert not [c for c in reached if c.startswith("line:")]


def test_first_line_checks_can_be_disabled():
    config = {**CONFIG, "checks": {**CONFIG["checks"], "first_line": False}}
    assert not [c for c in evaluate({"line_modes": {3: True}}, config)[0] if c.startswith("line:")]


def test_delivery_tiers_per_cargo():
    reached, _ = evaluate({"delivered": {"grain": 600, "coal": 50}})
    assert "delivered:grain:1" in reached and "delivered:grain:2" in reached
    assert not [c for c in reached if c.startswith("delivered:coal")]


def test_only_active_goals_are_reported_and_all_are_evaluated():
    _, goals = evaluate({"experience": 2500})
    assert goals == {"population": True}
    config = {**CONFIG, "goals": {"population": 2500, "company_level": 0, "passengers": 100, "cargo": 0}}
    _, goals = evaluate({"experience": 2500, "passengers": 99}, config)
    assert goals == {"population": True, "passengers": False}


def test_missing_readings_are_safe():
    reached, goals = evaluate({})
    assert reached == [] and goals == {"population": False}


def test_results_are_sorted():
    reached, _ = evaluate({"experience": 5000, "passengers": 500, "line_modes": {3: True, 7: True}})
    assert reached == sorted(reached)


def test_merge_never_shrinks():
    runtime, checks = load_module("ap_checks")
    merged = checks.merge_monotonic(to_lua(runtime, ["population:2", "line:road"]), to_lua(runtime, ["line:road", "cargo:1"]))
    assert from_lua(merged) == ["cargo:1", "line:road", "population:2"]


def test_experience_dropping_does_not_remove_checks_after_merge():
    runtime, checks = load_module("ap_checks")
    first, _ = evaluate({"experience": 1000})
    later, _ = evaluate({"experience": 100})
    merged = from_lua(checks.merge_monotonic(to_lua(runtime, first), to_lua(runtime, later)))
    assert "population:2" in merged


def test_goals_stay_reached_once_they_were():
    runtime, checks = load_module("ap_checks")
    merged = checks.merge_goals(to_lua(runtime, {"population": True}), to_lua(runtime, {"population": False, "passengers": True}))
    assert from_lua(merged) == {"population": True, "passengers": True}


def test_merge_goals_is_safe_with_nothing_before_or_nothing_now():
    runtime, checks = load_module("ap_checks")
    assert from_lua(checks.merge_goals(None, to_lua(runtime, {"population": False}))) == {"population": False}
    assert from_lua(checks.merge_goals(to_lua(runtime, {"population": True}), None)) == {"population": True}


def test_mission_checks_use_the_number_of_completed_missions():
    config = {"goals": {}, "checks": {"missions": [1, 2, 3]}}
    assert evaluate({"missions": 2}, config)[0] == ["mission:1", "mission:2"]
    assert evaluate({}, config)[0] == []


def merge_missions(previous, current):
    runtime, checks = load_module("ap_checks")
    return from_lua(checks.merge_missions(to_lua(runtime, previous), to_lua(runtime, current)))


def test_completed_missions_are_remembered_once_by_uid():
    assert merge_missions([5, 7], [7, 9]) == [5, 7, 9]
    assert merge_missions([], []) == []


def test_a_mission_that_leaves_the_game_list_is_still_counted():
    assert merge_missions([5, 7], []) == [5, 7]


def foreign_mission_uids(entries):
    runtime, checks = load_module("ap_checks")
    return from_lua(checks.foreign_mission_uids(to_lua(runtime, entries)))


def test_the_missions_of_the_game_are_counted_but_not_our_own_contracts():
    entries = [
        {"id": "::/game_mechanics/subventions/deliver_passengers/deliver_passengers.res", "uid": 11},
        {"id": "archipelago_tf3_1::/ap_subvention.res", "uid": 3905751701},
        {"id": "::/game_mechanics/subventions/deliver_cargo/deliver_cargo.res", "uid": 12},
    ]
    assert foreign_mission_uids(entries) == [11, 12]


def test_entries_without_a_uid_or_an_id_are_skipped():
    assert foreign_mission_uids([{"id": "x"}, {"uid": 5}, {"id": "y", "uid": "bad"}]) == []


def format_supported(version, supported=1):
    runtime, checks = load_module("ap_checks")
    return checks.format_supported(version, supported)


def test_an_inbox_format_the_mod_understands_is_supported():
    assert format_supported(1) is True and format_supported(0) is True


def test_a_newer_or_missing_or_invalid_inbox_format_is_not_supported():
    assert format_supported(2) is False
    assert format_supported(None) is False
    assert format_supported("1") is False


PER_CARGO = {
    "goals": {}, "checks": {"delivery": [100, 500], "delivery_by_cargo": {"coal": [100, 500], "vehicles": [20, 100]}},
}


def test_deliveries_use_the_amounts_of_their_own_cargo():
    reached, _ = evaluate({"delivered": {"coal": 150, "vehicles": 150}}, PER_CARGO)
    assert "delivered:coal:1" in reached and "delivered:coal:2" not in reached
    assert "delivered:vehicles:1" in reached and "delivered:vehicles:2" in reached


def test_a_cargo_without_checks_in_the_per_cargo_table_has_no_delivery_check():
    reached, _ = evaluate({"delivered": {"fish": 99999}}, PER_CARGO)
    assert not [check for check in reached if check.startswith("delivered:")]


def test_without_a_per_cargo_table_the_shared_list_still_applies():
    reached, _ = evaluate({"delivered": {"fish": 600}})
    assert "delivered:fish:1" in reached and "delivered:fish:2" in reached
