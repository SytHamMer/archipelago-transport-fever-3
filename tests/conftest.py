import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Archipelago checkout used for tests, and the world package under development.
for path in (ROOT / "ap", ROOT / "tf3_world"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Stop ModuleUpdate from trying to pip-install the GUI requirements during tests.
import ModuleUpdate  # noqa: E402

ModuleUpdate.update_ran = True
