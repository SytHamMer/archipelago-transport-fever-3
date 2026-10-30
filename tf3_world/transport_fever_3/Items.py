from . import data
from .Options import TF3Options

ITEM_ID_BASE = 7_300_000

# Every item the world can create, in a fixed order so that ids stay stable between versions.
_ITEM_NAMES = [
    *(data.ITEM_MODE(mode) for mode in data.MODES),
    *data.vehicle_items(),
    *data.type_items(),
    *data.TOOLS,
    *data.cargo_class_items(),
    data.ITEM_LEVEL,
    *data.MONEY_ITEMS,
    *data.TRAPS,
]
item_table: dict[str, int] = {name: ITEM_ID_BASE + index for index, name in enumerate(_ITEM_NAMES)}

# Vehicle tiers beyond the starting one (era B and era C), unlocked by the progressive items.
VEHICLE_TIERS_PER_MODE = 2


def item_counts(options: TF3Options) -> dict[str, int]:
    """Progression items the world creates; filler money and traps are added by the world itself."""
    counts = {data.ITEM_MODE(mode): 1 for mode in data.MODES}
    counts.update({name: VEHICLE_TIERS_PER_MODE for name in data.vehicle_items()})
    counts.update({name: VEHICLE_TIERS_PER_MODE for name in data.type_items()})  # same two steps as the vehicles
    counts.update({name: 1 for name in data.TOOLS})
    counts.update({name: 1 for name in data.cargo_class_items()})
    if options.company_level_checks.value > 0:
        counts[data.ITEM_LEVEL] = options.company_level_checks.value
    return counts
