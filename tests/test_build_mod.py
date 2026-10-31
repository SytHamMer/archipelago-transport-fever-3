import zipfile

import build_mod


def test_build_creates_a_zip_with_the_mod_folder_at_its_root(tmp_path):
    archive = build_mod.build(tmp_path)
    assert archive == tmp_path / "archipelago_tf3_1.zip"
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
    assert "archipelago_tf3_1/mod.json" in names
    assert "archipelago_tf3_1/content/ap_main.script.lua" in names
    assert all(name.startswith("archipelago_tf3_1/") for name in names)


def test_every_file_of_the_mod_is_in_the_zip(tmp_path):
    with zipfile.ZipFile(build_mod.build(tmp_path)) as z:
        packed = {name for name in z.namelist() if not name.endswith("/")}
    source = {f"archipelago_tf3_1/{path.relative_to(build_mod.MOD_SOURCE).as_posix()}"
              for path in build_mod.MOD_SOURCE.rglob("*") if path.is_file()}
    assert packed == source
