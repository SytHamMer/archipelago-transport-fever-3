from lua_helpers import from_lua, load_module, to_lua

CONFIG = {
    "checks": {
        "population": [500, 2500], "company_level": [2, 3], "passengers": [100], "cargo": [50],
        "first_line": True, "delivery": [100, 500],
    },
}


def state(items=None, checks=None):
    return {"items": items or {}, "checks": checks or []}


def diff(previous, current, config=CONFIG, limit=None):
    runtime, notify = load_module("ap_notify")
    prev = None if previous is None else to_lua(runtime, previous)
    result = notify.diff(prev, to_lua(runtime, current), to_lua(runtime, config), limit) if limit else \
        notify.diff(prev, to_lua(runtime, current), to_lua(runtime, config))
    return from_lua(result)


def texts(messages):
    return [m["text"] for m in messages]


def test_the_first_state_notifies_nothing():
    assert diff(None, state({"Rail Transport": 1}, ["population:1"])) == []


def test_an_unchanged_state_notifies_nothing():
    same = state({"Rail Transport": 1}, ["population:1"])
    assert diff(same, same) == []


def test_a_new_item_gives_an_item_message():
    messages = diff(state(), state({"Rail Transport": 1}))
    assert messages == [{"title": "Archipelago: item received", "text": "Rail Transport"}]


def test_several_copies_of_an_item_show_the_count():
    messages = diff(state({"Money Grant (small)": 1}), state({"Money Grant (small)": 3}))
    assert texts(messages) == ["Money Grant (small) x2"]


def test_new_checks_have_readable_texts():
    reached = ["population:2", "company_level:3", "passengers:1", "cargo:1", "line:rail", "delivered:grain:2"]
    messages = diff(state(), state(checks=reached), limit=10)
    assert {m["title"] for m in messages} == {"Archipelago: check sent"}
    assert sorted(texts(messages)) == sorted([
        "Population reached 2,500",
        "Company level 3 reached",
        "Passengers transported: 100",
        "Cargo transported: 50",
        "First rail line built",
        "Delivered 500 grain",
    ])


def test_underscores_in_cargo_names_become_spaces():
    assert texts(diff(state(), state(checks=["delivered:iron_ore:1"]))) == ["Delivered 100 iron ore"]


def test_an_unknown_check_is_shown_by_its_id_without_failing():
    assert texts(diff(state(), state(checks=["mystery:9", "population:9"]))) == [
        "Check reached: mystery:9", "Check reached: population:9",
    ]


def test_items_come_before_checks():
    messages = diff(state(), state({"Rail Transport": 1}, ["population:1"]))
    assert [m["title"] for m in messages] == ["Archipelago: item received", "Archipelago: check sent"]


def test_too_many_messages_are_summed_up_within_the_limit():
    reached = [f"population:{i}" for i in range(1, 8)]
    config = {"checks": {**CONFIG["checks"], "population": [100 * i for i in range(1, 8)]}}
    messages = diff(state(), state(checks=reached), config, limit=5)
    assert len(messages) == 5
    assert texts(messages)[-1] == "and 3 more"
    assert messages[-1]["title"] == "Archipelago"


def test_at_the_limit_nothing_is_summed_up():
    reached = [f"population:{i}" for i in range(1, 6)]
    config = {"checks": {**CONFIG["checks"], "population": [100 * i for i in range(1, 6)]}}
    assert len(diff(state(), state(checks=reached), config, limit=5)) == 5
    assert "more" not in texts(diff(state(), state(checks=reached), config, limit=5))[-1]


def test_a_check_that_disappears_does_not_notify():
    assert diff(state(checks=["population:1"]), state(checks=[])) == []


def test_a_missing_config_is_safe():
    runtime, notify = load_module("ap_notify")
    result = notify.diff(to_lua(runtime, state()), to_lua(runtime, state(checks=["population:1"])), None)
    assert texts(from_lua(result)) == ["Check reached: population:1"]


def log_state(entries, checks=None):
    return {"items": {}, "checks": checks or [], "log": entries, "log_size": len(entries)}


def test_new_log_entries_name_the_sender_and_the_source():
    first = {"item": "Rail Transport", "from": "Alice", "where": "Alice's chest"}
    second = {"item": "Tram Transport", "from": "Bob", "where": "Boss kill"}
    messages = diff(log_state([first]), log_state([first, second]))
    assert messages == [{"title": "Archipelago: item received", "text": "Tram Transport from Bob (Boss kill)"}]


def test_own_checks_are_described_with_the_readable_check_text():
    entry = {"item": "Rail Transport", "own": True, "where": "population:2"}
    messages = diff(log_state([]), log_state([entry]))
    assert texts(messages) == ["Rail Transport (Population reached 2,500)"]


def test_a_log_entry_without_a_source_shows_the_sender_only():
    entry = {"item": "Rail Transport", "from": "Archipelago"}
    assert texts(diff(log_state([]), log_state([entry]))) == ["Rail Transport from Archipelago"]


def test_the_log_replaces_the_item_counts_so_nothing_is_announced_twice():
    entry = {"item": "Rail Transport", "from": "Alice", "where": "chest"}
    previous = {"items": {}, "checks": [], "log": [], "log_size": 0}
    current = {"items": {"Rail Transport": 1}, "checks": [], "log": [entry], "log_size": 1}
    assert len(diff(previous, current)) == 1


def test_a_log_state_after_the_first_one_stays_silent_at_the_baseline():
    entry = {"item": "Rail Transport", "from": "Alice", "where": "chest"}
    assert diff(None, log_state([entry])) == []


def diff_with_contracts(previous, current, contracts):
    runtime, notify = load_module("ap_notify")
    result = notify.diff(to_lua(runtime, previous), to_lua(runtime, current), to_lua(runtime, CONFIG), 5,
                         to_lua(runtime, contracts))
    return from_lua(result)


def test_a_contract_with_its_reward_is_announced_with_the_reward():
    contracts = {"population:1": {"item": "Rail Transport", "to": "Me", "own": True}}
    messages = diff_with_contracts(state(), state(checks=["population:1"]), contracts)
    assert messages == [{"title": "Archipelago: contract completed",
                         "text": "Population reached 500 - reward: Rail Transport"}]


def test_a_reward_for_another_player_names_them():
    contracts = {"population:1": {"item": "Cargo Class: Bulk", "to": "Alice", "own": False}}
    messages = diff_with_contracts(state(), state(checks=["population:1"]), contracts)
    assert messages[0]["text"] == "Population reached 500 - reward: Cargo Class: Bulk for Alice"


def test_a_check_without_a_known_contract_keeps_the_plain_message():
    messages = diff_with_contracts(state(), state(checks=["population:1"]), {})
    assert messages == [{"title": "Archipelago: check sent", "text": "Population reached 500"}]


def test_a_mission_check_has_a_readable_text():
    config = {"checks": {"missions": [1, 2, 3]}}
    assert texts(diff(state(), state(checks=["mission:3"]), config)) == ["Missions completed: 3"]
