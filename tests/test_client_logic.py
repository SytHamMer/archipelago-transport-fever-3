import pytest

from transport_fever_3.Locations import location_table
from transport_fever_3.client import luafile
from transport_fever_3.client.bridge import Bridge
from transport_fever_3.client.tf3_client import TF3Sync, check_ids, find_userdata_dir

NOW = 1_000_000


def slot(**goals):
    base = {"population": 0, "company_level": 0, "passengers": 0, "cargo": 0}
    base.update(goals)
    return {
        "version": 1, "seed": "seed-1", "goals": base,
        "checks": {"population": [500], "company_level": [2], "passengers": [], "cargo": [], "first_line": True, "delivery": []},
    }


def outbox(tmp_path, **overrides):
    value = {"version": 1, "seed": "seed-1", "checks": [], "goals": {}, "applied": 0, "heartbeat": NOW}
    value.update(overrides)
    (tmp_path / f"archipelago_tf3_outbox_{value['seed']}.lua").write_text(luafile.dumps(value), encoding="utf-8")


@pytest.fixture
def sync(tmp_path):
    return TF3Sync(Bridge(tmp_path))


def test_goal_sent_only_when_all_active_goals_true(sync, tmp_path):
    sync.on_connected(slot(population=100, cargo=50), [])
    outbox(tmp_path, goals={"population": True, "cargo": False})
    assert sync.poll(NOW).goal_reached is False
    outbox(tmp_path, goals={"population": True, "cargo": True})
    assert sync.poll(NOW).goal_reached is True


def test_inactive_goal_is_ignored(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, goals={"population": True, "cargo": False})
    assert sync.poll(NOW).goal_reached is True


def test_no_goal_reached_before_any_outbox(sync):
    sync.on_connected(slot(population=100), [])
    result = sync.poll(NOW)
    assert result.goal_reached is False and result.status == "no_outbox"


def test_corrupt_outbox_sends_nothing(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    (tmp_path / "archipelago_tf3_outbox_seed-1.lua").write_text("function data()\nreturn { checks = { \"popul", encoding="utf-8")
    result = sync.poll(NOW)
    assert result.new_checks == set() and result.goal_reached is False


def test_new_checks_are_reported_once_after_mark_sent(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, checks=["population:1", "line:road"])
    first = sync.poll(NOW)
    assert first.new_checks == {"population:1", "line:road"}
    sync.mark_sent(first.new_checks)
    assert sync.poll(NOW).new_checks == set()


def test_checks_from_a_previous_connection_are_still_sent(sync, tmp_path):
    outbox(tmp_path, checks=["line:road"])
    sync.on_connected(slot(population=100), [])
    assert sync.poll(NOW).new_checks == {"line:road"}


def test_status_follows_heartbeat(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, heartbeat=NOW - 3)
    assert sync.poll(NOW).status == "game_connected"
    outbox(tmp_path, heartbeat=NOW - 60)
    assert sync.poll(NOW).status == "game_idle"


def test_outbox_of_another_seed_is_ignored(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, seed="old", checks=["line:road"], goals={"population": True})
    result = sync.poll(NOW)
    assert result.status == "no_outbox"
    assert result.new_checks == set() and result.goal_reached is False


def test_reconnect_resends_checks_that_were_marked_sent_while_offline(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, checks=["line:road"])
    sync.mark_sent(sync.poll(NOW).new_checks)  # marked while the socket was down: the server never got it
    assert sync.poll(NOW).new_checks == set()
    sync.on_connected(slot(population=100), [])  # reconnection
    assert sync.poll(NOW).new_checks == {"line:road"}


def test_failed_inbox_write_is_kept_for_a_retry_not_raised(sync, tmp_path, monkeypatch):
    calls = []
    real = sync.bridge.write_inbox

    def flaky(slot_data, received, log=None, contracts=None):
        calls.append(1)
        if len(calls) == 1:
            raise PermissionError("busy")
        real(slot_data, received, log, contracts)

    monkeypatch.setattr(sync.bridge, "write_inbox", flaky)
    sync.on_connected(slot(population=100), ["Rail Transport"])  # must not raise
    assert sync.inbox_dirty is True
    sync.flush_inbox()
    assert sync.inbox_dirty is False
    assert (tmp_path / "archipelago_tf3_inbox.lua").exists()


def test_flush_inbox_does_nothing_when_clean(sync):
    sync.on_connected(slot(population=100), [])
    assert sync.inbox_dirty is False
    sync.flush_inbox()
    assert sync.inbox_dirty is False


def test_find_userdata_dir_prefers_the_most_recently_used_account(tmp_path):
    import os

    old = tmp_path / "userdata" / "111" / "3493540" / "local"
    new = tmp_path / "userdata" / "222" / "3493540" / "local"
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    os.utime(old, (1_000_000, 1_000_000))
    os.utime(new, (2_000_000, 2_000_000))
    assert find_userdata_dir(steam_root=tmp_path) == new / "towns_industries"


def test_resolve_userdata_dir_accepts_an_existing_folder_only(tmp_path):
    from transport_fever_3.client.tf3_client import resolve_userdata_dir

    assert resolve_userdata_dir(str(tmp_path)) == tmp_path
    assert resolve_userdata_dir(f'"{tmp_path}"') == tmp_path  # quotes pasted from the Explorer
    assert resolve_userdata_dir(str(tmp_path / "nowhere")) is None
    assert resolve_userdata_dir("") is None


def test_items_update_rewrites_the_inbox(sync, tmp_path):
    sync.on_connected(slot(population=100), ["Rail Transport"])
    sync.on_items(["Rail Transport", "Money Grant (small)"])
    inbox = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))
    assert inbox["items"] == {"Rail Transport": 1, "Money Grant (small)": 1}
    assert [e["id"] for e in inbox["effects"]] == [2]


