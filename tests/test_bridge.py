import pytest

from transport_fever_3.client import luafile
from transport_fever_3.client.bridge import Bridge, Outbox

SLOT_DATA = {
    "version": 1,
    "seed": "seed-1",
    "goals": {"population": 2500, "company_level": 0, "passengers": 0, "cargo": 0},
    "checks": {"population": [500, 1000], "company_level": [2], "passengers": [], "cargo": [], "first_line": True, "delivery": [100]},
}
OUTBOX = {
    "version": 1, "seed": "seed-1", "checks": ["population:1", "line:road"],
    "goals": {"population": False}, "applied": 0, "heartbeat": 100,
}


@pytest.fixture
def bridge(tmp_path):
    return Bridge(tmp_path)


def write_outbox(tmp_path, value):
    (tmp_path / "archipelago_tf3_outbox.lua").write_text(luafile.dumps(value), encoding="utf-8")


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


def test_trap_effects_have_kinds(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, ["Money Loss", "Forced Loan"])
    effects = luafile.loads((tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8"))["effects"]
    assert [(e["id"], e["kind"]) for e in effects] == [(1, "money_loss"), (2, "loan")]
    assert effects[0]["amount"] == 100000


def test_resend_same_items_gives_identical_inbox(bridge, tmp_path):
    received = ["Rail Transport", "Money Grant (large)"]
    bridge.write_inbox(SLOT_DATA, received)
    first = (tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8")
    bridge.write_inbox(SLOT_DATA, received)
    assert (tmp_path / "archipelago_tf3_inbox.lua").read_text(encoding="utf-8") == first


def test_inbox_write_leaves_no_temporary_file(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, [])
    assert [p.name for p in tmp_path.iterdir()] == ["archipelago_tf3_inbox.lua"]


def test_read_outbox_roundtrip(bridge, tmp_path):
    write_outbox(tmp_path, OUTBOX)
    assert bridge.read_outbox() == Outbox(
        seed="seed-1", checks={"population:1", "line:road"}, goals={"population": False}, applied=0, heartbeat=100,
    )


def test_read_outbox_missing_returns_none(bridge):
    assert bridge.read_outbox() is None


def test_read_outbox_truncated_returns_none(bridge, tmp_path):
    text = luafile.dumps(OUTBOX)
    (tmp_path / "archipelago_tf3_outbox.lua").write_text(text[: len(text) // 2], encoding="utf-8")
    assert bridge.read_outbox() is None


def test_read_outbox_empty_file_returns_none(bridge, tmp_path):
    (tmp_path / "archipelago_tf3_outbox.lua").write_text("", encoding="utf-8")
    assert bridge.read_outbox() is None


def test_read_outbox_missing_fields_returns_none(bridge, tmp_path):
    write_outbox(tmp_path, {"version": 1, "seed": "seed-1"})
    assert bridge.read_outbox() is None


def test_empty_checks_and_goals_tables_read_back(bridge, tmp_path):
    write_outbox(tmp_path, {**OUTBOX, "checks": [], "goals": {}})
    outbox = bridge.read_outbox()
    assert outbox.checks == set() and outbox.goals == {}


def test_new_checks_returns_only_unsent(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, [])
    write_outbox(tmp_path, OUTBOX)
    assert bridge.new_checks({"population:1"}) == {"line:road"}
    assert bridge.new_checks({"population:1", "line:road"}) == set()


def test_seed_mismatch_is_detected_and_sends_nothing(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, [])
    write_outbox(tmp_path, {**OUTBOX, "seed": "old-seed"})
    assert bridge.seed_matches() is False
    assert bridge.new_checks(set()) == set()


def test_seed_matches_when_equal_or_no_outbox(bridge, tmp_path):
    bridge.write_inbox(SLOT_DATA, [])
    assert bridge.seed_matches() is True
    write_outbox(tmp_path, OUTBOX)
    assert bridge.seed_matches() is True
