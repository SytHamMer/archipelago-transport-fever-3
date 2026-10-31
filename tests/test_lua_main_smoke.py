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


def test_main_script_has_no_forced_loan_effect_any_more():
    # the loan trap was replaced by money losses; scaling the game's own loans (ap_loans) is a different thing
    source = (MOD_CONTENT / "ap_main.script.lua").read_text(encoding="utf-8").lower()
    assert "forced_loan" not in source and "forced loan" not in source and "makeloan" not in source
