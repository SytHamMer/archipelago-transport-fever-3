from .. import cargos, data
from ..cargo_data import CARGO_BY_CLIMATE
from ..Locations import active_locations
from ..Options import TF3Options
from ..Rules import need_for
from .bases import TF3TestBase, make_options


def opts(**overrides):
    return make_options(TF3Options, **overrides)


def delivered_cargos(**overrides) -> set[str]:
    return {name.split(":")[1] for name in active_locations(opts(**overrides)) if name.startswith("delivered:")}


def test_the_table_only_names_cargos_of_the_world_and_sane_ranks():
    assert set(CARGO_BY_CLIMATE) == {"temperate", "dry", "subarctic", "tropical"}
    for climate, table in CARGO_BY_CLIMATE.items():
        assert set(table) <= set(data.CARGOS), climate
        assert all(count >= 1 and 1 <= rank <= 15 for count, rank in table.values()), climate
    assert set(data.CARGOS) <= {cargo for table in CARGO_BY_CLIMATE.values() for cargo in table}


def test_a_cargo_the_climate_cannot_produce_is_never_eligible():
    assert "fish" not in cargos.eligible_cargos("dry", level_items=14)
    assert "fish" in cargos.eligible_cargos("temperate", level_items=14)
    assert "vegetables" not in cargos.eligible_cargos("subarctic", level_items=14)


def test_a_cargo_needing_a_high_company_rank_waits_for_enough_level_items():
    few = cargos.eligible_cargos("temperate", level_items=4)  # rank 5
    assert "steel" in few and "crude_oil" in few
    assert "vehicles" not in few and "beverages" not in few  # ranks 10 and 13
    assert "vehicles" in cargos.eligible_cargos("temperate", level_items=9)
    assert "beverages" in cargos.eligible_cargos("temperate", level_items=12)


def test_difficulty_follows_the_number_of_industries_a_cargo_depends_on():
    assert cargos.difficulty(1) == 1 and cargos.difficulty(2) == 1
    assert cargos.difficulty(3) == 2 and cargos.difficulty(5) == 2
    assert cargos.difficulty(6) == 3 and cargos.difficulty(9) == 3


def test_harder_cargos_ask_for_smaller_amounts():
    easy = cargos.delivery_amounts("coal", "temperate", 4)
    hard = cargos.delivery_amounts("vehicles", "temperate", 4)
    assert easy == [100, 500, 2000, 10000]
    assert all(h < e for h, e in zip(hard, easy))
    assert cargos.delivery_amounts("coal", "temperate", 2) == [100, 500]


def test_the_climate_option_changes_which_deliveries_exist():
    assert "fish" in delivered_cargos(climate=0, company_level_checks=14)  # temperate
    assert "fish" not in delivered_cargos(climate=1, company_level_checks=14)  # dry
    assert delivered_cargos(climate=1) <= set(CARGO_BY_CLIMATE["dry"])


def test_default_deliveries_only_include_cargos_reachable_with_the_default_level_items():
    reachable = set(cargos.eligible_cargos("temperate", level_items=4))
    assert delivered_cargos() == reachable
    assert "vehicles" not in delivered_cargos()


def test_a_delivery_needs_as_many_level_items_as_its_industries_need_rank():
    steel = need_for("delivered:steel:1", {}, climate="temperate")  # rank 3
    assert steel.items.get(data.ITEM_LEVEL) == 2
    easy = need_for("delivered:grain:1", {}, climate="temperate")  # rank 1
    assert data.ITEM_LEVEL not in easy.items


class TestSlotDataCarriesPerCargoAmounts(TF3TestBase):
    options = {"climate": 1, "company_level_checks": 8, "delivery_checks": 2}

    def test_the_slot_data_lists_the_amounts_of_the_eligible_cargos_only(self):
        checks = self.world.fill_slot_data()["checks"]
        per_cargo = checks["delivery_by_cargo"]
        assert "fish" not in per_cargo and "coal" in per_cargo
        assert per_cargo["coal"] == [100, 500]
        assert all(len(amounts) == 2 for amounts in per_cargo.values())
        assert set(per_cargo) == set(cargos.eligible_cargos("dry", level_items=8))

    def test_every_delivery_location_is_reachable_with_everything(self):
        self.collect_all_but([])
        deliveries = [name for name in active_locations(self.world.options) if name.startswith("delivered:")]
        assert deliveries and all(self.can_reach_location(name) for name in deliveries)


class TestDryMapFills(TF3TestBase):
    options = {"climate": 1}


class TestSubarcticMapFills(TF3TestBase):
    options = {"climate": 2, "company_level_checks": 9, "delivery_checks": 3}


class TestTropicalMapWithManyLevelsFills(TF3TestBase):
    options = {"climate": 3, "company_level_checks": 14, "delivery_checks": 4}

    def test_hard_cargos_become_available_with_enough_levels(self):
        assert "vehicles" in delivered_cargos(climate=3, company_level_checks=14)
