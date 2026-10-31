"""Names, constants and helpers shared by the world, the client and (through contract/constants.json) the mod."""

GAME_NAME = "Transport Fever 3"

# Transport modes that must be unlocked; the road is available from the start.
MODES = ("Tram", "Rail", "Water", "Air")
# Keys used in line check ids (`line:<key>`).
LINE_MODES = ("road", "tram", "rail", "water", "air")

ITEM_LEVEL = "Company Level +1"
# Specialised freight vehicle classes. Universal vehicles (any cargo) and passenger vehicles are never gated by class,
# so every cargo can be hauled by road from the start; a class item releases the vehicles made for that class only.
CARGO_CLASSES = ("Bulk", "Flatbed", "Goods", "Liquid")

# Construction tools, one item each: the tool stays locked until its item is received.
TOOLS = ("Tool: Bus Lanes", "Tool: Tram Tracks", "Tool: Rail Signals", "Tool: Electrification", "Tool: Noise Barriers")
# Road and track types come in steps by first year, like the vehicles (see ERA_STARTS).
ITEM_ROAD_TYPES = "Progressive Road Types"
ITEM_RAIL_TRACKS = "Progressive Rail Tracks"
# Amounts are in 1900 money: the mod multiplies them by the game's inflation of the year of the game.
MONEY_ITEMS = {
    "Money Grant (small)": 50_000,
    "Money Grant (medium)": 250_000,
    "Money Grant (large)": 1_000_000,
}
MONEY_WEIGHTS = (5, 3, 1)  # how often the filler draws each grant, small to large
# Traps take money away. The small loss is drawn three times out of four.
TRAPS = {"Money Loss (small)": 50_000, "Money Loss (medium)": 250_000}
TRAP_WEIGHTS = (3, 1)

# Cargos the world delivers (identifiers of the game's cargo files, passengers excluded): every one that exists in at
# least one climate, see cargo_data.py.
CARGOS = (
    "beverages", "bricks", "chemicals", "clay", "clothes", "coal", "crude_oil", "dyes", "fabric", "fish",
    "fuel", "furniture", "glass", "grain", "iron_ore", "logs", "machines", "meat", "planks", "sand",
    "sheet_metal", "steel", "stone", "tinned_food", "tools", "vegetables", "vehicles", "wool",
)
DELIVERY_AMOUNTS = (100, 500, 2000, 10000)

# First year of the second and third vehicle eras: vehicles are unlocked by tier, tier 1 (era A) comes with the mode.
ERA_STARTS = {"B": 1920, "C": 1960}
# Versions of the mod before 2.0 could not remove the first years of the content, so a game had to start at or after
# this year; the client only warns about an earlier one when the mod does not say it removed them.
MIN_START_YEAR = 2000

# Check families with a configurable ladder of thresholds, and goal names.
FAMILIES = ("population", "company_level", "passengers", "cargo")
GOALS = FAMILIES


def mode_item(mode: str) -> str:
    return f"{mode} Transport"


def vehicles_item(mode: str) -> str:
    return f"Progressive {mode} Vehicles"


def location_id(family: str, *parts) -> str:
    return ":".join([family, *(str(part) for part in parts)])


def spread(count: int, first: int, last: int) -> list[int]:
    """`count` strictly increasing thresholds, geometrically spaced from `first` to `last`.

    Degenerate input (count 1, equal or inverted bounds) never fails: the values are still strictly increasing.
    """
    if count <= 0:
        return []
    low = max(first, 1)
    high = max(last, low)
    values = []
    for index in range(count):
        ratio = index / (count - 1) if count > 1 else 0
        value = round(low * (high / low) ** ratio)
        if values and value <= values[-1]:
            value = values[-1] + 1
        values.append(value)
    return values


def vehicle_items() -> list[str]:
    return [vehicles_item(mode) for mode in ("Road", *MODES)]


def cargo_class_item(name: str) -> str:
    return f"Cargo Class: {name}"


def cargo_class_items() -> list[str]:
    return [cargo_class_item(name) for name in CARGO_CLASSES]


def type_items() -> list[str]:
    return [ITEM_ROAD_TYPES, ITEM_RAIL_TRACKS]


def contract() -> dict:
    """The part of this module that the mod and client tests must agree on."""
    return {
        "version": 1,
        "modes": list(MODES),
        "line_modes": list(LINE_MODES),
        "mode_items": [mode_item(mode) for mode in MODES],
        "vehicle_items": vehicle_items(),
        "type_items": type_items(),
        "tools": list(TOOLS),
        "cargo_class_items": cargo_class_items(),
        "level_item": ITEM_LEVEL,
        "money_items": dict(MONEY_ITEMS),
        "traps": dict(TRAPS),
        "trap_weights": list(TRAP_WEIGHTS),
        "cargos": list(CARGOS),
        "delivery_amounts": list(DELIVERY_AMOUNTS),
        "era_starts": dict(ERA_STARTS),
        "min_start_year": MIN_START_YEAR,
        "families": list(FAMILIES),
        "goals": list(GOALS),
    }
