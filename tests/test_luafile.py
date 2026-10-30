import pytest

from transport_fever_3.client.luafile import LuaFormatError, dumps, loads

GAME_SAMPLE = 'function data()\nreturn { \n\t\tcounter = 1,\n\t\tmsg = "created by game",\n\t}\nend'


def test_roundtrip_nested():
    value = {
        "version": 1,
        "seed": 'a "quoted"\nseed',
        "flag": True,
        "off": False,
        "ratio": 0.5,
        "items": {"Rail Transport": 1, "Money Grant (small)": 2},
        "effects": [{"id": 2, "kind": "money", "amount": 50000}, {"id": 3, "kind": "loan", "amount": 0}],
        "checks": ["population:1", "line:rail"],
        "empty": [],
    }
    assert loads(dumps(value)) == value


def test_dumps_uses_game_function_wrapper():
    text = dumps({"a": 1})
    assert text.startswith("function data()\nreturn {")
    assert text.rstrip().endswith("end")


def test_loads_game_written_sample():
    assert loads(GAME_SAMPLE) == {"counter": 1, "msg": "created by game"}


def test_loads_truncated_raises():
    with pytest.raises(LuaFormatError):
        loads(GAME_SAMPLE[: len(GAME_SAMPLE) // 2])


def test_loads_empty_raises():
    with pytest.raises(LuaFormatError):
        loads("")


def test_loads_never_executes_code():
    with pytest.raises(LuaFormatError):
        loads('function data()\nreturn { a = os.execute("calc") }\nend')
