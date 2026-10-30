import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Archipelago checkout used for tests.
for path in (ROOT / "ap", ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Stop ModuleUpdate from trying to pip-install the GUI requirements during tests.
import ModuleUpdate  # noqa: E402

ModuleUpdate.update_ran = True

# Archipelago registers the world once, from ap/worlds/transport_fever_3 (a junction to tf3_world/).
# Tests import it under the short name `transport_fever_3`, which is an alias of that same package,
# so the game is never registered twice.
import dev_link  # noqa: E402

dev_link.link()
import worlds.transport_fever_3  # noqa: E402

sys.modules["transport_fever_3"] = worlds.transport_fever_3
