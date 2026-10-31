import pytest

from transport_fever_3.client import bridge as bridge_module
from transport_fever_3.client import luafile
from transport_fever_3.client.bridge import Bridge, Outbox

SLOT_DATA = {
    "version": 1,
    "seed": "seed-1",
    "eras": {"B": 1920, "C": 1960},
    "goals": {"population": 2500, "company_level": 0, "passengers": 0, "cargo": 0},
    "checks": {"population": [500, 1000], "company_level": [2], "passengers": [], "cargo": [], "first_line": True, "delivery": [100]},
}
OUTBOX = {
    "version": 1, "seed": "seed-1", "checks": ["population:1", "line:road"],
    "goals": {"population": False}, "applied": 0, "heartbeat": 100,
}


@pytest.fixture
def bridge(tmp_path):
    return Bridge(tmp_path, seed="seed-1")


def outbox_file(tmp_path, seed="seed-1"):
    return tmp_path / f"archipelago_tf3_outbox_{seed}.lua"


def write_outbox(tmp_path, value):
    outbox_file(tmp_path, value["seed"]).write_text(luafile.dumps(value), encoding="utf-8")


def test_inbox_counts_items_and_numbers_effects(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, ["Rail Transport", "Money Grant (small)", "Money Grant (small)"])
    inbox = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))
    assert inbox["version"] == 1 and inbox["seed"] == "seed-1"
    assert inbox["items"]["Rail Transport"] == 1
    assert inbox["items"]["Money Grant (small)"] == 2
    assert inbox["effects"] == [
        {"id": 2, "kind": "money", "amount": 50000},
        {"id": 3, "kind": "money", "amount": 50000},
    ]
    assert inbox["config"]["goals"]["population"] == 2500
    assert inbox["config"]["checks"]["population"] == [500, 1000]
    assert inbox["config"]["eras"] == {"B": 1920, "C": 1960}


def test_traps_are_money_loss_effects_with_their_amount(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, ["Money Loss (small)", "Money Loss (medium)"])
    effects = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["effects"]
    assert effects == [
        {"id": 1, "kind": "money_loss", "amount": 50000},
        {"id": 2, "kind": "money_loss", "amount": 250000},
    ]


