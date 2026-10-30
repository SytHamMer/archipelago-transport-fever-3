from helpers import make_options

from transport_fever_3 import data
from transport_fever_3.Items import item_counts, item_table
from transport_fever_3.Locations import active_locations, location_table
from transport_fever_3.Options import TF3Options


def opts(**overrides):
    return make_options(TF3Options, **overrides)


def test_default_item_counts():
    counts = item_counts(opts())
    assert counts["Rail Transport"] == 1
    assert counts["Progressive Road Vehicles"] == 2
    assert counts[data.ITEM_LEVEL] == 4
    assert "Road Transport" not in counts


def test_level_items_follow_company_level_checks():
    assert item_counts(opts(company_level_checks=0)).get(data.ITEM_LEVEL, 0) == 0
    assert item_counts(opts(company_level_checks=9))[data.ITEM_LEVEL] == 9


def test_every_counted_item_is_in_the_item_table():
    assert set(item_counts(opts())) <= set(item_table)
    assert set(data.MONEY_ITEMS) | set(data.TRAPS) <= set(item_table)


def test_default_locations():
    locations = active_locations(opts())
    assert "population:1" in locations and "population:4" in locations
    assert "population:5" not in locations
    assert "company_level:2" in locations and "company_level:5" in locations
    assert "company_level:6" not in locations
    assert "line:rail" in locations and "line:road" in locations
    assert "delivered:grain:1" in locations
    assert "delivered:grain:2" not in locations
    assert len(locations) == len(set(locations))


def test_first_line_checks_toggle():
    assert not any(name.startswith("line:") for name in active_locations(opts(first_line_checks=0)))


def test_delivery_checks_scale_with_tiers():
    assert not any(name.startswith("delivered:") for name in active_locations(opts(delivery_checks=0)))
    delivered = [name for name in active_locations(opts(delivery_checks=3)) if name.startswith("delivered:")]
    assert len(delivered) == 3 * len(data.CARGOS)


def test_zero_checks_disables_family():
    locations = active_locations(opts(population_checks=0, passengers_checks=0, cargo_checks=0))
    assert not any(name.split(":")[0] in ("population", "passengers", "cargo") for name in locations)


def test_ids_are_unique_and_stable():
    assert len(set(item_table.values())) == len(item_table)
    assert len(set(location_table.values())) == len(location_table)
    assert set(active_locations(opts(delivery_checks=4, population_checks=30))) <= set(location_table)
    from importlib import reload
    from transport_fever_3 import Locations
    snapshot = dict(location_table)
    reload(Locations)
    assert Locations.location_table == snapshot


def test_the_item_table_has_the_two_money_losses_and_no_loan():
    assert "Money Loss (small)" in item_table and "Money Loss (medium)" in item_table
    assert "Forced Loan" not in item_table and "Money Loss" not in item_table