def test_items_before_connection_are_ignored(sync, tmp_path):
    sync.on_items(["Rail Transport"])
    assert not (tmp_path / "archipelago_tf3_inbox.lua").exists()


def test_check_ids_maps_known_names_and_skips_unknown():
    assert check_ids({"population:1", "no-such-check"}) == [location_table["population:1"]]


def test_find_userdata_dir_uses_steam_layout_and_creates_folder(tmp_path):
    local = tmp_path / "userdata" / "123" / "3493540" / "local"
    local.mkdir(parents=True)
    found = find_userdata_dir(steam_root=tmp_path)
    assert found == local / "towns_industries" and found.is_dir()


def test_find_userdata_dir_missing_returns_none(tmp_path):
    assert find_userdata_dir(steam_root=tmp_path) is None


def test_find_userdata_dir_override_wins(tmp_path):
    custom = tmp_path / "custom"
    custom.mkdir()
    assert find_userdata_dir(steam_root=tmp_path, override=str(custom)) == custom


def test_launcher_component_is_registered():
    from worlds.LauncherComponents import Type, components

    matches = [c for c in components if c.display_name == "Transport Fever 3 Client"]
    assert len(matches) == 1
    assert matches[0].type == Type.CLIENT
    assert callable(matches[0].func)


def test_launch_args_accept_name_and_connect():
    from transport_fever_3.client.tf3_client import parse_launch_args

    args = parse_launch_args(["--connect", "localhost:38281", "--name", "Mathys"])
    assert args.connect == "localhost:38281" and args.name == "Mathys"


def test_launch_args_accept_an_archipelago_url():
    from transport_fever_3.client.tf3_client import parse_launch_args

    args = parse_launch_args(["archipelago://Mathys:secret@example.org:38281"])
    assert args.connect.endswith("example.org:38281")  # Archipelago keeps the credentials in the netloc
    assert args.name == "Mathys" and args.password == "secret"


def test_launch_args_without_anything_are_valid():
    from transport_fever_3.client.tf3_client import parse_launch_args

    args = parse_launch_args([])
    assert args.connect is None and args.name is None


def test_low_game_year_raises_a_warning(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, year=1890)
    assert sync.poll(NOW).year_warning is True


def test_late_or_unknown_game_year_has_no_warning(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, year=2020)
    assert sync.poll(NOW).year_warning is False
    outbox(tmp_path)
    assert sync.poll(NOW).year_warning is False


def test_received_log_names_the_sender_and_the_source_check():
    from transport_fever_3.client.tf3_client import received_log

    names = {1: "Me", 2: "Alice"}
    where = {(7400001, 1): "population:1", (55, 2): "Alice's chest"}
    log = received_log(
        [("Money Grant (small)", 7400001, 1), ("Rail Transport", 55, 2)],
        own_slot=1, player_name=names.get, location_name=lambda code, slot: where[(code, slot)],
    )
    assert log == [
        {"item": "Money Grant (small)", "own": True, "where": "population:1"},
        {"item": "Rail Transport", "from": "Alice", "where": "Alice's chest"},
    ]


def test_received_log_leaves_out_a_location_that_cannot_be_named():
    from transport_fever_3.client.tf3_client import received_log

    def unknown(code, slot):
        raise KeyError(code)

    log = received_log([("Rail Transport", -2, 0)], own_slot=1, player_name={0: "Archipelago"}.get, location_name=unknown)
    assert log == [{"item": "Rail Transport", "from": "Archipelago"}]


def test_sync_passes_the_log_to_the_inbox(sync, tmp_path):
    log = [{"item": "Rail Transport", "from": "Alice", "where": "chest"}]
    sync.on_connected(slot(population=100), ["Rail Transport"], log)
    assert luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["log"] == log
    more = log + [{"item": "Tram Transport", "own": True, "where": "population:1"}]
    sync.on_items(["Rail Transport", "Tram Transport"], more)
    assert luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["log"] == more


def test_a_brief_missing_outbox_does_not_change_the_reported_status():
    from transport_fever_3.client.tf3_client import StatusTracker

    tracker = StatusTracker()
    assert tracker.update("game_connected") == "game_connected"
    assert tracker.update("no_outbox") is None  # half-written file: ignored
    assert tracker.update("no_outbox") is None
    assert tracker.update("game_connected") is None  # back to the same status: nothing to say


def test_a_missing_outbox_that_lasts_is_reported():
    from transport_fever_3.client.tf3_client import StatusTracker

    tracker = StatusTracker()
    tracker.update("game_connected")
    results = [tracker.update("no_outbox") for _ in range(StatusTracker.NO_OUTBOX_POLLS)]
    assert results[:-1] == [None] * (StatusTracker.NO_OUTBOX_POLLS - 1) and results[-1] == "no_outbox"


def test_the_first_status_is_always_reported_and_real_changes_are_immediate():
    from transport_fever_3.client.tf3_client import StatusTracker

    tracker = StatusTracker()
    assert tracker.update("no_outbox") == "no_outbox"
    assert tracker.update("game_idle") == "game_idle"
    assert tracker.update("game_connected") == "game_connected"
