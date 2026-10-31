"""The contracts of the multiworld: the reward each check holds, and how a check is written for the player."""
from collections.abc import Callable, Container, Iterable

def contracts_from_scout(
    infos: Iterable[tuple[int, int, int]],
    own_slot: int,
    location_name: Callable[[int], str | None],
    item_name: Callable[[int, int], str | None],
    player_name: Callable[[int], str | None],
) -> dict:
    """The reward of each check from the server's scout reply, keyed by check id.

    `infos` is a list of (location id, item id, receiving slot); an id that cannot be named is skipped.
    `item_name(item id, slot)` must look the item up in the game of the receiving slot: item ids are numbered per
    game, so the receiver may play another game than ours.
    """
    contracts = {}
    for location, item, receiver in infos:
        check, reward = location_name(location), item_name(item, receiver)
        if check is None or reward is None:
            continue
        contracts[check] = {"item": reward, "to": player_name(receiver) or f"Player {receiver}",
                            "own": receiver == own_slot}
    return contracts


FAMILY_ORDER = ("population", "company_level", "passengers", "cargo", "mission", "line", "delivered")
# Checks that are a step of a ladder: family -> (key of the thresholds in the slot data, text with the value)
LADDER_TEXTS = {
    "population": ("population", "Population reached {}"),
    "passengers": ("passengers", "Passengers transported: {}"),
    "cargo": ("cargo", "Cargo transported: {}"),
    "mission": ("missions", "Missions completed: {}"),
}


def nth(values: list[int], index: str) -> int | None:
    """The `index`-th value (counted from 1, as in a check id), or None when there is none."""
    return values[int(index) - 1] if index.isdigit() and 0 < int(index) <= len(values) else None


def delivery_amount(checks: dict, cargo: str, tier: str) -> int | None:
    """The amount of a delivery check: the cargo's own list when the seed gives one, the shared list otherwise."""
    amounts = (checks.get("delivery_by_cargo") or {}).get(cargo) or checks.get("delivery") or []
    return nth(amounts, tier)


def describe_check(check: str, checks: dict | None) -> str:
    """Readable text of a check id, as the in-game contract shows it (the id itself when it is not known)."""
    checks = checks or {}
    family, *parts = check.split(":")
    if family in LADDER_TEXTS and parts:
        key, template = LADDER_TEXTS[family]
        value = nth(checks.get(key) or [], parts[0])
        if value is not None:
            return template.format(f"{value:,}")
    elif family == "company_level" and parts:
        return f"Company level {parts[0]} reached"
    elif family == "line" and parts:
        return f"First {parts[0]} line built"
    elif family == "delivered" and len(parts) == 2:
        amount = delivery_amount(checks, parts[0], parts[1])
        if amount is not None:
            return f"Delivered {amount:,} {parts[0].replace('_', ' ')}"
    return check


def _next_contracts(open_ids: list[str]) -> list[str]:
    """The next step of each ladder and of each cargo's deliveries, and every first line (as the game shows them)."""
    best: dict[str, tuple[int, str]] = {}
    chosen = []
    for check in open_ids:
        family, *parts = check.split(":")
        if family == "line" or not parts or not parts[-1].isdigit():
            chosen.append(check)
            continue
        group = f"{family}:{parts[0]}" if family == "delivered" else family
        step = int(parts[-1])
        if group not in best or step < best[group][0]:
            best[group] = (step, check)
    chosen += [check for _, check in best.values()]
    return chosen


def _order(check: str) -> tuple[int, str]:
    family = check.split(":")[0]
    return FAMILY_ORDER.index(family) if family in FAMILY_ORDER else len(FAMILY_ORDER), check


def contracts_report(
    contracts: dict, done: Container[str], checks: dict | None = None, show_all: bool = False
) -> list[str]:
    """Console lines for /contracts: the progress, then the next open contracts with their reward.

    `checks` holds the thresholds of the slot data (to write the contracts in plain text); `show_all` lists every
    open contract, not only the next step of each ladder.
    """
    if not contracts:
        return ["No contracts known yet (waiting for the server)."]
    open_ids = [check for check in contracts if check not in done]
    shown = sorted(open_ids if show_all else _next_contracts(open_ids), key=_order)
    hidden = len(open_ids) - len(shown)
    header = f"Contracts: {len(contracts) - len(open_ids)}/{len(contracts)} done"
    if hidden:
        header += f" ({hidden} later contracts not shown, /contracts all lists everything)"
    lines = [header]
    for check in shown:
        reward = contracts[check]
        suffix = "" if reward["own"] else f" for {reward['to']}"
        lines.append(f"{describe_check(check, checks)} -> {reward['item']}{suffix}")
    return lines
