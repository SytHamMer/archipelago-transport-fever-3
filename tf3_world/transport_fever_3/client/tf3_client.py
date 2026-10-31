"""Archipelago client for Transport Fever 3: relays between the server and the game mod through two files."""
import asyncio
import os
import time
from argparse import Namespace
from collections.abc import Callable, Container, Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .. import data
from ..Locations import location_table
from .bridge import Bridge

STEAM_ROOT = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam"
TF3_APP_ID = "3493540"
EXCHANGE_FOLDER = "towns_industries"  # one of the two userdata folders the game lets mods use
HEARTBEAT_TIMEOUT = 10  # seconds without a mod heartbeat before the game counts as idle


def find_userdata_dir(steam_root: Path | None = None, override: str | None = None) -> Path | None:
    """The folder shared with the mod, or None when TF3's user data cannot be found.

    With several Steam accounts the most recently used one wins.
    """
    override = override or os.environ.get("TF3_USERDATA_DIR")
    if override:
        return Path(override)
    root = Path(steam_root) if steam_root is not None else STEAM_ROOT
    candidates = list((root / "userdata").glob(f"*/{TF3_APP_ID}/local"))
    if not candidates:
        return None
    folder = max(candidates, key=lambda path: path.stat().st_mtime) / EXCHANGE_FOLDER
    folder.mkdir(exist_ok=True)
    return folder


def resolve_userdata_dir(text: str) -> Path | None:
    """A folder typed or pasted by the player (quotes allowed), or None when it does not exist."""
    cleaned = text.strip().strip('"').strip()
    if not cleaned:
        return None
    path = Path(cleaned)
    return path if path.is_dir() else None


def check_ids(names: Iterable[str]) -> list[int]:
    """Archipelago location ids for the check names the mod reported (unknown names are skipped)."""
    return sorted(location_table[name] for name in names if name in location_table)


def received_log(
    received: Iterable[tuple[str, int, int]],
    own_slot: int,
    player_name: Callable[[int], str | None],
    location_name: Callable[[int, int], str],
) -> list[dict]:
    """Who sent each received item and for which check, for the in-game notifications.

    `received` is a list of (item name, location id, sender slot); `player_name(slot)` and `location_name(id, slot)`
    give the names (a location that cannot be named is left out).
    """
    log = []
    for item, location, sender in received:
        entry: dict = {"item": item}
        if sender == own_slot:
            entry["own"] = True
        else:
            entry["from"] = player_name(sender) or f"Player {sender}"
        try:
            entry["where"] = location_name(location, sender)
        except (KeyError, LookupError):
            pass
        log.append(entry)
    return log


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


def delivery_amount(checks: dict, cargo: str, tier: str) -> int | None:
    """The amount of a delivery check: the cargo's own list when the seed gives one, the shared list otherwise."""
    amounts = (checks.get("delivery_by_cargo") or {}).get(cargo) or checks.get("delivery") or []
    return amounts[int(tier) - 1] if tier.isdigit() and 0 < int(tier) <= len(amounts) else None


def describe_check(check: str, checks: dict | None) -> str:
    """Readable text of a check id, as the in-game contract shows it (the id itself when it is not known)."""
    checks = checks or {}
    family, *parts = check.split(":")

    def threshold(name: str, index: str) -> int | None:
        values = checks.get(name) or []
        return values[int(index) - 1] if index.isdigit() and 0 < int(index) <= len(values) else None

    if family == "population" and threshold("population", parts[0]) is not None:
        return f"Population reached {threshold('population', parts[0]):,}"
    if family == "company_level" and parts:
        return f"Company level {parts[0]} reached"
    if family == "passengers" and threshold("passengers", parts[0]) is not None:
        return f"Passengers transported: {threshold('passengers', parts[0]):,}"
    if family == "cargo" and threshold("cargo", parts[0]) is not None:
        return f"Cargo transported: {threshold('cargo', parts[0]):,}"
    if family == "mission" and threshold("missions", parts[0]) is not None:
        return f"Missions completed: {threshold('missions', parts[0]):,}"
    if family == "line" and parts:
        return f"First {parts[0]} line built"
    if family == "delivered" and len(parts) == 2:
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


class StatusTracker:
    """Decides when a change of the game's status is worth telling the player.

    The mod rewrites its outbox every two seconds, so reading it can briefly fail while the file is half written:
    "no_outbox" is only reported once it has lasted a few polls, instead of flapping between two messages.
    """

    NO_OUTBOX_POLLS = 3

    def __init__(self) -> None:
        self.reported: str | None = None
        self.missing = 0

    def update(self, status: str) -> str | None:
        """The status to report now, or None when there is nothing new to say."""
        if status == "no_outbox" and self.reported not in (None, "no_outbox"):
            self.missing += 1
            if self.missing < self.NO_OUTBOX_POLLS:
                return None
        else:
            self.missing = 0
        if status == self.reported:
            return None
        self.reported = status
        return status


