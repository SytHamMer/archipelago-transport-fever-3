from typing import Optional, Any
from BaseClasses import MultiWorld



def get_option_value(multiworld: MultiWorld, player: int, name: str) -> int:
    # not imported from ..Helpers: that module imports this one
    option = getattr(multiworld.worlds[player].options, name, None)
    return 0 if option is None else option.value

# family category -> option name; build.py replaces this line (the apworld is a zip, so no data file)
FAMILY_OPTIONS: dict[str, str] = {}  # @@FAMILIES@@


def before_is_category_enabled(multiworld: MultiWorld, player: int, category_name: str) -> Optional[bool]:
    return None

def before_is_item_enabled(multiworld: MultiWorld, player: int, item:  dict[str, Any]) -> Optional[bool]:
    return None

def before_is_location_enabled(multiworld: MultiWorld, player: int, location:  dict[str, Any]) -> Optional[bool]:
    """A tiered check is active only while its tier <= the family's YAML option value."""
    categories = location.get("category", [])
    if "First Lines" in categories:
        return bool(get_option_value(multiworld, player, "first_line_checks"))
    for family, option in FAMILY_OPTIONS.items():
        if family in categories:
            tier = next(int(c.split()[1]) for c in categories if c.startswith("Tier "))
            return tier <= get_option_value(multiworld, player, option)
    return None

def before_is_event_enabled(multiworld: MultiWorld, player: int, event:  dict[str, Any]) -> Optional[bool]:
    return None
