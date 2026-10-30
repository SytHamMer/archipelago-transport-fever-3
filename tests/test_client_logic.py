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
    (tmp_path / "archipelago_tf3_outbox.lua").write_text(luafile.dumps(value), encoding="utf-8")


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
    (tmp_path / "archipelago_tf3_outbox.lua").write_text("function data()\nreturn { checks = { \"popul", encoding="utf-8")
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


def test_seed_mismatch_sends_nothing_and_is_reported(sync, tmp_path):
    sync.on_connected(slot(population=100), [])
    outbox(tmp_path, seed="old", checks=["line:road"], goals={"population": True})
    result = sync.poll(NOW)
    assert result.status == "seed_mismatch"
    assert result.new_checks == set() and result.goal_reached is False


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
