from transport_fever_3.client import luafile
from transport_fever_3.client.bridge import INBOX_NAME, Bridge
from transport_fever_3.client.tf3_client import COOLDOWN_SECONDS, TF3Sync, death_effect

SLOT = {
    "version": 1, "seed": "seed-1", "goals": {"population": 0, "company_level": 0, "passengers": 0, "cargo": 0},
    "checks": {"population": [500], "company_level": [], "passengers": [], "cargo": [], "first_line": False, "delivery": []},
    "money_scale": 100, "death_link": True,
}


def death(source="Alice", cause="Alice fell into lava", time=1_000.5):
    return {"time": time, "source": source, "cause": cause}


def test_a_death_becomes_a_money_loss_with_a_stable_id():
    effect = death_effect(death(), own_name="Mathys", money_scale=100)
    assert effect == {"id": 1_000_500, "amount": 1_000_000, "source": "Alice", "cause": "Alice fell into lava"}


def test_the_loss_follows_the_money_scale():
    assert death_effect(death(), "Mathys", money_scale=50)["amount"] == 500_000


def test_our_own_deaths_and_malformed_ones_are_ignored():
    assert death_effect(death(source="Mathys"), "Mathys", 100) is None
    assert death_effect({"source": "Alice"}, "Mathys", 100) is None
    assert death_effect({"time": "x", "source": "Alice"}, "Mathys", 100) is None


def test_a_death_without_a_cause_still_has_a_text():
    effect = death_effect({"time": 5.0, "source": "Alice"}, "Mathys", 100)
    assert effect["cause"] == "" and effect["source"] == "Alice"


def test_the_inbox_carries_the_deaths_only_when_there_are_some(tmp_path):
    bridge = Bridge(tmp_path)
    bridge.write_inbox(SLOT, [])
    assert "deaths" not in luafile.loads((tmp_path / INBOX_NAME).read_text(encoding="utf-8"))
    deaths = [{"id": 5, "amount": 1_000_000, "source": "Alice", "cause": 'fell "off"'}]
    bridge.write_inbox(SLOT, [], deaths=deaths)
    assert luafile.loads((tmp_path / INBOX_NAME).read_text(encoding="utf-8"))["deaths"] == deaths


def make_sync(tmp_path):
    sync = TF3Sync(Bridge(tmp_path), own_name="Mathys")
    sync.on_connected(SLOT, [])
    return sync


def written(tmp_path):
    return luafile.loads((tmp_path / INBOX_NAME).read_text(encoding="utf-8"))


def test_a_received_death_reaches_the_inbox(tmp_path):
    sync = make_sync(tmp_path)
    sync.on_death(death())
    assert [d["source"] for d in written(tmp_path)["deaths"]] == ["Alice"]


def test_deaths_inside_the_cooldown_are_dropped(tmp_path):
    sync = make_sync(tmp_path)
    sync.on_death(death(time=100.0))
    sync.on_death(death(source="Bob", time=100.0 + COOLDOWN_SECONDS - 1))
    sync.on_death(death(source="Carol", time=100.0 + COOLDOWN_SECONDS + 1))
    assert [d["source"] for d in written(tmp_path)["deaths"]] == ["Alice", "Carol"]


def test_the_same_death_is_not_applied_twice(tmp_path):
    sync = make_sync(tmp_path)
    sync.on_death(death())
    sync.on_death(death())
    assert len(written(tmp_path)["deaths"]) == 1


def test_deaths_the_mod_has_applied_are_dropped_from_the_inbox(tmp_path):
    sync = make_sync(tmp_path)
    sync.on_death(death())
    sync.acknowledge_deaths(1_000_500)
    sync.flush_inbox()
    sync.on_death(death(source="Bob", time=1_500.0))
    assert [d["source"] for d in written(tmp_path)["deaths"]] == ["Bob"]


def test_deaths_are_ignored_when_the_option_is_off(tmp_path):
    sync = TF3Sync(Bridge(tmp_path), own_name="Mathys")
    sync.on_connected({**SLOT, "death_link": False}, [])
    sync.on_death(death())
    assert "deaths" not in written(tmp_path)
