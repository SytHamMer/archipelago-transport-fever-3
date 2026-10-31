from lua_helpers import load_module


def scale(amount, percent):
    _, loans = load_module("ap_loans")
    return loans.scale_amount(amount, percent)


def test_an_amount_is_scaled_by_the_percentage_and_rounded_to_a_thousand():
    assert scale(12_000_000, 10) == 1_200_000
    assert scale(23_456_789, 10) == 2_346_000


def test_a_hundred_percent_keeps_the_game_amount_and_the_result_is_never_zero():
    assert scale(36_000_000, 100) == 36_000_000
    assert scale(100_000, 1) == 1_000


def test_a_missing_or_invalid_scale_keeps_the_amount():
    _, loans = load_module("ap_loans")
    assert loans.scale_amount(5_000_000, None) == 5_000_000
    assert loans.scale_amount(5_000_000, 0) == 5_000_000
