from lua_helpers import from_lua, load_module, to_lua


def contract(key, **extra):
    return {"key": key, "title": f"Contract: {key}", "text": "Reward: X", **extra}


def plan(open_contracts, checks, spawned, present, tick):
    runtime, sync = load_module("ap_contract_sync")
    state = to_lua(runtime, spawned)
    result = sync.plan(to_lua(runtime, open_contracts), to_lua(runtime, checks), state, to_lua(runtime, present), tick)
    return from_lua(result), from_lua(state)


def keys(actions):
    return [a["key"] for a in actions]


def test_an_open_contract_with_no_subvention_is_spawned_with_a_stable_uid():
    first, state = plan([contract("population:1")], [], {}, [], tick=1)
    assert keys(first["spawn"]) == ["population:1"]
    uid = first["spawn"][0]["uid"]
    assert state["population:1"]["uid"] == uid
    other, _ = plan([contract("population:1")], [], {}, [], tick=1)
    assert other["spawn"][0]["uid"] == uid


def test_a_pending_spawn_is_not_repeated_before_the_game_lists_it():
    _, state = plan([contract("population:1")], [], {}, [], tick=1)
    again, _ = plan([contract("population:1")], [], state, [], tick=2)
    assert again["spawn"] == []


def test_a_spawn_the_game_never_listed_is_retried_after_a_while_with_a_new_uid():
    first, state = plan([contract("population:1")], [], {}, [], tick=1)
    late, _ = plan([contract("population:1")], [], state, [], tick=20)
    assert keys(late["spawn"]) == ["population:1"]
    assert late["spawn"][0]["uid"] != first["spawn"][0]["uid"]


def test_a_declined_contract_comes_back_with_a_new_uid():
    first, state = plan([contract("population:1")], [], {}, [], tick=1)
    uid = first["spawn"][0]["uid"]
    _, state = plan([contract("population:1")], [], state, [uid], tick=2)  # the game lists it
    back, _ = plan([contract("population:1")], [], state, [], tick=3)      # then it is gone: declined
    assert keys(back["spawn"]) == ["population:1"] and back["spawn"][0]["uid"] != uid


def test_a_listed_contract_is_left_alone():
    first, state = plan([contract("population:1")], [], {}, [], tick=1)
    uid = first["spawn"][0]["uid"]
    result, _ = plan([contract("population:1")], [], state, [uid], tick=2)
    assert not any(result.values())


def test_a_reached_check_is_accepted_then_reported_on_the_next_tick():
    first, state = plan([contract("population:1")], [], {}, [], tick=1)
    uid = first["spawn"][0]["uid"]
    accept, state = plan([], ["population:1"], state, [uid], tick=2)
    assert keys(accept["accept"]) == ["population:1"] and accept["reached"] == []
    reached, state = plan([], ["population:1"], state, [uid], tick=3)
    assert keys(reached["reached"]) == ["population:1"] and reached["accept"] == []
    done, _ = plan([], ["population:1"], state, [uid], tick=4)
    assert not done.get("accept") and not done.get("reached")


def test_a_reached_check_that_was_never_spawned_needs_nothing():
    result, _ = plan([], ["population:1"], {}, [], tick=1)
    assert not result.get("accept") and not result.get("reached") and not result.get("spawn")
