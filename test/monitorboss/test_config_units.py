import tomlkit
import pytest
from pydantic import ValidationError

from monitorboss import config, MonitorBossError
from monitorboss.config import Config, _RawTomlConfig, _RawTomlSettings
from test.testdata import TEST_TOML_CONTENTS


# Base template for constructing test configs — used by parametrized tests
CONFIG_DICT_TEMPLATE: dict = {
    "monitor_names": {},
    "feature_aliases": {},
    "value_aliases": {},
    "settings": _RawTomlSettings(wait_get=0.05, wait_set=0.1, wait_internal=0.04),
}


def test_config_auto_create(pytester):
    confpath = pytester.path.joinpath("test_config.toml")
    config.get_config(confpath.as_posix())
    assert confpath.exists()
    with open(confpath, "r", encoding="utf8") as file:
        contents = file.read()
    assert contents == tomlkit.dumps(config.default_toml())


def test_config_reset(pytester):
    conf = pytester.makefile(".toml", test_toml="trash")

    # sanity checking
    with open(conf, "r", encoding="utf8") as file:
        contents = file.read()
    assert contents == "trash"

    config.reset_config(conf.as_posix())
    with open(conf, "r", encoding="utf8") as file:
        contents = file.read()
    assert contents == tomlkit.dumps(config.default_toml())


class TestConfigValidation:
    """Tests for Pydantic validation of Config after TOML parsing."""

    def test_config_valid_round_trip(self, test_cfg: Config):
        """Test that TEST_TOML_CONTENTS parses to a valid Config with expected field values."""
        # Verify all six fields are populated correctly
        assert test_cfg.monitor_names == {"foo": 0, "bar": 1, "baz": 1}
        assert test_cfg.feature_aliases == {
            "lum": 16, "luminance": 16, "brightness": 16,
            "cnt": 18, "contrast": 18,
            "clr": 20, "color": 20, "clrpreset": 20,
            "src": 96, "source": 96, "input": 96,
            "pwr": 214, "power": 214, "powermode": 214,
        }
        # After inversion: TOML {value_id: [aliases]} -> Config {alias: value_id}
        assert test_cfg.value_aliases == {
            "input_source": {"usbc": 27, "usb-c": 27, "hdmi": 17},
            "image_luminance": {"night": 25, "day": 75, "bright": 75},
        }
        assert test_cfg.wait_get_time == 0
        assert test_cfg.wait_set_time == 0
        assert test_cfg.wait_internal_time == 0

    @pytest.mark.parametrize("overrides,expected_match", [
        # Non-numeric keys
        ({"monitor_names": {"abc": "main"}},                                    "Monitor IDs must be non-negative integers"),
        ({"feature_aliases": {"abc": "brightness"}},                            "Feature codes must be non-negative integers"),
        ({"value_aliases": {"image_luminance": {"abc": "night"}}},              "Value IDs must be non-negative integers"),
        # Numeric aliases
        ({"monitor_names": {"0": "123"}},                                       "Monitor aliases can not be numeric"),
        ({"feature_aliases": {"16": ["brightness", "123"]}},                    "Feature aliases can not be numeric"),
        ({"value_aliases": {"image_luminance": {"25": ["night", "123"]}}},      "Value aliases can not be numeric"),
        # Duplicate aliases
        ({"monitor_names": {"0": "foo", "1": "foo"}},                           "Monitor alias is used multiple times"),
        ({"feature_aliases": {"16": "brightness", "18": "brightness"}},         "Feature alias is used multiple times"),
        ({"value_aliases": {"image_luminance": {"25": "night", "75": "night"}}}, "Value alias is used multiple times"),
        # Invalid feature codes / names
        ({"feature_aliases": {"999": ["brightness"]}},                          "does not correspond to a valid command"),
        ({"value_aliases": {"invalid_feature": {"25": "night"}}},               "does not correspond to a valid command"),
    ])
    def test_raw_config_invalid_rejected(self, overrides: dict, expected_match: str):
        """Invalid _RawTomlConfig data must be rejected by field validators with a descriptive error."""
        config_dict = {**CONFIG_DICT_TEMPLATE, **overrides}
        with pytest.raises(ValidationError, match=expected_match):
            _RawTomlConfig(**config_dict)

    def test_value_aliases_same_alias_across_subtables_valid(self):
        """The same alias string in different value_alias sub-tables must be accepted (conflict scope is per sub-table)."""
        # Should not raise — "day" appears in two different sub-tables, which is allowed
        config_dict = {
            **CONFIG_DICT_TEMPLATE,
            "value_aliases": {
                "image_luminance": {"25": "day"},
                "image_contrast": {"50": "day"},  # "day" in a different sub-table — not a conflict
            }
        }
        raw = _RawTomlConfig(**config_dict)
        # raw.value_aliases is pre-inversion: keys are value ID strings, values are alias strings
        assert raw.value_aliases["image_luminance"]["25"] == "day"
        assert raw.value_aliases["image_contrast"]["50"] == "day"

    @pytest.mark.parametrize("settings", [
        {"wait_get": -0.05, "wait_set": 0.1,  "wait_internal": 0.04},
        {"wait_get": 0.05,  "wait_set": -0.1, "wait_internal": 0.04},
        {"wait_get": 0.05,  "wait_set": 0.1,  "wait_internal": -0.04},
    ])
    def test_settings_negative_wait_time_rejected(self, settings: dict):
        """Any negative wait time must be rejected by _RawTomlSettings."""
        with pytest.raises(ValidationError, match="Wait times must be non-negative"):
            _RawTomlSettings(**settings)


def test_inversion():
    """Aliases should be inverted correctly: {id: [aliases]} -> {alias: id}."""
    config_dict = {
        **CONFIG_DICT_TEMPLATE,
        "monitor_names": {"0": "main", "1": ["second", "side"]},
        "feature_aliases": {"16": "brightness", "18": ["con", "cntr"]},
        "value_aliases": {
                "image_luminance": {"25": "night", "75": ["day", "bright"]}
            }
    }
    raw = _RawTomlConfig(**config_dict)
    cfg = Config.from_raw(raw)
    assert cfg.monitor_names == {"main": 0, "second": 1, "side": 1}
    assert cfg.feature_aliases == {"brightness": 16, "con": 18, "cntr": 18}
    assert cfg.value_aliases == {"image_luminance": {"night": 25, "day": 75, "bright": 75}}


def test_config_is_frozen(test_cfg: Config):
    """Config objects should be immutable at the top level."""
    with pytest.raises(ValidationError):
        test_cfg.wait_get_time = 0.5
