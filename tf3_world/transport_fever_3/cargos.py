"""Which cargos can be delivered in a game, and how many: from the climate, the company rank and the difficulty."""
from . import data
from .cargo_data import CARGO_BY_CLIMATE

CLIMATES = tuple(CARGO_BY_CLIMATE)  # temperate, dry, subarctic, tropical: the order of the `climate` option
EASY_MAX_INDUSTRIES = 2  # a cargo that depends on this many industries or fewer is easy
HARD_MIN_INDUSTRIES = 6  # and one that depends on this many or more is hard
# Delivery amounts per difficulty (easy, medium, hard): a car or a machine is far harder to deliver than grain.
AMOUNTS_BY_DIFFICULTY: dict[int, tuple[int, ...]] = {
    1: (100, 500, 2000, 10000),
    2: (50, 250, 1000, 5000),
    3: (20, 100, 400, 2000),
}


def difficulty(industries: int) -> int:
    """1 (easy), 2 (medium) or 3 (hard) for a cargo that depends on this many industries."""
    if industries <= EASY_MAX_INDUSTRIES:
        return 1
    return 3 if industries >= HARD_MIN_INDUSTRIES else 2


def required_level_items(cargo: str, climate: str) -> int:
    """The "Company Level +1" items that guarantee the company rank at which the cargo's industries exist."""
    return CARGO_BY_CLIMATE[climate][cargo][1] - 1


def eligible_cargos(climate: str, level_items: int) -> list[str]:
    """The cargos that can be produced in the climate and whose industries exist with this many level items."""
    table = CARGO_BY_CLIMATE[climate]
    return [cargo for cargo in data.CARGOS if cargo in table and required_level_items(cargo, climate) <= level_items]


def delivery_amounts(cargo: str, climate: str, tiers: int) -> list[int]:
    """The amounts of the first `tiers` delivery checks of a cargo."""
    return list(AMOUNTS_BY_DIFFICULTY[difficulty(CARGO_BY_CLIMATE[climate][cargo][0])][:tiers])