def test_resend_same_items_gives_identical_inbox(bridge, tmp_path):
    received = ["Rail Transport", "Money Grant (large)"]
    bridge.write_inbox(SLOT_DATA, received)
    first = (tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8")
    bridge.write_inbox(SLOT_DATA, received)
    assert (tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8") == first


def test_inbox_write_leaves_no_temporary_file(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, [])
    assert [p.name for p in tmp_path.iterdir()] == ["archipelago_tf3_inbox.lua"]


def test_old_slot_data_without_eras_still_writes_an_inbox(bridge, tmp_path):
    old = {key: value for key, value in SLOT_DATA.items() if key != "eras"}
    bridge.write_inbox(old, [])
    config = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["config"]
    assert "eras" not in config


def test_write_inbox_learns_the_seed(tmp_path):
    fresh = Bridge(tmp_path)
    assert fresh.seed is None
    fresh.write_inbox(SLOT_DATA, [])
    assert fresh.seed == "seed-1"


def test_inbox_replace_is_retried_when_the_file_is_busy(bridge, tmp_path, monkeypatch):
    real_replace = bridge_module.os.replace
    calls = []

    def busy_twice(source, target):
        calls.append(1)
        if len(calls) <= 2:
            raise PermissionError("sharing violation")
        real_replace(source, target)

    monkeypatch.setattr(bridge_module.os, "replace", busy_twice)
    bridge.write_inbox(SLOT_DATA, ["Rail Transport"])
    assert len(calls) == 3
    assert (tmp_path / "archipelago_tf3_inbox.lua").exists()


def test_inbox_replace_that_never_succeeds_raises_after_retries(bridge, monkeypatch):
    def always_busy(source, target):
        raise PermissionError("busy")

    monkeypatch.setattr(bridge_module.os, "replace", always_busy)
    with pytest.raises(PermissionError):
        bridge.write_inbox(SLOT_DATA, [])


def test_read_outbox_roundtrip(bridge, tmp_path):
    write_outbox(tmp_path, OUTBOX)
    assert bridge.read_outbox() == Outbox(
        seed="seed-1", checks={"population:1", "line:road"}, goals={"population": False}, applied=0, heartbeat=100,
    )


def test_read_outbox_missing_returns_none(bridge):
    assert bridge.read_outbox() is None


def test_read_outbox_without_a_known_seed_returns_none(tmp_path):
    write_outbox(tmp_path, OUTBOX)
    assert Bridge(tmp_path).read_outbox() is None


def test_read_outbox_truncated_returns_none(bridge, tmp_path):
    text = luafile.dumps(OUTBOX)
    outbox_file(tmp_path).write_text(text[: len(text) // 2], encoding="utf-8")
    assert bridge.read_outbox() is None


def test_read_outbox_empty_file_returns_none(bridge, tmp_path):
    outbox_file(tmp_path).write_text("", encoding="utf-8")
    assert bridge.read_outbox() is None


def test_read_outbox_missing_fields_returns_none(bridge, tmp_path):
    write_outbox(tmp_path, {"version": 1, "seed": "seed-1"})
    assert bridge.read_outbox() is None


def test_empty_checks_and_goals_tables_read_back(bridge, tmp_path):
    write_outbox(tmp_path, {**OUTBOX, "checks": [], "goals": {}})
    outbox = bridge.read_outbox()
    assert outbox.checks == set() and outbox.goals == {}


def test_each_seed_has_its_own_outbox_file(bridge, tmp_path):
    write_outbox(tmp_path, {**OUTBOX, "seed": "other", "checks": ["cargo:1"]})
    assert bridge.read_outbox() is None  # the other seed's progress is never mixed in
    write_outbox(tmp_path, OUTBOX)
    assert bridge.read_outbox().checks == {"population:1", "line:road"}


def test_an_outbox_whose_content_names_another_seed_is_rejected(bridge, tmp_path):
    outbox_file(tmp_path).write_text(luafile.dumps({**OUTBOX, "seed": "other"}), encoding="utf-8")
    assert bridge.read_outbox() is None


def test_seed_is_made_safe_for_a_file_name(tmp_path):
    name = Bridge(tmp_path, seed="a/b\\c:d").outbox_path().name
    assert "/" not in name and "\\" not in name and ":" not in name


def test_new_checks_returns_only_unsent(bridge, tmp_path):
    write_outbox(tmp_path, OUTBOX)
    assert bridge.new_checks({"population:1"}) == {"line:road"}
    assert bridge.new_checks({"population:1", "line:road"}) == set()


def test_outbox_year_is_read_when_present(bridge, tmp_path):
    write_outbox(tmp_path, {**OUTBOX, "year": 2020})
    assert bridge.read_outbox().year == 2020


def test_outbox_without_year_is_still_valid(bridge, tmp_path):
    write_outbox(tmp_path, OUTBOX)
    assert bridge.read_outbox().year is None


def test_inbox_carries_the_log_of_who_sent_what_when_given(bridge, tmp_path):
    log = [{"item": "Rail Transport", "from": "Alice", "where": "Alice's chest"}, {"item": "Money Grant (small)", "own": True, "where": "population:1"}]
    bridge.write_inbox(SLOT_DATA, ["Rail Transport", "Money Grant (small)"], log)
    inbox = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))
    assert inbox["log"] == log


def test_inbox_without_a_log_has_no_log_field(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, ["Rail Transport"])
    assert "log" not in luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))


def test_money_scale_multiplies_grants_and_losses(bridge, tmp_path):
    bridge.write_inbox({**SLOT_DATA, "money_scale": 50}, ["Money Grant (small)", "Money Loss (medium)"])
    effects = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["effects"]
    assert [effect["amount"] for effect in effects] == [25000, 125000]


def test_slot_data_without_a_money_scale_keeps_the_base_amounts(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, ["Money Grant (small)"])
    effects = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["effects"]
    assert effects[0]["amount"] == 50000


def test_the_loan_scale_reaches_the_mod_through_the_config(bridge, tmp_path):
    bridge.write_inbox({**SLOT_DATA, "loan_scale": 10}, [])
    inbox = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))
    assert inbox["config"]["loan_scale"] == 10


def test_slot_data_without_a_loan_scale_leaves_the_loans_alone(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, [])
    inbox = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))
    assert "loan_scale" not in inbox["config"]
