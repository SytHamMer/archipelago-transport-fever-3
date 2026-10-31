import json
import zipfile

import build_world


def test_build_creates_an_apworld_with_the_package_at_its_root(tmp_path):
    archive = build_world.build(tmp_path)
    assert archive == tmp_path / "transport_fever_3.apworld"
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
    assert "transport_fever_3/__init__.py" in names
    assert "transport_fever_3/archipelago.json" in names
    assert "transport_fever_3/client/tf3_client.py" in names


def test_archive_has_no_bytecode_or_cache(tmp_path):
    with zipfile.ZipFile(build_world.build(tmp_path)) as z:
        assert not [n for n in z.namelist() if n.endswith(".pyc") or "__pycache__" in n]


def test_manifest_inside_the_archive_names_the_game(tmp_path):
    with zipfile.ZipFile(build_world.build(tmp_path)) as z:
        manifest = json.loads(z.read("transport_fever_3/archipelago.json"))
    assert manifest["game"] == "Transport Fever 3"
    assert manifest["world_version"] == "2.0.0"
    assert manifest["version"] == 7 and manifest["compatible_version"] == 7


def test_the_manifest_in_the_source_folder_has_no_container_fields():
    # the packaging adds them (see scripts/build_world.py), as Archipelago's own builder does
    source = json.loads((build_world.PACKAGE / "archipelago.json").read_text(encoding="utf-8"))
    assert "version" not in source and "compatible_version" not in source


def test_building_twice_gives_the_same_file_list(tmp_path):
    first = zipfile.ZipFile(build_world.build(tmp_path / "a")).namelist()
    second = zipfile.ZipFile(build_world.build(tmp_path / "b")).namelist()
    assert first == second
