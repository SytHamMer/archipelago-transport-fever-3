"""Read-only extraction of the climates' economy from the game's files.

Usage: python scripts/extract_economy.py "<TF3 install>/base/content" > economy.json

It runs each climate's economy script (economy/<climate>.eco.lua) with stubs for the helper module it requires, reads
each industry's inputs and outputs from its construction file, and reports per climate which industries and cargos
exist, what each cargo depends on, and the company rank that unlocks industries.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

from lupa import LuaRuntime

CLIMATES = {"dry": "dry.eco.lua", "temperate": "temperate.eco.lua", "subarctic": "subarctic.eco.lua",
            "tropical": "tropic.eco.lua"}
SKIPPED_INDUSTRIES = {"shared", "emissive", "farms_shared", "dredging_platform"}
SKIPPED_CARGOS = {"classes", "formats", "icons", "shared", "passengers"}
STOCK = re.compile(r'type\s*=\s*"(INPUT_STOCK|OUTPUT_STOCK)"\s*,\s*cargoType\s*=\s*"::/cargos/(\w+)/')


def industries(content: Path) -> list[str]:
    return sorted(p.stem for p in (content / "industries").glob("*.zip") if p.stem not in SKIPPED_INDUSTRIES)


def cargos(content: Path) -> list[str]:
    return sorted(p.stem for p in (content / "cargos").glob("*.zip") if p.stem not in SKIPPED_CARGOS)


def industry_io(content: Path) -> dict[str, dict[str, list[str]]]:
    """The cargos each industry takes in and puts out, from the stocks of its construction files."""
    result = {}
    for name in industries(content):
        archive = zipfile.ZipFile(content / "industries" / f"{name}.zip")
        inputs, outputs = set(), set()
        for entry in archive.namelist():
            if entry.endswith(".con.lua"):
                for kind, cargo in STOCK.findall(archive.read(entry).decode("utf-8", "replace")):
                    (inputs if kind == "INPUT_STOCK" else outputs).add(cargo)
        result[name] = {"in": sorted(inputs), "out": sorted(outputs)}
    return result


def climate_economy(content: Path, climate: str, filename: str, all_industries: list[str], all_cargos: list[str]) -> dict:
    archive = zipfile.ZipFile(content / "economy.zip")
    lua = LuaRuntime(unpack_returned_tuples=True)
    params = lua.table_from({name: lua.table_from({}) for name in all_industries})
    categories = lua.table_from({name: lua.table_from({}) for name in all_cargos})
    lua.globals()["__params"], lua.globals()["__cats"] = params, categories
    lua.execute("""
        function _(text) return text end
        package.preload["::/economy/placementparamsutil.lua"] = function()
            return {
                getAllParams = function() return __params end,
                getCargoCategories = function() return __cats end,
                removeTags = function() end,
                getDefaultTownLevels2CargoInfos = function() return {} end,
            }
        end
        function require(name) return package.preload[name]() end
    """)
    lua.execute(archive.read(f"economy/{filename}").decode("utf-8"))
    table = lua.eval("data")()
    depends = {cargo: sorted(dict(deps)) for cargo, deps in dict(table["cargoRequiredIndustries"]).items()}
    ranks = {int(rank): sorted(dict(deps)) for rank, deps in dict(table["companyRankRequiredIndustries"]).items()}
    return {
        "industries": sorted(k for k, v in params.items() if v is not None),
        "depends_on": depends,
        "rank_unlocks": ranks,
    }


def extract(content: Path) -> dict:
    all_industries, all_cargos = industries(content), cargos(content)
    return {
        "cargos": all_cargos,
        "industry_io": industry_io(content),
        "climates": {climate: climate_economy(content, climate, filename, all_industries, all_cargos)
                     for climate, filename in CLIMATES.items()},
    }


if __name__ == "__main__":
    print(json.dumps(extract(Path(sys.argv[1])), indent=1, sort_keys=True))
