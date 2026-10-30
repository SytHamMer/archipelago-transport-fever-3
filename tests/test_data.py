import json
from pathlib import Path

from transport_fever_3 import data

CONTRACT = Path(__file__).resolve().parent.parent / "contract" / "constants.json"


def test_spread_is_strictly_increasing_with_exact_bounds():
    values = data.spread(8, 500, 20000)
    assert len(values) == 8
    assert values[0] == 500 and values[-1] == 20000
    assert all(a < b for a, b in zip(values, values[1:]))


def test_spread_single_step_is_first():
    assert data.spread(1, 500, 20000) == [500]


def test_spread_equal_bounds_still_strictly_increasing():
    values = data.spread(3, 100, 100)
    assert len(values) == 3
    assert all(a < b for a, b in zip(values, values[1:]))


def test_spread_inverted_bounds_does_not_crash():
    values = data.spread(4, 5000, 100)
    assert len(values) == 4
    assert all(a < b for a, b in zip(values, values[1:]))


def test_spread_zero_count_is_empty():
    assert data.spread(0, 1, 2) == []


def test_item_names():
    assert data.ITEM_MODE("Rail") == "Rail Transport"
    assert data.ITEM_VEHICLES("Road") == "Progressive Road Vehicles"
    assert data.ITEM_VEHICLES("Air") == "Progressive Air Vehicles"
    assert data.ITEM_LEVEL == "Company Level +1"


def test_location_id_format():
    assert data.location_id("population", 3) == "population:3"
    assert data.location_id("line", "rail") == "line:rail"
    assert data.location_id("delivered", "grain", 2) == "delivered:grain:2"


def test_cargos_are_unique_lowercase_game_ids():
    assert len(data.CARGOS) == 28
    assert len(set(data.CARGOS)) == 28
    assert all(name == name.lower() and " " not in name for name in data.CARGOS)


def test_constants_match_contract():
    assert json.loads(CONTRACT.read_text(encoding="utf-8")) == data.contract()


def test_era_starts_are_increasing():
    assert data.ERA_STARTS == {"B": 1920, "C": 1960}
    assert data.ERA_STARTS["B"] < data.ERA_STARTS["C"]


def test_minimum_start_year_is_late_enough_for_every_era():
    assert data.MIN_START_YEAR == 2000
    assert data.MIN_START_YEAR > data.ERA_STARTS["C"]


def test_traps_are_money_losses_in_two_sizes_and_the_loan_is_gone():
    assert data.TRAPS == {"Money Loss (small)": 50_000, "Money Loss (medium)": 250_000}
    assert len(data.TRAP_WEIGHTS) == len(data.TRAPS)
    assert data.TRAP_WEIGHTS[0] > data.TRAP_WEIGHTS[1]  # the small loss is the common one
    assert "Forced Loan" not in data.TRAPS
