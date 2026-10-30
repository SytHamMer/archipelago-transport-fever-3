from dataclasses import dataclass, field

from . import data

MODE_ITEMS = tuple(data.ITEM_MODE(mode) for mode in data.MODES)
ROAD_VEHICLES = data.ITEM_VEHICLES("Road")


@dataclass(frozen=True)
class Need:
    """What a location needs: item counts, plus how many non-road modes must be unlocked."""
    items: dict = field(default_factory=dict)
    modes: int = 0


def _ladder_need(step: int, total: int) -> Need:
    fraction = step / total
    modes = 0 if fraction <= 1 / 3 else 1 if fraction <= 2 / 3 else 2
    tiers = 0 if fraction <= 0.5 else 1 if fraction <= 0.8 else 2
    return Need({ROAD_VEHICLES: tiers} if tiers else {}, modes)


def _level_need(level: int) -> Need:
    modes = 0 if level < 5 else 1 if level < 9 else 2 if level < 12 else 3
    tiers = 0 if level < 8 else 1 if level < 12 else 2
    return Need({ROAD_VEHICLES: tiers} if tiers else {}, modes)


def need_for(location: str, ladder_sizes: dict[str, int]) -> Need:
    """Requirements of a check, from its id (see data.location_id)."""
    family, *parts = location.split(":")
    if family in ("population", "passengers", "cargo"):
        return _ladder_need(int(parts[0]), ladder_sizes[family])
    if family == "company_level":
        return _level_need(int(parts[0]))
    if family == "line":
        mode = parts[0]
        return Need({data.ITEM_MODE(mode.capitalize()): 1}) if mode != "road" else Need()
    if family == "delivered":
        tier = int(parts[1])
        tiers = 0 if tier <= 1 else 1 if tier <= 2 else 2
        return Need({ROAD_VEHICLES: tiers} if tiers else {})
    if family == "mission":
        return Need()  # an offer can be completed with the starting road vehicles
    raise ValueError(f"unknown location {location}")


# Reaching any goal needs two unlocked modes and the second road vehicle tier.
GOAL_NEED = Need({ROAD_VEHICLES: 2}, 2)
