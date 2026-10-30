import json
from pathlib import Path

MOD = Path(__file__).resolve().parent.parent / "tf3_mod" / "archipelago_tf3_1"


def test_content_json_lists_exactly_the_files_of_the_content_folder():
    listed = set(json.loads((MOD / "_content.json").read_text(encoding="utf-8"))["files"])
    present = {p.name for p in (MOD / "content").iterdir() if p.is_file()}
    assert listed == present


def test_mod_json_points_at_scripts_that_exist():
    mod = json.loads((MOD / "mod.json").read_text(encoding="utf-8"))
    for key in ("runScript", "postRunScript", "preRunScript"):
        name = mod[key]["fileName"]
        if name:
            script = name.split("::/", 1)[1].split("@", 1)[0]
            assert (MOD / "content" / f"{script}.lua").exists(), name


def test_the_notification_icon_is_a_32_bit_tga():
    data = (MOD / "content" / "ap_icon@2x.tga").read_bytes()
    assert data[2] == 2 and data[16] == 32


def test_every_lua_file_of_the_mod_is_valid_syntax():
    import lupa
    from pathlib import Path

    runtime = lupa.LuaRuntime(unpack_returned_tuples=True)
    check = runtime.eval("function(source, name) local chunk, err = load(source, name) return chunk ~= nil, err end")
    root = Path(__file__).resolve().parent.parent / "tf3_mod" / "archipelago_tf3_1"
    for path in sorted(root.rglob("*.lua")):
        valid, error = check(path.read_text(encoding="utf-8"), path.name)
        assert valid, f"{path.name}: {error}"


def test_game_modules_are_required_with_the_game_root_prefix():
    # a path starting with a single slash is looked up inside the mod and fails (it broke the game's own scripts)
    import re
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent / "tf3_mod" / "archipelago_tf3_1"
    bad = []
    for path in sorted(root.rglob("*.lua")):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if re.search(r'ug_require\s*\(?\s*"/', line):
                bad.append(f"{path.name}:{number}")
    assert not bad, bad
