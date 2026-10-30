"""Generates the Manual data files for Transport Fever 3 and packages the .apworld.

Usage: python build.py <path to Manual repo clone>
Output: dist/manual_transportfever3_mathys.apworld

Check families are generated with many tiers (category "Tier N"). The player picks, per family,
how many tiers are active through a YAML Range option; hooks/Helpers.py drops the rest.
"""
import json
import shutil
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
GAME = "TransportFever3"
CREATOR = "Mathys"
PACKAGE = "manual_transportfever3_mathys"
SCHEMA = "https://github.com/ManualForArchipelago/Manual/raw/main/schemas/Manual.{}.schema.json"
OPTIONS_SCHEMA = "https://raw.githubusercontent.com/ManualForArchipelago/Manual/main/schemas/Manual.options.schema.json"

MODES = ["Road Transport", "Tram Transport", "Rail Transport", "Water Transport", "Air Transport"]
ANY_MODE = "|@Transport Modes:1|"

# Source: TF3 install, base/content/economy.zip (temperate.eco.lua) and base/content/cargos.
# Mail does not exist in TF3. Climate changes the cargo set; this covers temperate.
# Industries spawn with game progression (company rank only unlocks one extra placeable), so
# cargo availability is not gated by rank here.
CARGO = [
    "Passengers", "Grain", "Vegetables", "Meat", "Fish", "Clay", "Bricks", "Stone", "Coal", "Iron Ore",
    "Steel", "Sheet Metal", "Machines", "Vehicles", "Crude Oil", "Fuel", "Chemicals", "Dyes", "Clothes",
    "Fabric", "Logs", "Planks", "Tools", "Tinned Food", "Sand", "Glass", "Furniture", "Beverages",
]

VEHICLE_TIERS = {"Road": 3, "Tram": 3, "Rail": 4, "Water": 3, "Air": 3}

# family -> (option name, default tiers active, option description)
FAMILIES = {
    "Population": ("population_checks", 4, "Number of total-population milestones that are checks."),
    "Company Level": ("company_level_checks", 5, "Number of company level milestones that are checks (levels 2, 3, 4...)."),
    "Towns": ("town_size_checks", 2, "Number of 'one town reaches N inhabitants' milestones that are checks."),
    "Town Connections": ("town_connection_checks", 3, "Number of 'connect N towns' milestones that are checks."),
    "Industry Connections": ("industry_connection_checks", 3, "Number of 'connect N industries' milestones that are checks."),
    "Deliveries": ("delivery_checks", 1, "Number of delivery milestones per cargo type that are checks."),
    "Company Value": ("company_value_checks", 3, "Number of company value milestones that are checks."),
    "Yearly Profit": ("yearly_profit_checks", 2, "Number of yearly profit milestones that are checks."),
}

POPULATION = [250, 500, 1000, 2000, 3500, 5000, 7500, 10000, 15000, 25000, 50000, 100000]
TOWN_SIZE = [200, 500, 1000, 2000, 5000, 10000]
TOWN_CONN = [2, 3, 5, 8, 12, 20, 30, 40]
INDUSTRY_CONN = [1, 2, 3, 5, 8, 12, 20, 30]
DELIVERY = [100, 500, 2000, 10000]
COMPANY_VALUE = [(100_000, "$100K"), (500_000, "$500K"), (1_000_000, "$1M"), (5_000_000, "$5M"),
                 (20_000_000, "$20M"), (100_000_000, "$100M"), (500_000_000, "$500M"), (1_000_000_000, "$1B")]
YEARLY_PROFIT = [(10_000, "$10K"), (50_000, "$50K"), (250_000, "$250K"), (1_000_000, "$1M"),
                 (5_000_000, "$5M"), (20_000_000, "$20M")]
MAX_LEVEL = 15


def modes_for_fraction(i, n, top=4):
    """Modes needed for tier i (0-based) of n: 1 early, up to `top` for the last tiers."""
    return 1 + (i * (top - 1)) // max(n - 1, 1)


def pop_req(pop):
    modes = 1 if pop < 15_000 else 2 if pop < 50_000 else 3
    req = f"|@Transport Modes:{modes}|"
    if pop >= 25_000:
        req += " and |Progressive Era:1|"
    return req


def level_req(lvl):
    modes = 1 if lvl < 5 else 2 if lvl < 9 else 3 if lvl < 12 else 4
    req = f"|@Transport Modes:{modes}|"
    if lvl >= 8:
        req += " and |Progressive Era:1|"
    if lvl >= 12:
        req += " and |Progressive Era:2|"
    return req


def items():
    out = []
    for m in MODES:
        out.append({"name": m, "category": ["Transport Modes"], "progression": True})
    for mode, n in VEHICLE_TIERS.items():
        out.append({
            "name": f"Progressive {mode} Vehicles", "count": n,
            "category": ["Vehicles"], "progression": True,
        })
    out.append({"name": "Progressive Era", "count": 3, "category": ["Eras"], "progression": True})
    for c in CARGO:
        out.append({"name": f"Cargo: {c}", "category": ["Cargo"], "progression": True})
    out.append({"name": "Station Construction Permit", "category": ["Construction"], "useful": True})
    out.append({"name": "Depot Construction Permit", "category": ["Construction"], "useful": True})
    out.append({"name": "Money Grant", "category": ["Filler"], "filler": True, "count": 20})
    for trap in ("Breakdown Wave", "Forced Loan", "Maintenance Cost Spike"):
        out.append({"name": trap, "category": ["Traps"], "trap": True, "count": 3})
    return out


