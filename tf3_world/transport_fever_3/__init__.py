from collections.abc import Callable

from BaseClasses import CollectionState, Item, ItemClassification, Location, Region, Tutorial
from Options import OptionError
from worlds.AutoWorld import WebWorld, World
from worlds.LauncherComponents import Component, Type, components, launch as launch_component
from worlds.generic.Rules import set_rule

from . import cargos, data
from .Items import ITEM_GROUPS, item_counts, item_table
from .Locations import LOCATION_GROUPS, active_locations, eligible_cargos, location_table
from .Options import OPTION_GROUPS, OPTION_PRESETS, TF3Options, validate_goals
from .Rules import GOAL_NEED, MODE_ITEMS, Need, need_for


CLIENT_NAME = f"{data.GAME_NAME} Client"
CARGO_CLASS_ITEMS = frozenset(data.cargo_class_items())


def launch_client(*args: str) -> None:
    from .client.tf3_client import launch

    launch_component(launch, name=CLIENT_NAME, args=args)


components.append(Component(CLIENT_NAME, func=launch_client, component_type=Type.CLIENT))


class TF3Web(WebWorld):
    theme = "ocean"
    tutorials = [Tutorial(
        "Multiworld Setup Guide", "A guide to setting up Transport Fever 3 for Archipelago.", "English",
        "setup_en.md", "setup/en", ["Mathys"],
    )]
    option_groups = OPTION_GROUPS
    options_presets = OPTION_PRESETS
    bug_report_page = "https://github.com/SytHamMer/archipelago-transport-fever-3/issues"


class TF3Item(Item):
    game = data.GAME_NAME


class TF3Location(Location):
    game = data.GAME_NAME


class TF3World(World):
    """
    Transport Fever 3: build road, rail, tram, water and air networks.
    Unlocks and checks are driven by a game mod.
    """

    game = data.GAME_NAME
    web = TF3Web()
    options_dataclass = TF3Options
    options: TF3Options
    item_name_to_id = item_table
    location_name_to_id = location_table
    item_name_groups = ITEM_GROUPS
    location_name_groups = LOCATION_GROUPS
    topology_present = False

    def generate_early(self) -> None:
        validate_goals(self.options)
        locations = len(active_locations(self.options))
        needed = sum(item_counts(self.options).values())
        if locations < needed:
            raise OptionError(
                f"{data.GAME_NAME}: the chosen options only give {locations} checks, but {needed} progression items "
                f"must be placed. Raise the check options (population_checks, company_level_checks, "
                f"passengers_checks, cargo_checks, delivery_checks, first_line_checks, mission_checks) until there are "
                f"at least {needed} checks."
            )

    def _ladder_sizes(self) -> dict[str, int]:
        return {
            "population": self.options.population_checks.value,
            "passengers": self.options.passengers_checks.value,
            "cargo": self.options.cargo_checks.value,
        }

    def create_item(self, name: str) -> TF3Item:
        if name in data.TRAPS:
            classification = ItemClassification.trap
        elif name in data.MONEY_ITEMS:
            classification = ItemClassification.filler
        elif name in CARGO_CLASS_ITEMS:
            classification = ItemClassification.useful
        else:
            classification = ItemClassification.progression
        return TF3Item(name, classification, item_table[name], self.player)

    def create_regions(self) -> None:
        menu = Region("Menu", self.player, self.multiworld)
        menu.add_locations({name: location_table[name] for name in active_locations(self.options)}, TF3Location)
        goal = TF3Location(self.player, "Goal", None, menu)
        goal.place_locked_item(Item("Goal reached", ItemClassification.progression, None, self.player))
        menu.locations.append(goal)
        self.multiworld.regions.append(menu)

    def create_items(self) -> None:
        pool = [self.create_item(name) for name, count in item_counts(self.options).items() for _ in range(count)]
        filler_count = len(active_locations(self.options)) - len(pool)
        for _ in range(filler_count):
            pool.append(self.create_item(self.get_filler_item_name()))
        self.multiworld.itempool += pool

    def get_filler_item_name(self) -> str:
        if self.random.random() < 0.15:
            return self.random.choices(list(data.TRAPS), weights=data.TRAP_WEIGHTS)[0]
        return self.random.choices(list(data.MONEY_ITEMS), weights=data.MONEY_WEIGHTS)[0]

    def _rule(self, need: Need) -> Callable[[CollectionState], bool]:
        player = self.player
        return lambda state: (
            state.has_all_counts(need.items, player) and state.count_from_list(MODE_ITEMS, player) >= need.modes
        )

    def set_rules(self) -> None:
        sizes = self._ladder_sizes()
        for name in active_locations(self.options):
            set_rule(self.get_location(name), self._rule(need_for(name, sizes, self.options.climate.current_key)))
        set_rule(self.get_location("Goal"), self._rule(GOAL_NEED))
        self.multiworld.completion_condition[self.player] = lambda state: state.has("Goal reached", self.player)

    def fill_slot_data(self) -> dict:
        options = self.options
        return {
            "version": 1,
            "seed": self.multiworld.seed_name,
            "eras": dict(data.ERA_STARTS),
            "money_scale": options.money_scale.value,
            "loan_scale": options.loan_scale.value,
            "death_link": bool(options.death_link.value),
            "death_link_loss": options.death_link_loss.value,
            "goals": {
                "population": options.goal_population.value,
                "company_level": options.goal_company_level.value,
                "passengers": options.goal_passengers.value,
                "cargo": options.goal_cargo.value,
            },
            "checks": {
                "population": data.spread(
                    options.population_checks.value, options.population_first.value, options.population_last.value
                ),
                "company_level": list(range(2, options.company_level_checks.value + 2)),
                "passengers": data.spread(
                    options.passengers_checks.value, options.passengers_first.value, options.passengers_last.value
                ),
                "cargo": data.spread(options.cargo_checks.value, options.cargo_first.value, options.cargo_last.value),
                "first_line": bool(options.first_line_checks.value),
                "missions": list(range(1, options.mission_checks.value + 1)),
                "delivery": list(data.DELIVERY_AMOUNTS[: options.delivery_checks.value]),
                "delivery_by_cargo": {
                    cargo: cargos.delivery_amounts(cargo, options.climate.current_key, options.delivery_checks.value)
                    for cargo in eligible_cargos(options)
                },
            },
        }
