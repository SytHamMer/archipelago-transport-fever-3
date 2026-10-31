from ..Options import OPTION_PRESETS
from .bases import TF3TestBase


class TestShortGamePreset(TF3TestBase):
    options = OPTION_PRESETS["Short game"]


class TestLongGamePreset(TF3TestBase):
    options = OPTION_PRESETS["Long game"]


class TestDefaultPreset(TF3TestBase):
    options = OPTION_PRESETS["Default"]


class TestPresetsNameRealOptions(TF3TestBase):
    def test_every_preset_only_uses_existing_options(self) -> None:
        from ..Options import TF3Options

        for name, preset in OPTION_PRESETS.items():
            self.assertLessEqual(set(preset), set(TF3Options.type_hints), name)
