"""Archipelago client for Transport Fever 3: relays between the server and the game mod through two files."""
import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path

from ..Locations import location_table
from .bridge import Bridge

STEAM_ROOT = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam"
TF3_APP_ID = "3493540"
EXCHANGE_FOLDER = "towns_industries"  # one of the two userdata folders the game lets mods use
HEARTBEAT_TIMEOUT = 10  # seconds without a mod heartbeat before the game counts as idle


def find_userdata_dir(steam_root: Path | None = None, override: str | None = None) -> Path | None:
    """The folder shared with the mod, or None when TF3's user data cannot be found."""
    override = override or os.environ.get("TF3_USERDATA_DIR")
    if override:
        return Path(override)
    root = Path(steam_root) if steam_root is not None else STEAM_ROOT
    for local in sorted((root / "userdata").glob(f"*/{TF3_APP_ID}/local")):
        folder = local / EXCHANGE_FOLDER
        folder.mkdir(exist_ok=True)
        return folder
    return None


def check_ids(names) -> list[int]:
    """Archipelago location ids for the check names the mod reported (unknown names are skipped)."""
    return sorted(location_table[name] for name in names if name in location_table)


@dataclass
class PollResult:
    new_checks: set = field(default_factory=set)
    goal_reached: bool = False
    status: str = "no_outbox"  # no_outbox, seed_mismatch, game_connected or game_idle


class TF3Sync:
    """The logic of the client, independent of the network: slot state in, checks and goal status out."""

    def __init__(self, bridge: Bridge):
        self.bridge = bridge
        self.slot_data: dict | None = None
        self.received: list[str] = []
        self.sent: set = set()

    def on_connected(self, slot_data: dict, received: list[str]) -> None:
        self.slot_data = slot_data
        self.received = list(received)
        self.bridge.write_inbox(slot_data, self.received)

    def on_items(self, received: list[str]) -> None:
        self.received = list(received)
        if self.slot_data is not None:
            self.bridge.write_inbox(self.slot_data, self.received)

    def mark_sent(self, checks) -> None:
        self.sent |= set(checks)

    def poll(self, now: float | None = None) -> PollResult:
        now = time.time() if now is None else now
        outbox = self.bridge.read_outbox()
        if outbox is None or self.slot_data is None:
            return PollResult()
        if not self.bridge.seed_matches():
            return PollResult(status="seed_mismatch")
        active = [name for name, value in self.slot_data["goals"].items() if value > 0]
        goal = bool(active) and all(outbox.goals.get(name) is True for name in active)
        status = "game_connected" if now - outbox.heartbeat <= HEARTBEAT_TIMEOUT else "game_idle"
        return PollResult(new_checks=self.bridge.new_checks(self.sent), goal_reached=goal, status=status)


def launch(*launch_args) -> None:
    """Entry point used by the Archipelago Launcher component."""
    from CommonClient import ClientCommandProcessor, CommonContext, get_base_parser, gui_enabled, logger, server_loop
    from NetUtils import ClientStatus

    class TF3Context(CommonContext):
        game = "Transport Fever 3"
        command_processor = ClientCommandProcessor
        items_handling = 0b111

        def __init__(self, server_address, password, userdata_dir: Path):
            super().__init__(server_address, password)
            self.sync = TF3Sync(Bridge(userdata_dir))
            self.poll_task: asyncio.Task | None = None
            self.last_status = ""

        async def server_auth(self, password_requested: bool = False):
            if password_requested and not self.password:
                await super().server_auth(password_requested)
            await self.get_username()
            await self.send_connect()

        def received_names(self) -> list[str]:
            return [self.item_names.lookup_in_game(item.item, self.game) for item in self.items_received]

        def on_package(self, cmd: str, args: dict) -> None:
            if cmd == "Connected":
                self.sync.on_connected(args["slot_data"], self.received_names())
                if self.poll_task is None or self.poll_task.done():
                    self.poll_task = asyncio.create_task(self.poll_loop(), name="TF3 outbox poll")
            elif cmd == "ReceivedItems":
                self.sync.on_items(self.received_names())

        async def poll_loop(self) -> None:
            while not self.exit_event.is_set():
                result = self.sync.poll()
                if result.status != self.last_status:
                    self.last_status = result.status
                    logger.info({
                        "no_outbox": "Waiting for the game mod (no outbox file yet).",
                        "seed_mismatch": "The game's outbox belongs to another seed: start a new game with this seed.",
                        "game_connected": "Game connected.",
                        "game_idle": "The game mod is not answering (is the game running with the mod?).",
                    }[result.status])
                if result.new_checks:
                    sent = await self.check_locations(check_ids(result.new_checks))
                    self.sync.mark_sent(result.new_checks)
                    logger.info(f"Sent {len(sent)} new checks.")
                if result.goal_reached and not self.finished_game:
                    self.finished_game = True
                    await self.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                    logger.info("Goal reached.")
                await asyncio.sleep(1)

    async def main(args) -> None:
        userdata = find_userdata_dir()
        if userdata is None:
            logger.error("Transport Fever 3 user data not found. Set TF3_USERDATA_DIR to the towns_industries folder.")
            return
        ctx = TF3Context(args.connect, args.password, userdata)
        ctx.auth = args.name
        ctx.server_task = asyncio.create_task(server_loop(ctx), name="server loop")
        if gui_enabled:
            ctx.run_gui()
        ctx.run_cli()
        await ctx.exit_event.wait()
        await ctx.shutdown()

    parser = get_base_parser(description="Transport Fever 3 client.")
    args = parser.parse_args(launch_args)
    asyncio.run(main(args))
