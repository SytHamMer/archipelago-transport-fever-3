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
