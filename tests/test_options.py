import pytest
from helpers import make_options
from Options import OptionError

from transport_fever_3.Options import TF3Options, validate_goals

GOAL_OPTIONS = ("goal_population", "goal_company_level", "goal_passengers", "goal_cargo")


def test_default_options_have_exactly_one_goal():
    options = make_options(TF3Options)
    active = [name for name in GOAL_OPTIONS if getattr(options, name).value > 0]
    assert active == ["goal_population"]
    validate_goals(options)  # does not raise


def test_no_active_goal_raises_with_goal_in_message():
    options = make_options(TF3Options, **{name: 0 for name in GOAL_OPTIONS})
    with pytest.raises(OptionError, match="goal"):
        validate_goals(options)


def test_any_single_goal_is_enough():
    for name in GOAL_OPTIONS:
        zeroed = {other: 0 for other in GOAL_OPTIONS}
        zeroed[name] = 5
        validate_goals(make_options(TF3Options, **zeroed))


def test_option_names_are_valid_unique_yaml_keys():
    names = list(TF3Options.type_hints)
    assert len(names) == len(set(names))
    assert all(name == name.lower() and " " not in name for name in names)


def test_check_families_default_to_small_ladders():
    options = make_options(TF3Options)
    assert options.population_checks.value == 4
    assert options.population_first.value < options.population_last.value
    assert options.first_line_checks.value == 1
    assert options.delivery_checks.value == 1


def test_every_option_class_can_be_pickled():
    # Archipelago pickles the options of a generated game; a class made by a factory must name its real module
    import pickle

    for name, option in TF3Options.type_hints.items():
        assert pickle.loads(pickle.dumps(option)) is option, name
