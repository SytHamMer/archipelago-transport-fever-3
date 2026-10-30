from lua_helpers import MOD_CONTENT, new_runtime


def test_main_script_parses_and_exposes_the_four_game_script_functions():
    runtime = new_runtime()
    runtime.execute((MOD_CONTENT / "ap_main.script.lua").read_text(encoding="utf-8"))
    table = runtime.globals().data()
    assert sorted(key for key, _ in table.items()) == ["guiHandleEvent", "guiUpdate", "handleEvent", "update"]


def test_game_script_registration_points_at_the_main_script():
    runtime = new_runtime()
    runtime.execute((MOD_CONTENT / "ap.gs.lua").read_text(encoding="utf-8"))
    table = runtime.globals().data()
    assert table["guiUpdateScript"]["fileName"] == "ap_main.script@guiUpdate"
