"""Install the TF3 mod as a new folder in the game's user mods directory.

Only that one folder is ever written. The game install, the saves and other mods are never touched.
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_SOURCE = ROOT / "tf3_mod" / "archipelago_tf3_1"
STEAM_ROOT = Path(r"C:\Program Files (x86)\Steam")
TF3_APP_ID = "3493540"


class InstallError(RuntimeError):
    pass


def game_is_running() -> bool:
    out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq TransportFever3.exe"], capture_output=True, text=True)
    return "TransportFever3.exe" in out.stdout


def find_mods_dir(steam_root: Path | None = None) -> Path | None:
    root = Path(steam_root) if steam_root is not None else STEAM_ROOT
    for local in sorted((root / "userdata").glob(f"*/{TF3_APP_ID}/local")):
        if (local / "mods").is_dir():
            return local / "mods"
    return None


def install(source: Path, mods_dir: Path, update: bool = False, game_running=game_is_running) -> Path:
    source, mods_dir = Path(source), Path(mods_dir)
    if mods_dir.name != "mods":
        raise InstallError(f"{mods_dir} is not a 'mods' folder; refusing to write there.")
    if game_running():
        raise InstallError("Transport Fever 3 is running: close the game before installing the mod.")
    target = mods_dir / source.name
    if target.exists() and not update:
        raise InstallError(f"{target} already exists; use --update to replace the mod files.")
    shutil.copytree(source, target, dirs_exist_ok=True)
    if update:
        remove_stale(source, target)
    return target


def remove_stale(source: Path, target: Path) -> None:
    """Delete what an earlier version left in the installed copy and the source no longer has (that folder only)."""
    for path in sorted(target.rglob("*"), key=lambda item: len(item.parts), reverse=True):
        if (source / path.relative_to(target)).exists():
            continue
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="replace the files of an installed copy")
    parser.add_argument("--mods-dir", type=Path, help="override the detected user mods folder")
    args = parser.parse_args()
    mods = args.mods_dir or find_mods_dir()
    if mods is None:
        print("TF3 user mods folder not found; pass --mods-dir.", file=sys.stderr)
        return 1
    try:
        print(install(MOD_SOURCE, mods, update=args.update))
    except InstallError as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
