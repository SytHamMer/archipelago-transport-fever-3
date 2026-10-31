from dataclasses import dataclass

from Options import Choice, DeathLink, OptionError, OptionGroup, PerGameCommonOptions, Range, Toggle


def _ladder(prefix: str, label: str, checks: int, first: int, last: int, top: int) -> tuple[type, type, type]:
    """Three options describing a ladder of thresholds: how many, the first and the last value."""
    count = type(f"{prefix.title().replace('_', '')}Checks", (Range,), {
        "__doc__": f"Number of {label} milestones that are checks (0 disables them).",
        "display_name": f"{label.capitalize()} checks",
        "range_start": 0, "range_end": 30, "default": checks, "__module__": __name__,
    })
    low = type(f"{prefix.title().replace('_', '')}First", (Range,), {
        "__doc__": f"Value of the first {label} milestone.",
        "display_name": f"First {label} milestone",
        "range_start": 1, "range_end": top, "default": first, "__module__": __name__,
    })
    high = type(f"{prefix.title().replace('_', '')}Last", (Range,), {
        "__doc__": f"Value of the last {label} milestone.",
        "display_name": f"Last {label} milestone",
        "range_start": 1, "range_end": top, "default": last, "__module__": __name__,
    })
    return count, low, high


PopulationChecks, PopulationFirst, PopulationLast = _ladder("population", "population", 4, 500, 5000, 1_000_000)
PassengersChecks, PassengersFirst, PassengersLast = _ladder(
    "passengers", "passengers transported", 3, 100, 2000, 10_000_000
)
CargoChecks, CargoFirst, CargoLast = _ladder("cargo", "cargo transported", 3, 100, 2000, 10_000_000)


class CompanyLevelChecks(Range):
    """Number of company level milestones that are checks: levels 2, 3, 4... (0 disables them)."""
    display_name = "Company level checks"
    range_start = 0
    range_end = 14
    default = 4


class DeliveryChecks(Range):
    """Delivery tiers per cargo that are checks (up to four; the amounts depend on how hard the cargo is). 0 disables
    them."""
    display_name = "Delivery checks per cargo"
    range_start = 0
    range_end = 4
    default = 1


class MissionChecks(Range):
    """Number of missions (the game's offers such as connecting two towns) that are checks: 1, 2, 3... missions
    completed (0 disables them)."""
    display_name = "Mission checks"
    range_start = 0
    range_end = 30
    default = 3


class Climate(Choice):
    """Climate of the map you will play: delivery checks only ask for cargos that climate can produce, and only
    for those whose industries exist at the company rank your level items guarantee."""
    display_name = "Map climate"
    option_temperate = 0
    option_dry = 1
    option_subarctic = 2
    option_tropical = 3
    default = 0


class FirstLineChecks(Toggle):
    """Building the first line of each transport mode is a check."""
    display_name = "First line checks"
    default = 1


class GoalPopulation(Range):
    """Goal: reach this many inhabitants in total. 0 disables this goal."""
    display_name = "Goal: population"
    range_start = 0
    range_end = 1_000_000
    default = 2500


class GoalCompanyLevel(Range):
    """Goal: reach this company level through experience. 0 disables this goal."""
    display_name = "Goal: company level"
    range_start = 0
    range_end = 15
    default = 0


class GoalPassengers(Range):
    """Goal: transport this many passengers in total. 0 disables this goal."""
    display_name = "Goal: passengers transported"
    range_start = 0
    range_end = 10_000_000
    default = 0


class GoalCargo(Range):
    """Goal: transport this many units of cargo in total. 0 disables this goal."""
    display_name = "Goal: cargo transported"
    range_start = 0
    range_end = 10_000_000
    default = 0


class MoneyScale(Range):
    """Percentage applied to every money grant and every money loss (100 = the base amounts)."""
    display_name = "Money scale (%)"
    range_start = 10
    range_end = 1000
    default = 100


class LoanScale(Range):
    """Percentage applied to the amount of every bank loan (100 = the game's amounts, which follow the year of the game
    and are very large in a game that starts in 2020)."""
    display_name = "Loan scale (%)"
    range_start = 1
    range_end = 200
    default = 100


class DeathLinkLoss(Range):
    """Money the company loses each time another player's DeathLink arrives (needs death_link), in 1900 money: it is
    multiplied by the game's inflation of the year of the game, like every amount of this world. money_scale is not
    applied to it."""
    display_name = "Death link loss"
    range_start = 1_000
    range_end = 100_000_000
    default = 50_000


@dataclass
class TF3Options(PerGameCommonOptions):
    population_checks: PopulationChecks
    population_first: PopulationFirst
    population_last: PopulationLast
    company_level_checks: CompanyLevelChecks
    passengers_checks: PassengersChecks
    passengers_first: PassengersFirst
    passengers_last: PassengersLast
    cargo_checks: CargoChecks
    cargo_first: CargoFirst
    cargo_last: CargoLast
    delivery_checks: DeliveryChecks
    first_line_checks: FirstLineChecks
    climate: Climate
    mission_checks: MissionChecks
    goal_population: GoalPopulation
    goal_company_level: GoalCompanyLevel
    goal_passengers: GoalPassengers
    goal_cargo: GoalCargo
    money_scale: MoneyScale
    loan_scale: LoanScale
    death_link: DeathLink
    death_link_loss: DeathLinkLoss


def validate_goals(options: TF3Options) -> None:
    goals = (options.goal_population, options.goal_company_level, options.goal_passengers, options.goal_cargo)
    if not any(goal.value > 0 for goal in goals):
        raise OptionError(
            "Transport Fever 3: no goal is active. Set at least one of goal_population, goal_company_level, "
            "goal_passengers or goal_cargo above 0."
        )


OPTION_GROUPS = [
    OptionGroup("Checks", [
        PopulationChecks, PopulationFirst, PopulationLast, PassengersChecks, PassengersFirst, PassengersLast,
        CargoChecks, CargoFirst, CargoLast, CompanyLevelChecks, DeliveryChecks, FirstLineChecks, MissionChecks,
    ]),
    OptionGroup("Map and economy", [Climate, MoneyScale, LoanScale]),
    OptionGroup("Goals", [GoalPopulation, GoalCompanyLevel, GoalPassengers, GoalCargo]),
    OptionGroup("DeathLink", [DeathLink, DeathLinkLoss]),
]


# Presets offered on the web page of the game: a quick game, the default one and a long one.
OPTION_PRESETS: dict[str, dict[str, int]] = {
    "Short game": {
        "goal_population": 1500, "population_checks": 3, "population_last": 1500, "passengers_checks": 2,
        "cargo_checks": 2, "mission_checks": 2,
    },
    "Default": {},
    "Long game": {
        "goal_population": 20_000, "goal_passengers": 5_000, "population_checks": 10, "population_last": 20_000,
        "passengers_checks": 6, "passengers_last": 5_000, "cargo_checks": 5, "company_level_checks": 9,
        "delivery_checks": 2, "mission_checks": 5,
    },
}
