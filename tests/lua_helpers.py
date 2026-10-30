"""Run the mod's pure Lua modules under lupa and convert data between Python and Lua."""
from pathlib import Path

from lupa import LuaRuntime

MOD_CONTENT = Path(__file__).resolve().parent.parent / "tf3_mod" / "archipelago_tf3" / "content"


def new_runtime() -> LuaRuntime:
    return LuaRuntime(unpack_returned_tuples=True)


def load_module(name: str, runtime: LuaRuntime | None = None):
    """Load tf3_mod/archipelago_tf3/content/<name>.lua and return (runtime, module table)."""
    runtime = runtime or new_runtime()
    source = (MOD_CONTENT / f"{name}.lua").read_text(encoding="utf-8")
    return runtime, runtime.execute(source)


def to_lua(runtime: LuaRuntime, value):
    if isinstance(value, dict):
        return runtime.table_from({key: to_lua(runtime, item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return runtime.table_from([to_lua(runtime, item) for item in value])
    return value


def from_lua(value):
    """Lua table to dict/list: a table with keys 1..n becomes a list, an empty table becomes an empty list."""
    if not hasattr(value, "items"):
        return value
    pairs = dict(value.items())
    if not pairs:
        return []
    if all(isinstance(key, int) for key in pairs) and sorted(pairs) == list(range(1, len(pairs) + 1)):
        return [from_lua(pairs[index]) for index in range(1, len(pairs) + 1)]
    return {key: from_lua(item) for key, item in pairs.items()}
