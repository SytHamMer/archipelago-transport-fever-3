"""Package the world as dist/transport_fever_3.apworld (a zip whose root folder is the world package)."""
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "tf3_world" / "transport_fever_3"
DEFAULT_OUT = ROOT / "dist"
MANIFEST = "archipelago.json"
# The packaging scheme of Archipelago's .apworld files (Archipelago's worlds/Files.py, container_version): the
# official "Build APWorlds" component adds these two fields to the manifest, a world folder must not carry them.
CONTAINER = {"version": 7, "compatible_version": 7}


def build(out_dir: Path = DEFAULT_OUT) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / "transport_fever_3.apworld"
    files = sorted(
        path for path in PACKAGE.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc"
    )
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            name = Path("transport_fever_3") / path.relative_to(PACKAGE)
            if path.name == MANIFEST:
                z.writestr(str(name), json.dumps({**json.loads(path.read_text(encoding="utf-8")), **CONTAINER}, indent=4))
            else:
                z.write(path, name)
    return archive


if __name__ == "__main__":
    print(build())
    sys.exit(0)