@dataclass
class PollResult:
    new_checks: set = field(default_factory=set)
    goal_reached: bool = False
    status: str = "no_outbox"  # no_outbox, game_connected or game_idle
    year_warning: bool = False  # the game's year is before data.MIN_START_YEAR


class TF3Sync:
    """The logic of the client, independent of the network: slot state in, checks and goal status out."""

    def __init__(self, bridge: Bridge) -> None:
        self.bridge = bridge
        self.slot_data: dict | None = None
        self.received: list[str] = []
        self.log: list[dict] | None = None
        self.sent: set = set()
        self.inbox_dirty = False  # the last inbox write failed and must be retried
        self.contracts: dict | None = None

    def _write_inbox(self) -> None:
        if self.slot_data is None:
            return
        try:
            self.bridge.write_inbox(self.slot_data, self.received, self.log, self.contracts)
            self.inbox_dirty = False
        except OSError:
            self.inbox_dirty = True

    def on_connected(self, slot_data: dict, received: list[str], log: list[dict] | None = None) -> None:
        self.slot_data = slot_data
        self.received = list(received)
        self.log = log
        # A new connection starts from the server's view: every check of the outbox is offered again, since checks
        # marked as sent while the connection was down never reached the server (the server ignores duplicates).
        self.sent = set()
        self._write_inbox()

    def on_items(self, received: list[str], log: list[dict] | None = None) -> None:
        self.received = list(received)
        self.log = log
        self._write_inbox()

    def set_contracts(self, contracts: dict) -> None:
        self.contracts = contracts
        self._write_inbox()

    def flush_inbox(self) -> None:
        if self.inbox_dirty:
            self._write_inbox()

    def mark_sent(self, checks: Iterable[str]) -> None:
        self.sent |= set(checks)

    def poll(self, now: float | None = None) -> PollResult:
        now = time.time() if now is None else now
        outbox = self.bridge.read_outbox()
        if outbox is None or self.slot_data is None:
            return PollResult()
        active = [name for name, value in self.slot_data["goals"].items() if value > 0]
        goal = bool(active) and all(outbox.goals.get(name) is True for name in active)
        status = "game_connected" if now - outbox.heartbeat <= HEARTBEAT_TIMEOUT else "game_idle"
        year_warning = outbox.year is not None and outbox.year < data.MIN_START_YEAR
        return PollResult(new_checks=self.bridge.new_checks(self.sent), goal_reached=goal, status=status,
                          year_warning=year_warning)


def parse_launch_args(launch_args: Sequence[str]) -> Namespace:
    """Command line of the client: the base Archipelago arguments plus --name and an archipelago:// url."""
    from CommonClient import get_base_parser, handle_url_arg

    parser = get_base_parser(description="Transport Fever 3 client.")
    parser.add_argument("--name", default=None, help="Slot name to connect as.")
    parser.add_argument("url", nargs="?", help="Archipelago connection url (archipelago://name:password@host:port).")
    return handle_url_arg(parser.parse_args(launch_args), parser=parser)