def locations():
    out = []

    def loc(name, family, tier, requires, extra_cat=()):
        d = {"name": name, "category": [family, f"Tier {tier}", *extra_cat]}
        if requires:
            d["requires"] = requires
        out.append(d)

    for i, pop in enumerate(POPULATION, 1):
        loc(f"Total population reaches {pop:,}", "Population", i, pop_req(pop))

    for i, lvl in enumerate(range(2, MAX_LEVEL + 1), 1):
        loc(f"Company reaches level {lvl}", "Company Level", i, level_req(lvl))

    for i, pop in enumerate(TOWN_SIZE, 1):
        modes = 1 if pop < 5000 else 2 if pop < 10000 else 3
        loc(f"Any town reaches {pop:,} inhabitants", "Towns", i, f"|@Transport Modes:{modes}|")

    for i, n in enumerate(TOWN_CONN, 1):
        loc(f"Connect {n} towns", "Town Connections", i, f"|@Transport Modes:{1 if n < 12 else 2}|")
    for i, n in enumerate(INDUSTRY_CONN, 1):
        loc(f"Connect {n} industries", "Industry Connections", i, f"|@Transport Modes:{1 if n < 8 else 2}|")

    for m in MODES:
        out.append({
            "name": f"First {m.split()[0].lower()} line", "category": ["First Lines"],
            "requires": f"|{m}|",
        })

    for tier, amount in enumerate(DELIVERY, 1):
        for c in CARGO:
            loc(f"Deliver {amount:,} units of {c}", "Deliveries", tier,
                f"{ANY_MODE} and |Cargo: {c}|", extra_cat=[c])

    for i, (_, label) in enumerate(COMPANY_VALUE, 1):
        loc(f"Company value reaches {label}", "Company Value", i, f"|@Transport Modes:{modes_for_fraction(i - 1, len(COMPANY_VALUE), 3)}|")
    for i, (_, label) in enumerate(YEARLY_PROFIT, 1):
        loc(f"Yearly profit reaches {label}", "Yearly Profit", i, f"|@Transport Modes:{modes_for_fraction(i - 1, len(YEARLY_PROFIT), 3)}|")

    # Goals (victory): each one is a value of the `goal` option. Order = option order, first is default.
    for pop in (2_500, 5_000, 10_000, 25_000, 50_000):
        out.append({
            "name": f"Goal: reach {pop:,} total inhabitants", "victory": True,
            "category": ["Goals"], "requires": pop_req(pop),
        })
    for lvl in (5, 8, 10, 12, 15):
        out.append({
            "name": f"Goal: reach company level {lvl}", "victory": True,
            "category": ["Goals"], "requires": level_req(lvl),
        })
    return out


def options():
    user = {
        "first_line_checks": {
            "type": "Toggle", "default": True, "group": "Checks",
            "description": "Building the first line of each transport mode is a check.",
        },
    }
    for family, (name, default, desc) in FAMILIES.items():
        top = {
            "Population": len(POPULATION), "Company Level": MAX_LEVEL - 1, "Towns": len(TOWN_SIZE),
            "Town Connections": len(TOWN_CONN), "Industry Connections": len(INDUSTRY_CONN),
            "Deliveries": len(DELIVERY), "Company Value": len(COMPANY_VALUE),
            "Yearly Profit": len(YEARLY_PROFIT),
        }[family]
        user[name] = {
            "type": "Range", "range_start": 0, "range_end": top, "default": default, "group": "Checks",
            "description": [desc, "0 disables the family. Tiers go from the easiest upwards."],
        }
    return {
        "$schema": OPTIONS_SCHEMA,
        "core": {"death_link": {"default": False}, "filler_traps": {"values": {"recommended": 15}}},
        "user": user,
    }


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def main(manual_repo):
    src = Path(manual_repo) / "src"
    stage = HERE / "build" / PACKAGE
    if stage.parent.exists():
        shutil.rmtree(stage.parent)
    shutil.copytree(src, stage, ignore=shutil.ignore_patterns("test", "__pycache__", "docs"))
    data = stage / "data"

    hook = (HERE / "hooks" / "Helpers.py").read_text(encoding="utf-8")
    table = {f: v[0] for f, v in FAMILIES.items()}
    hook = hook.replace("FAMILY_OPTIONS: dict[str, str] = {}  # @@FAMILIES@@",
                        f"FAMILY_OPTIONS: dict[str, str] = {table!r}")
    assert "@@FAMILIES@@" not in hook
    (stage / "hooks" / "Helpers.py").write_text(hook, encoding="utf-8")
    shutil.copy(HERE / "hooks" / "World.py", stage / "hooks" / "World.py")
    shutil.copy(Path(manual_repo) / "templates" / "archipelago.json", stage / "archipelago.json")

    game = {
        "$schema": SCHEMA.format("game"),
        "game": GAME, "creator": CREATOR,
        "filler_item_name": "Money Grant",
        "starting_items": [{"items": ["Road Transport", "Cargo: Passengers"]}],
        "death_link": False,
        "starting_index": 1,
        "unused_goals_are_locations": False,
    }
    locs = locations()
    dump(data / "game.json", game)
    dump(data / "items.json", {"$schema": SCHEMA.format("items"), "data": items()})
    dump(data / "locations.json", {"$schema": SCHEMA.format("locations"), "data": locs})
    dump(data / "regions.json", {"$schema": SCHEMA.format("regions")})
    dump(data / "events.json", {"$schema": SCHEMA.format("events"), "data": []})
    dump(data / "categories.json", {"$schema": SCHEMA.format("categories")})
    dump(data / "options.json", options())

    dist = HERE / "dist"
    dist.mkdir(exist_ok=True)
    out = dist / f"{PACKAGE}.apworld"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for p in stage.rglob("*"):
            if p.is_file():
                z.write(p, Path(PACKAGE) / p.relative_to(stage))
    print(f"built {out} ({len(locs)} locations, {len(items())} item entries)")


if __name__ == "__main__":
    main(sys.argv[1])
