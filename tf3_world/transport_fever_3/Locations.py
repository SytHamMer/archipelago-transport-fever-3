from . import cargos, data
from .Options import TF3Options

LOCATION_ID_BASE = 7_400_000
MAX_LADDER_STEPS = 30  # matches the range_end of the *_checks options
MAX_COMPANY_LEVEL = 15

_NAMES = [
    *(data.location_id("population", step) for step in range(1, MAX_LADDER_STEPS + 1)),
    *(data.location_id("company_level", level) for level in range(2, MAX_COMPANY_LEVEL + 1)),
    *(data.location_id("passengers", step) for step in range(1, MAX_LADDER_STEPS + 1)),
    *(data.location_id("cargo", step) for step in range(1, MAX_LADDER_STEPS + 1)),
    *(data.location_id("line", mode) for mode in data.LINE_MODES),
    *(
        data.location_id("delivered", cargo, tier)
        for cargo in data.CARGOS
        for tier in range(1, len(data.DELIVERY_AMOUNTS) + 1)
    ),
    *(data.location_id("mission", step) for step in range(1, MAX_LADDER_STEPS + 1)),  # appended last: ids stay stable
]
location_table: dict[str, int] = {name: LOCATION_ID_BASE + index for index, name in enumerate(_NAMES)}


def eligible_cargos(options: TF3Options) -> list[str]:
    """The cargos that get delivery checks: producible in the chosen climate, and with their industries unlocked."""
    return cargos.eligible_cargos(options.climate.current_key, options.company_level_checks.value)


def active_locations(options: TF3Options) -> list[str]:
    names = [data.location_id("population", step) for step in range(1, options.population_checks.value + 1)]
    names += [data.location_id("company_level", level) for level in range(2, options.company_level_checks.value + 2)]
    names += [data.location_id("passengers", step) for step in range(1, options.passengers_checks.value + 1)]
    names += [data.location_id("cargo", step) for step in range(1, options.cargo_checks.value + 1)]
    if options.first_line_checks.value:
        names += [data.location_id("line", mode) for mode in data.LINE_MODES]
    names += [
        data.location_id("delivered", cargo, tier)
        for cargo in eligible_cargos(options)
        for tier in range(1, options.delivery_checks.value + 1)
    ]
    names += [data.location_id("mission", step) for step in range(1, options.mission_checks.value + 1)]
    return names