def launch(*launch_args) -> None:
    """Entry point used by the Archipelago Launcher component."""
    from CommonClient import ClientCommandProcessor, CommonContext, gui_enabled, logger, server_loop
    from NetUtils import ClientStatus, NetworkItem

    class TF3CommandProcessor(ClientCommandProcessor):
        def _cmd_folder(self, *path_parts: str) -> bool:
            """Set the folder shared with the game mod: /folder <path to ...\\3493540\\local\\towns_industries>"""
            folder = resolve_userdata_dir(" ".join(path_parts))
            if folder is None:
                self.output("That folder does not exist. Usage: /folder <path to the towns_industries folder>")
                return False
            self.ctx.set_folder(folder)
            self.output(f"Using {folder}")
            return True

        def _cmd_contracts(self, what: str = "") -> bool:
            """List the next open contracts with their reward (/contracts all: every open contract)."""
            for line in contracts_report(self.ctx.contracts, done=self.ctx.checked_names(),
                                         checks=self.ctx.slot_checks(), show_all=what.strip().lower() == "all"):
                self.output(line)
            return True

    class TF3Context(CommonContext):
        game = "Transport Fever 3"
        command_processor = TF3CommandProcessor
        items_handling = 0b111

        def __init__(self, server_address: str | None, password: str | None, userdata_dir: Path | None) -> None:
            super().__init__(server_address, password)
            self.sync = TF3Sync(Bridge(userdata_dir)) if userdata_dir else None
            self.pending_slot: tuple[dict, list[str], list[dict]] | None = None  # kept until a folder is known
            self.poll_task: asyncio.Task | None = None
            self.status_tracker = StatusTracker()
            self.warned_year = False
            self.warned_folder = False
            self.contracts: dict = {}  # check id -> reward, filled from the server's scout reply

        def slot_checks(self) -> dict | None:
            return self.pending_slot[0].get("checks") if self.pending_slot else None

        def checked_names(self) -> set:
            return {self.location_names.lookup_in_slot(code, self.slot) for code in self.checked_locations}

        def set_folder(self, folder: Path) -> None:
            self.sync = TF3Sync(Bridge(folder))
            if self.pending_slot:
                self.sync.on_connected(*self.pending_slot)

        async def server_auth(self, password_requested: bool = False) -> None:
            if password_requested and not self.password:
                await super().server_auth(password_requested)
            await self.get_username()
            await self.send_connect()

        def received_names(self) -> list[str]:
            return [self.item_names.lookup_in_game(item.item, self.game) for item in self.items_received]

        def received_with_sources(self) -> tuple[list[str], list[dict]]:
            names = self.received_names()
            log = received_log(
                [(name, item.location, item.player) for name, item in zip(names, self.items_received)],
                own_slot=self.slot,
                player_name=lambda slot: self.player_names.get(slot),
                location_name=lambda code, slot: self.location_names.lookup_in_slot(code, slot),
            )
            return names, log

        def on_package(self, cmd: str, args: dict) -> None:
            if cmd == "Connected":
                self.pending_slot = (args["slot_data"], *self.received_with_sources())
                if self.sync:
                    self.sync.on_connected(*self.pending_slot)
                if self.poll_task is None or self.poll_task.done():
                    self.poll_task = asyncio.create_task(self.poll_loop(), name="TF3 outbox poll")
                everything = sorted(set(args.get("missing_locations", [])) | set(args.get("checked_locations", [])))
                if everything:
                    asyncio.create_task(self.send_msgs([{"cmd": "LocationScouts", "locations": everything,
                                                         "create_as_hint": 0}]), name="TF3 scout")
            elif cmd == "LocationInfo":
                infos = [(entry.location, entry.item, entry.player) for entry in
                         (NetworkItem(**raw) if isinstance(raw, dict) else raw for raw in args["locations"])]
                self.contracts = contracts_from_scout(
                    infos, own_slot=self.slot,
                    location_name=lambda code: self.location_names.lookup_in_slot(code, self.slot),
                    item_name=lambda code, slot: self.item_names.lookup_in_slot(code, slot),
                    player_name=lambda slot: self.player_names.get(slot))
                if self.sync:
                    self.sync.set_contracts(self.contracts)
            elif cmd == "ReceivedItems" and self.pending_slot:
                self.pending_slot = (self.pending_slot[0], *self.received_with_sources())
                if self.sync:
                    self.sync.on_items(*self.pending_slot[1:])

        def connected_to_server(self) -> bool:
            return self.server is not None and self.slot is not None

        async def poll_loop(self) -> None:
            while not self.exit_event.is_set():
                await self.poll_once()
                await asyncio.sleep(1)

        async def poll_once(self) -> None:
            if self.sync is None:
                if not self.warned_folder:
                    self.warned_folder = True
                    logger.error("Transport Fever 3 user data not found. Type /folder <path to your "
                                 "...\\3493540\\local\\towns_industries folder>, or set TF3_USERDATA_DIR.")
                return
            self.sync.flush_inbox()
            result = self.sync.poll()
            reported = self.status_tracker.update(result.status)
            if reported is not None:
                logger.info({
                    "no_outbox": "Waiting for the game mod (no outbox file for this seed yet).",
                    "game_connected": "Game connected.",
                    "game_idle": "The game mod is not answering (is the game running with the mod?).",
                }[reported])
            if result.year_warning and not self.warned_year:
                self.warned_year = True
                logger.warning(
                    f"The game year is before {data.MIN_START_YEAR}: vehicles of later years stay hidden and "
                    f"no item can unlock them. Create the game with a start year of {data.MIN_START_YEAR} or later."
                )
            if not self.connected_to_server():
                return  # nothing may be marked as sent while the server cannot receive it
            if result.new_checks:
                sent = await self.check_locations(check_ids(result.new_checks))
                self.sync.mark_sent(result.new_checks)
                logger.info(f"Sent {len(sent)} new checks.")
            if result.goal_reached and not self.finished_game:
                self.finished_game = True
                await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                logger.info("Goal reached.")

    async def main(args: Namespace) -> None:
        userdata = find_userdata_dir()
        ctx = TF3Context(args.connect, args.password, userdata)
        ctx.auth = args.name
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        await ctx.exit_event.wait()
        await ctx.shutdown()

    asyncio.run(main(parse_launch_args(launch_args)))
