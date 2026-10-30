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
