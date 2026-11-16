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


def open_contracts(contracts, done, config=CONFIG):
    runtime, notify = load_module("ap_notify")
    return from_lua(notify.open_contracts(to_lua(runtime, contracts), to_lua(runtime, done), to_lua(runtime, config)))


def reward(item="Rail Transport", to="Me", own=True):
    return {"item": item, "to": to, "own": own}


def test_the_next_contract_of_each_ladder_is_open_with_its_reward():
    contracts = {"population:1": reward(), "population:2": reward("Cargo Class: Bulk", "Alice", False),
                 "company_level:2": reward("Money Grant (small)")}
    result = open_contracts(contracts, ["population:1"])
    assert result == [
        {"key": "population:2", "title": "Contract: Population reached 2,500",
         "text": "Reward: Cargo Class: Bulk for Alice", "progress": {"kind": "population", "goal": 2500}},
        {"key": "company_level:2", "title": "Contract: Company level 2 reached", "text": "Reward: Money Grant (small)",
         "progress": {"kind": "company_level", "goal": 2}},
    ]


def test_every_first_line_is_open_but_only_the_next_delivery_tier_of_each_cargo():
    contracts = {"line:rail": reward(), "line:road": reward(), "delivered:grain:1": reward(),
                 "delivered:grain:2": reward(), "delivered:coal:2": reward()}
    keys = [c["key"] for c in open_contracts(contracts, ["delivered:coal:1"])]
    assert sorted(keys) == ["delivered:coal:2", "delivered:grain:1", "line:rail", "line:road"]


def test_no_contract_is_open_without_scouted_contracts_or_when_all_are_done():
    assert open_contracts({}, []) == []
    assert open_contracts({"population:1": reward()}, ["population:1"]) == []


def progress_spec(check, config=CONFIG):
    runtime, notify = load_module("ap_notify")
    return from_lua(notify.progress_spec(check, to_lua(runtime, config)))


def test_ladders_and_deliveries_have_a_progress_to_follow():
    assert progress_spec("population:2") == {"kind": "population", "goal": 2500}
    assert progress_spec("company_level:3") == {"kind": "company_level", "goal": 3}
    assert progress_spec("passengers:1") == {"kind": "passengers", "goal": 100}
    assert progress_spec("cargo:1") == {"kind": "cargo", "goal": 50}
    assert progress_spec("delivered:wool:2") == {"kind": "delivered", "goal": 500, "cargo": "wool"}


def test_lines_missions_and_unknown_checks_have_no_progress():
    assert progress_spec("line:rail") is None
    assert progress_spec("mission:1", {"checks": {"missions": [1]}}) is None
    assert progress_spec("population:9") is None


def test_an_open_contract_carries_its_progress_spec():
    contracts = {"delivered:wool:1": reward(), "line:rail": reward()}
    by_key = {c["key"]: c for c in open_contracts(contracts, [])}
    assert by_key["delivered:wool:1"]["progress"] == {"kind": "delivered", "goal": 100, "cargo": "wool"}
    assert "progress" not in by_key["line:rail"]


PER_CARGO_CONFIG = {"checks": {"delivery": [100], "delivery_by_cargo": {"vehicles": [20, 100], "coal": [100]}}}


def test_a_delivery_check_names_the_amount_of_its_own_cargo():
    assert texts(diff(state(), state(checks=["delivered:vehicles:1"]), PER_CARGO_CONFIG)) == ["Delivered 20 vehicles"]
    assert texts(diff(state(), state(checks=["delivered:vehicles:2"]), PER_CARGO_CONFIG)) == ["Delivered 100 vehicles"]


def test_the_progress_goal_of_a_delivery_uses_the_amount_of_its_own_cargo():
    assert progress_spec("delivered:vehicles:2", PER_CARGO_CONFIG) == {"kind": "delivered", "goal": 100, "cargo": "vehicles"}
    assert progress_spec("delivered:vehicles:1", PER_CARGO_CONFIG)["goal"] == 20


def death_message(effect):
    runtime, notify = load_module("ap_notify")
    return from_lua(notify.death_message(to_lua(runtime, effect)))


def test_a_death_message_names_who_died_and_what_it_costs():
    message = death_message({"id": 1, "amount": 1_000_000, "source": "Alice", "cause": "Alice fell into lava"})
    assert message == {"title": "Archipelago: DeathLink",
                       "text": "Alice fell into lava - the company loses 1,000,000"}


def test_a_death_message_without_a_cause_uses_the_name():
    message = death_message({"id": 1, "amount": 500_000, "source": "Alice", "cause": ""})
    assert message["text"] == "Alice died - the company loses 500,000"


def resume(current, notified):
    runtime, notify = load_module("ap_notify")
    return from_lua(notify.resume(to_lua(runtime, current), notified))


def test_resume_starts_from_the_saved_cursor_so_missed_entries_are_new():
    entries = [{"item": f"Item {i}"} for i in range(3)]
    previous = resume(log_state(entries, ["population:1"]), 1)
    assert previous["log_size"] == 1 and previous["checks"] == ["population:1"]
    assert texts(diff(previous, log_state(entries, ["population:1"]))) == ["Item 1", "Item 2"]


def test_resume_without_a_cursor_or_with_a_cursor_past_the_log_is_silent():
    current = log_state([{"item": "A"}])
    assert resume(current, None) is None
    assert resume(current, 5) is None
    assert resume(current, -1) is None
    assert resume(state(), 0) is None  # no log in the inbox: the item-count path is unchanged


def test_a_batch_above_the_limit_is_one_grouped_summary():
    entries = [{"item": "Rail Transport"}, {"item": "Rail Transport"}, {"item": "Tool: Bus Lanes"}] + \
        [{"item": f"Extra {i}"} for i in range(4)]
    messages = diff(log_state([]), log_state(entries), limit=5)
    assert messages == [{"title": "Archipelago: items received", "seconds": 30,
                         "text": "Rail Transport x2, Extra 0, Extra 1, Extra 2 and 2 more"}]


def test_exactly_the_limit_is_announced_one_by_one():
    entries = [{"item": f"Item {i}"} for i in range(5)]
    assert len(diff(log_state([]), log_state(entries), limit=5)) == 5


def test_the_summary_counts_the_same_item_from_different_players_together():
    entries = [{"item": "Rail Transport", "from": "Alice"}, {"item": "Rail Transport", "from": "Bob"}] + \
        [{"item": f"Item {i}"} for i in range(4)]
    assert texts(diff(log_state([]), log_state(entries), limit=5))[0].startswith("Rail Transport x2")


def test_the_summary_comes_before_the_check_messages():
    entries = [{"item": f"Item {i}"} for i in range(6)]
    messages = diff(log_state([]), log_state(entries, ["population:1"]), limit=5)
    assert [m["title"] for m in messages] == ["Archipelago: items received", "Archipelago: check sent"]


def test_linger_makes_catch_up_messages_last_longer_without_changing_a_set_duration():
    runtime, notify = load_module("ap_notify")
    messages = to_lua(runtime, [{"title": "A", "text": "x"}, {"title": "B", "text": "y", "seconds": 5}])
    assert [m["seconds"] for m in from_lua(notify.linger(messages))] == [30, 5]
