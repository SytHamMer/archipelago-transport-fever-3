"""Development helper: write the mod's inbox as the client would, with the given received item names.

Usage: python scripts/dev_inbox.py [--seed SEED] [ITEM ...]
Loads the bridge modules directly so the Archipelago world package is not imported.
"""
import argparse
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "tf3_world" / "transport_fever_3"
DEFAULT_DIR = Path(r"C:\Program Files (x86)\Steam\userdata\260400121\3493540\local\towns_industries")


def load_bridge():
    package = types.ModuleType("tfpkg")
    package.__path__ = [str(PACKAGE)]
    sys.modules["tfpkg"] = package
    client = types.ModuleType("tfpkg.client")
    client.__path__ = [str(PACKAGE / "client")]
    sys.modules["tfpkg.client"] = client
    for name, path in (("data", "data.py"), ("client.luafile", "client/luafile.py"), ("client.bridge", "client/bridge.py")):
        spec = importlib.util.spec_from_file_location(f"tfpkg.{name}", PACKAGE / path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"tfpkg.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules["tfpkg.client.bridge"].Bridge


def slot_data(seed: str, eras: tuple[int, int] = (1920, 1960)) -> dict:
    return {
        "version": 1, "seed": seed, "eras": {"B": eras[0], "C": eras[1]},
        "goals": {"population": 2500, "company_level": 0, "passengers": 0, "cargo": 0},
        "checks": {"population": [500, 501, 700], "company_level": [2, 3], "passengers": [50, 100], "cargo": [20],
                   "first_line": True, "delivery": [100], "missions": [1, 2, 3]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("items", nargs="*")
    parser.add_argument("--seed", default="manual-test-1")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--eras", type=int, nargs=2, default=(1920, 1960), metavar=("B", "C"))
    parser.add_argument("--sender", help="pretend every item comes from this other player (fills the notification log)")
    parser.add_argument("--where", default="a faraway chest", help="source check shown with --sender")
    parser.add_argument("--contracts", action="store_true", help="add fake contract rewards for the population and level checks")
    args = parser.parse_args()
    args.dir.mkdir(exist_ok=True)
    contracts = {
        "population:1": {"item": "Progressive Rail Vehicles", "to": "Me", "own": True},
        "population:2": {"item": "Cargo Class: Bulk", "to": "Alice", "own": False},
        "population:3": {"item": "Money Grant (large)", "to": "Me", "own": True},
        "company_level:2": {"item": "Money Grant (small)", "to": "Me", "own": True},
    } if args.contracts else None
    log = [{"item": item, "from": args.sender, "where": args.where} for item in args.items] if args.sender else None
    load_bridge()(args.dir).write_inbox(slot_data(args.seed, tuple(args.eras)), args.items, log, contracts)
    print(f"inbox written to {args.dir} with {len(args.items)} items, seed {args.seed}")


if __name__ == "__main__":
    main()
