from lua_helpers import from_lua, load_module, to_lua

EFFECTS = [
    {"id": 1, "kind": "money", "amount": 50000},
    {"id": 2, "kind": "money_loss", "amount": 100000},
    {"id": 4, "kind": "loan", "amount": 0},
]


def pending(effects, applied):
    runtime, module = load_module("ap_effects")
    return from_lua(module.pending(to_lua(runtime, effects), applied))


def granted(items, earned):
    runtime, module = load_module("ap_effects")
    return module.granted_level(to_lua(runtime, items), earned)


def test_pending_skips_applied():
    assert [e["id"] for e in pending(EFFECTS, 1)] == [2, 4]


def test_pending_is_ordered_by_id():
    shuffled = [EFFECTS[2], EFFECTS[0], EFFECTS[1]]
    assert [e["id"] for e in pending(shuffled, 0)] == [1, 2, 4]


def test_replaying_the_same_inbox_applies_nothing_new():
    assert pending(EFFECTS, 4) == []


def test_empty_or_missing_effects_are_safe():
    assert pending([], 0) == []
    runtime, module = load_module("ap_effects")
    assert from_lua(module.pending(None, 0)) == []


def test_granted_level_adds_one_per_item_to_the_starting_level():
    assert granted({"Company Level +1": 3}, 1) == 4


def test_granted_level_is_never_below_earned_level():
    assert granted({"Company Level +1": 1}, 6) == 6
    assert granted({}, 3) == 3


def test_granted_level_is_capped():
    assert granted({"Company Level +1": 99}, 1) == 15


def test_granted_level_with_no_items_is_the_earned_level():
    assert granted({}, 1) == 1
    assert granted(None, 2) == 2
