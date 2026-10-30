import pytest

import install_mod


@pytest.fixture
def tree(tmp_path):
    source = tmp_path / "source" / "archipelago_tf3"
    (source / "content").mkdir(parents=True)
    (source / "mod.json").write_text("{}", encoding="utf-8")
    (source / "content" / "a.lua").write_text("-- a", encoding="utf-8")
    local = tmp_path / "local"
    (local / "mods" / "other_mod").mkdir(parents=True)
    (local / "mods" / "other_mod" / "keep.txt").write_text("keep", encoding="utf-8")
    (local / "save").mkdir()
    (local / "save" / "game.sav").write_text("save", encoding="utf-8")
    return source, local / "mods", local


def snapshot(path):
    return {str(p.relative_to(path)): p.read_text(encoding="utf-8") for p in sorted(path.rglob("*")) if p.is_file()}


def test_install_refuses_when_game_running(tree):
    source, mods, _ = tree
    with pytest.raises(install_mod.InstallError, match="running"):
        install_mod.install(source, mods, game_running=lambda: True)
    assert not (mods / "archipelago_tf3").exists()


def test_install_creates_new_folder_only(tree):
    source, mods, local = tree
    before = snapshot(local)
    target = install_mod.install(source, mods, game_running=lambda: False)
    assert target == mods / "archipelago_tf3"
    after = snapshot(local)
    added = set(after) - set(before)
    assert added == {"mods\\archipelago_tf3\\mod.json", "mods\\archipelago_tf3\\content\\a.lua"} or added == {
        "mods/archipelago_tf3/mod.json", "mods/archipelago_tf3/content/a.lua"}
    assert {k: v for k, v in after.items() if k in before} == before  # nothing existing changed, save untouched


def test_install_refuses_existing_folder_without_update(tree):
    source, mods, _ = tree
    install_mod.install(source, mods, game_running=lambda: False)
    with pytest.raises(install_mod.InstallError, match="already exists"):
        install_mod.install(source, mods, game_running=lambda: False)


def test_update_replaces_only_own_folder(tree):
    source, mods, local = tree
    install_mod.install(source, mods, game_running=lambda: False)
    (source / "content" / "a.lua").write_text("-- a v2", encoding="utf-8")
    others_before = snapshot(local / "save"), snapshot(mods / "other_mod")
    install_mod.install(source, mods, update=True, game_running=lambda: False)
    assert (mods / "archipelago_tf3" / "content" / "a.lua").read_text(encoding="utf-8") == "-- a v2"
    assert (snapshot(local / "save"), snapshot(mods / "other_mod")) == others_before


def test_install_refuses_a_target_outside_a_mods_folder(tree, tmp_path):
    source, _, _ = tree
    with pytest.raises(install_mod.InstallError, match="mods"):
        install_mod.install(source, tmp_path / "somewhere", game_running=lambda: False)


def test_find_mods_dir_uses_steam_layout(tmp_path):
    mods = tmp_path / "userdata" / "1" / "3493540" / "local" / "mods"
    mods.mkdir(parents=True)
    assert install_mod.find_mods_dir(steam_root=tmp_path) == mods
    assert install_mod.find_mods_dir(steam_root=tmp_path / "nowhere") is None
