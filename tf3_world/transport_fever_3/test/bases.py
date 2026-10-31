import dataclasses

from test.bases import WorldTestBase

from .. import data


class TF3TestBase(WorldTestBase):
    game = data.GAME_NAME


def make_options(options_class, **overrides):
    """Build an options dataclass with defaults, overriding the given raw values."""
    hints = options_class.type_hints
    values = {}
    for field in dataclasses.fields(options_class):
        option = hints[field.name]
        values[field.name] = option.from_any(overrides.get(field.name, option.default))
    unknown = set(overrides) - set(values)
    assert not unknown, f"unknown options: {unknown}"
    return options_class(**values)
