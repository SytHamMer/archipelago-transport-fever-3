"""Development helper: switch the subvention experiment on (or off with --off) in the exchange folder."""
import argparse
from pathlib import Path

DEFAULT_DIR = Path(r"C:\Program Files (x86)\Steam\userdata\260400121\3493540\local\towns_industries")

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
parser.add_argument("--off", action="store_true")
args = parser.parse_args()
flag = args.dir / "archipelago_tf3_experiment.lua"
if args.off:
    flag.unlink(missing_ok=True)
    print("experiment off")
else:
    flag.write_text("function data()\nreturn { enabled = true }\nend\n", encoding="utf-8")
    print("experiment on:", flag)
