"""Package the mod as dist/archipelago_tf3_1.zip (a zip whose root folder is the mod folder, to extract in the mods folder)."""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MOD_SOURCE = ROOT / "tf3_mod" / "archipelago_tf3_1"
DEFAULT_OUT = ROOT / "dist"


def build(out_dir: Path = DEFAULT_OUT) -> Path:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    archive = out_dir / f"{MOD_SOURCE.name}.zip"
    files = sorted(path for path in MOD_SOURCE.rglob("*") if path.is_file())
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, Path(MOD_SOURCE.name) / path.relative_to(MOD_SOURCE))
    return archive


if __name__ == "__main__":
    print(build())
    sys.exit(0)
