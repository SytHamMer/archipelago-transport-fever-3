"""Link the world package into the Archipelago checkout so Archipelago loads it during tests.

Creates a directory junction ap/worlds/transport_fever_3 -> tf3_world/transport_fever_3 (Windows).
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "tf3_world" / "transport_fever_3"
TARGET = ROOT / "ap" / "worlds" / "transport_fever_3"


def link() -> Path:
    if not SOURCE.is_dir():
        raise SystemExit(f"world package missing: {SOURCE}")
    if TARGET.exists():
        return TARGET
    subprocess.run(["cmd", "/c", "mklink", "/J", str(TARGET), str(SOURCE)], check=True, capture_output=True)
    return TARGET


if __name__ == "__main__":
    print(link())
    sys.exit(0)
