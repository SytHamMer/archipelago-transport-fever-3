from lua_helpers import from_lua, load_module, to_lua

EFFECTS = [
    {"id": 1, "kind": "money", "amount": 50000},
    {"id": 2, "kind": "money_loss", "amount": 100000},
    {"id": 4, "kind": "money_loss", "amount": 250000},
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


def test_failures_are_counted_per_effect_and_skip_after_the_limit():
    runtime, module = load_module("ap_effects")
    failures = runtime.table_from({})
    skipped = [module.register_failure(failures, 7) for _ in range(module.MAX_FAILURES)]
    assert skipped == [False] * (module.MAX_FAILURES - 1) + [True]
    assert module.register_failure(failures, 8) is False  # another effect starts from zero


def inflation(year):
    runtime, effects = load_module("ap_effects")
    return effects.inflation(year)


def scaled(amount, year):
    runtime, effects = load_module("ap_effects")
    return effects.scale_money(amount, year)


def test_inflation_goes_from_one_in_1900_to_six_in_2020_exponentially():
    assert inflation(1900) == 1
    assert abs(inflation(2020) - 6) < 1e-9
    assert abs(inflation(1960) - 6 ** 0.5) < 1e-9


def test_inflation_is_clamped_outside_the_years_the_game_scales():
    assert inflation(1850) == 1 and inflation(1000) == 1
    assert abs(inflation(2100) - 6) < 1e-9


def test_a_missing_year_means_no_inflation():
    assert inflation(None) == 1


def test_a_money_amount_follows_the_inflation_and_is_rounded_to_a_thousand():
    assert scaled(50_000, 1900) == 50_000
    assert scaled(50_000, 2020) == 300_000
    assert scaled(250_000, 1960) == 612_000  # 250,000 x 2.449 rounded to a thousand


def test_a_small_amount_never_rounds_to_zero():
    assert scaled(100, 1900) == 1_000
