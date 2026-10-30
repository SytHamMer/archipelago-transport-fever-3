import pytest
from Options import OptionError
from test.bases import WorldTestBase


class TF3TestBase(WorldTestBase):
    game = "Transport Fever 3"


class TestDefaultWorld(TF3TestBase):
    def test_default_seed_is_beatable(self):
        self.collect_all_but([])
        self.assertBeatable(True)

    def test_default_seed_is_not_beatable_without_items(self):
        self.assertBeatable(False)

    def test_line_check_requires_mode_item(self):
        assert not self.can_reach_location("line:rail")
        self.collect_by_name("Rail Transport")
        assert self.can_reach_location("line:rail")

    def test_road_line_is_reachable_from_the_start(self):
        assert self.can_reach_location("line:road")

    def test_slot_data_shape(self):
        data = self.world.fill_slot_data()
        assert data["version"] == 1
        assert data["seed"] == self.multiworld.seed_name
        assert data["goals"] == {"population": 2500, "company_level": 0, "passengers": 0, "cargo": 0}
        assert len(data["checks"]["population"]) == 4
        assert data["checks"]["population"][0] == 500 and data["checks"]["population"][-1] == 5000
        assert data["checks"]["company_level"] == [2, 3, 4, 5]
        assert data["checks"]["first_line"] is True
        assert data["checks"]["delivery"] == [100]
        assert data["eras"] == {"B": 1920, "C": 1960}


class TestFillerAndTraps(TF3TestBase):
    def test_filler_draws_only_known_items_with_about_fifteen_percent_traps(self):
        names = [self.world.get_filler_item_name() for _ in range(2000)]
        traps = [n for n in names if n.startswith("Money Loss")]
        assert set(names) <= set(self.world.item_name_to_id)
        assert "Forced Loan" not in names
        assert 0.10 < len(traps) / len(names) < 0.20
        assert traps.count("Money Loss (small)") > traps.count("Money Loss (medium)") > 0

    def test_traps_are_classified_as_traps(self):
        from BaseClasses import ItemClassification

        assert self.world.create_item("Money Loss (small)").classification == ItemClassification.trap
        assert self.world.create_item("Money Loss (medium)").classification == ItemClassification.trap


class TestAllGoalsRequired(TF3TestBase):
    options = {"goal_population": 100, "goal_passengers": 100, "goal_cargo": 100, "goal_company_level": 2}

    def test_beatable_with_everything(self):
        self.collect_all_but([])
        self.assertBeatable(True)

    def test_slot_data_lists_every_goal(self):
        assert self.world.fill_slot_data()["goals"] == {
            "population": 100, "company_level": 2, "passengers": 100, "cargo": 100,
        }


class TestTooFewChecks(TF3TestBase):
    options = {
        "population_checks": 0, "company_level_checks": 0, "passengers_checks": 0, "cargo_checks": 0,
        "delivery_checks": 0, "first_line_checks": 0,
    }
    auto_construct = False

    def test_too_few_checks_raises_with_numbers(self):
        with pytest.raises(OptionError, match=r"0 checks.*progression items"):
            self.world_setup()


class TestNoGoal(TF3TestBase):
    options = {"goal_population": 0}
    auto_construct = False

    def test_no_goal_raises(self):
        with pytest.raises(OptionError, match="goal"):
            self.world_setup()


class TestCargoClassItems(TF3TestBase):
    def test_cargo_class_items_are_useful_not_progression(self):
        from BaseClasses import ItemClassification

        item = self.world.create_item("Cargo Class: Bulk")
        assert item.classification == ItemClassification.useful

    def test_deliveries_do_not_need_a_cargo_class_item(self):
        # a universal road vehicle carries every cargo from the start
        assert self.can_reach_location("delivered:coal:1")
        assert self.can_reach_location("delivered:crude_oil:1")
