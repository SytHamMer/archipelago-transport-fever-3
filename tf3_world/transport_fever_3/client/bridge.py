"""The file exchange with the TF3 mod: the client writes the inbox and reads the outbox."""
import os
from dataclasses import dataclass
from pathlib import Path

from .. import data
from . import luafile

INBOX_NAME = "archipelago_tf3_inbox.lua"
OUTBOX_NAME = "archipelago_tf3_outbox.lua"
FORMAT_VERSION = 1


@dataclass(frozen=True)
class Outbox:
    seed: str
    checks: set
    goals: dict
    applied: int
    heartbeat: int


def _effect(index: int, name: str) -> dict | None:
    """One-shot effect for a received item (None for items that are state, not effects)."""
    if name in data.MONEY_ITEMS:
        return {"id": index, "kind": "money", "amount": data.MONEY_ITEMS[name]}
    if name == "Money Loss":
        return {"id": index, "kind": "money_loss", "amount": data.TRAPS[name]}
    if name == "Forced Loan":
        return {"id": index, "kind": "loan", "amount": data.TRAPS[name]}
    return None


class Bridge:
    def __init__(self, userdata_dir: Path):
        self.dir = Path(userdata_dir)
        self.seed: str | None = None

    def write_inbox(self, slot_data: dict, received: list[str]) -> None:
        """Write the complete wanted state. `received` is the full ordered list of items received so far."""
        self.seed = slot_data["seed"]
        items: dict[str, int] = {}
        effects = []
        for index, name in enumerate(received, start=1):
            items[name] = items.get(name, 0) + 1
            effect = _effect(index, name)
            if effect:
                effects.append(effect)
        inbox = {
            "version": FORMAT_VERSION,
            "seed": slot_data["seed"],
            "config": {"goals": slot_data["goals"], "checks": slot_data["checks"]},
            "items": items,
            "effects": effects,
        }
        target = self.dir / INBOX_NAME
        temporary = self.dir / (INBOX_NAME + ".tmp")
        temporary.write_text(luafile.dumps(inbox), encoding="utf-8")
        os.replace(temporary, target)

    def read_outbox(self) -> Outbox | None:
        """The mod's outbox, or None when it is missing, unreadable (for example half written) or incomplete."""
        try:
            raw = luafile.loads((self.dir / OUTBOX_NAME).read_text(encoding="utf-8"))
            goals = raw["goals"] or {}
            return Outbox(
                seed=str(raw["seed"]),
                checks=set(raw["checks"]),
                goals=dict(goals),
                applied=int(raw["applied"]),
                heartbeat=int(raw["heartbeat"]),
            )
        except (OSError, luafile.LuaFormatError, KeyError, TypeError, ValueError):
            return None

    def seed_matches(self, slot_seed: str | None = None) -> bool:
        """False when an outbox exists but belongs to another seed. No outbox counts as a match."""
        wanted = slot_seed if slot_seed is not None else self.seed
        outbox = self.read_outbox()
        return outbox is None or outbox.seed == wanted

    def new_checks(self, sent: set) -> set:
        outbox = self.read_outbox()
        if outbox is None or not self.seed_matches():
            return set()
        return set(outbox.checks) - set(sent)
