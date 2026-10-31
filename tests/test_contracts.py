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


CHECKS = {"population": [500, 1000, 2500], "company_level": [2, 3], "passengers": [100], "cargo": [50],
          "first_line": True, "delivery": [100, 500], "missions": [1, 2]}


def reward(item="Rail Transport", to="Me", own=True):
    return {"item": item, "to": to, "own": own}


def test_the_report_lists_the_next_contracts_in_readable_text_with_their_reward():
    contracts = {"population:1": reward(), "population:2": reward("Cargo Class: Bulk", "Alice", False),
                 "company_level:2": reward("Money Grant (small)")}
    lines = contracts_report(contracts, done={"population:1"}, checks=CHECKS)
    assert lines[0] == "Contracts: 1/3 done"
    assert lines[1:] == ["Population reached 1,000 -> Cargo Class: Bulk for Alice",
                         "Company level 2 reached -> Money Grant (small)"]


def test_only_the_next_step_of_each_ladder_and_delivery_is_listed_but_every_first_line():
    contracts = {"population:1": reward(), "population:2": reward(), "line:rail": reward(), "line:road": reward(),
                 "delivered:wool:1": reward(), "delivered:wool:2": reward()}
    lines = contracts_report(contracts, done=set(), checks=CHECKS)
    assert len(lines) == 1 + 4  # header, population:1, both lines, delivered:wool:1
    assert "Population reached 500 -> Rail Transport" in lines
    assert "First rail line built -> Rail Transport" in lines
    assert "Delivered 100 wool -> Rail Transport" in lines
    assert lines[0] == "Contracts: 0/6 done (2 later contracts not shown, /contracts all lists everything)"


def test_all_lists_every_open_contract():
    contracts = {"population:1": reward(), "population:2": reward()}
    lines = contracts_report(contracts, done=set(), checks=CHECKS, show_all=True)
    assert lines == ["Contracts: 0/2 done", "Population reached 500 -> Rail Transport",
                     "Population reached 1,000 -> Rail Transport"]


def test_every_check_family_has_a_readable_text():
    contracts = {c: reward() for c in ("passengers:1", "cargo:1", "mission:2", "delivered:iron_ore:2")}
    lines = contracts_report(contracts, done=set(), checks=CHECKS)[1:]
    assert sorted(lines) == sorted([
        "Passengers transported: 100 -> Rail Transport", "Cargo transported: 50 -> Rail Transport",
        "Missions completed: 2 -> Rail Transport", "Delivered 500 iron ore -> Rail Transport"])


def test_an_unknown_check_is_listed_by_its_id_and_without_the_config_too():
    lines = contracts_report({"mystery:1": reward()}, done=set(), checks=None)
    assert lines[1:] == ["mystery:1 -> Rail Transport"]


def test_the_report_without_contracts_says_so():
    assert contracts_report({}, done=set()) == ["No contracts known yet (waiting for the server)."]
