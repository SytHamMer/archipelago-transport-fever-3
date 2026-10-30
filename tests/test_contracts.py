from transport_fever_3.client import luafile
from transport_fever_3.client.bridge import INBOX_NAME, Bridge
from transport_fever_3.client.tf3_client import TF3Sync, contracts_from_scout, contracts_report

SLOT = {
    "version": 1, "seed": "seed-1", "goals": {"population": 0, "company_level": 0, "passengers": 0, "cargo": 0},
    "checks": {"population": [500], "company_level": [], "passengers": [], "cargo": [], "first_line": False, "delivery": []},
}
LOCATIONS = {10: "population:1", 11: "company_level:2"}
ITEMS = {100: "Rail Transport", 101: "Cargo Class: Bulk"}
PLAYERS = {1: "Me", 2: "Alice"}


def scout(infos):
    return contracts_from_scout(infos, own_slot=1, location_name=LOCATIONS.get, item_name=ITEMS.get,
                                player_name=PLAYERS.get)


def test_an_own_reward_is_marked_own():
    assert scout([(10, 100, 1)]) == {"population:1": {"item": "Rail Transport", "to": "Me", "own": True}}


def test_a_reward_for_another_player_names_the_receiver():
    assert scout([(11, 101, 2)]) == {"company_level:2": {"item": "Cargo Class: Bulk", "to": "Alice", "own": False}}


def test_a_location_or_item_that_cannot_be_named_is_skipped():
    assert scout([(99, 100, 1), (10, 999, 1)]) == {}


def test_the_inbox_carries_contracts_only_when_given(tmp_path):
    bridge = Bridge(tmp_path)
    bridge.write_inbox(SLOT, [])
    assert "contracts" not in luafile.loads((tmp_path / INBOX_NAME).read_text(encoding="utf-8"))
    contracts = {"population:1": {"item": "Rail Transport", "to": "Me", "own": True}}
    bridge.write_inbox(SLOT, [], contracts=contracts)
    assert luafile.loads((tmp_path / INBOX_NAME).read_text(encoding="utf-8"))["contracts"] == contracts


def test_setting_contracts_rewrites_the_inbox(tmp_path):
    sync = TF3Sync(Bridge(tmp_path))
    sync.on_connected(SLOT, [])
    sync.set_contracts({"population:1": {"item": "Rail Transport", "to": "Me", "own": True}})
    written = luafile.loads((tmp_path / INBOX_NAME).read_text(encoding="utf-8"))
    assert written["contracts"]["population:1"]["to"] == "Me"


def test_the_report_lists_open_contracts_and_the_progress():
    contracts = {"population:1": {"item": "Rail Transport", "to": "Me", "own": True},
                 "company_level:2": {"item": "Cargo Class: Bulk", "to": "Alice", "own": False}}
    lines = contracts_report(contracts, done={"population:1"})
    assert lines[0] == "Contracts: 1/2 done"
    assert lines[1:] == ["company_level:2 -> Cargo Class: Bulk for Alice"]


def test_the_report_without_contracts_says_so():
    assert contracts_report({}, done=set()) == ["No contracts known yet (waiting for the server)."]
