import base64

import pyedid
import pytest
from pydantic import ValidationError
from tomlkit import dumps

from monitorboss import MonitorBossError
from monitorboss.profile import (
    MonitorProfile,
    MonitorIdentity,
    ProfileTomlCategories,
    _RawTomlProfile,
    _RawTomlIdentity,
    _RawTomlCapabilities,
    _RawTomlProfileSettings,
    get_profile,
    new_profile_toml,
    write_profile,
)
from test.testdata import _EDID_128_BASE64, vcp_template


# Base template for identity fields — used by parametrized tests
PROFILE_IDENTITY_TEMPLATE: dict = {
    "pnpid": "MBS",
    "model": "DUMM13",
    "serial": "DUMMYSERIAL",
    "year": 2022,
    "week": 5,
    "edid_128_base64": _EDID_128_BASE64,
}

# Base template for constructing _RawTomlProfile instances — used by parametrized tests
PROFILE_DICT_TEMPLATE: dict = {
    "identity": PROFILE_IDENTITY_TEMPLATE,
    "capabilities": _RawTomlCapabilities(raw=""),
    "max_values": {},
    "value_redirects": {},
    "settings": _RawTomlProfileSettings(),
}


class TestProfileValidation:
    """Tests for Pydantic validation of MonitorProfile after TOML parsing."""

    def test_profile_valid_round_trip(self, test_profile: MonitorProfile):
        """Test that TEST_PROFILE_TOML_CONTENTS parses to a valid MonitorProfile with expected field values."""
        assert test_profile.identity.pnpid == PROFILE_IDENTITY_TEMPLATE["pnpid"]
        assert test_profile.identity.model == PROFILE_IDENTITY_TEMPLATE["model"]
        assert test_profile.identity.serial == PROFILE_IDENTITY_TEMPLATE["serial"]
        assert test_profile.identity.year == PROFILE_IDENTITY_TEMPLATE["year"]
        assert test_profile.identity.week == PROFILE_IDENTITY_TEMPLATE["week"]
        assert test_profile.identity.edid_128_base64 == PROFILE_IDENTITY_TEMPLATE["edid_128_base64"]
        assert test_profile.capabilities == vcp_template.caps_str
        assert test_profile.max_values == {16: 100, 18: 100}
        assert test_profile.value_redirects == {"input_source": {16: 27}}
        assert test_profile.wait_get_time == 0.05
        assert test_profile.wait_set_time == 0.1
        assert test_profile.wait_internal_time == 0.04

    @pytest.mark.parametrize("overrides,expected_match", [
        # Extra field
        ({**PROFILE_IDENTITY_TEMPLATE, "extra": "bad"},          "Extra inputs are not permitted"),
        # edid_128_base64 wrong length (valid base64 but not 128 bytes)
        ({**PROFILE_IDENTITY_TEMPLATE, "edid_128_base64": "AAAA"},  "must decode to exactly 128 bytes"),
        # Invalid base64 string
        ({**PROFILE_IDENTITY_TEMPLATE, "edid_128_base64": "!!!!"}, "not valid base64"),
        # Missing required field: pnpid
        ({k: v for k, v in PROFILE_IDENTITY_TEMPLATE.items() if k != "pnpid"}, "Field required"),
        # Missing required field: model
        ({k: v for k, v in PROFILE_IDENTITY_TEMPLATE.items() if k != "model"}, "Field required"),
        # Missing required field: serial
        ({k: v for k, v in PROFILE_IDENTITY_TEMPLATE.items() if k != "serial"}, "Field required"),
        # Missing required field: year
        ({k: v for k, v in PROFILE_IDENTITY_TEMPLATE.items() if k != "year"}, "Field required"),
        # Missing required field: week
        ({k: v for k, v in PROFILE_IDENTITY_TEMPLATE.items() if k != "week"}, "Field required"),
        # Missing required field: edid_128_base64
        ({k: v for k, v in PROFILE_IDENTITY_TEMPLATE.items() if k != "edid_128_base64"}, "Field required"),
    ])
    def test_identity_invalid_rejected(self, overrides: dict, expected_match: str):
        """Invalid identity fields must be rejected with a descriptive error."""
        with pytest.raises(ValidationError, match=expected_match):
            _RawTomlIdentity(**overrides)

    @pytest.mark.parametrize("kwargs,expected_match", [
        # Extra field
        ({"raw": "", "extra": "bad"}, "Extra inputs are not permitted"),
        # Missing required field
        ({},                          "Field required"),
    ])
    def test_capabilities_invalid_rejected(self, kwargs: dict, expected_match: str):
        """Invalid capabilities fields must be rejected with a descriptive error."""
        with pytest.raises(ValidationError, match=expected_match):
            _RawTomlCapabilities(**kwargs)

    @pytest.mark.parametrize("kwargs,expected_match", [
        ({"wait_get": -0.05},                        "Wait times must be non-negative"),
        ({"wait_set": -0.1},                         "Wait times must be non-negative"),
        ({"wait_internal": -0.04},                   "Wait times must be non-negative"),
        ({"wait_get": 0.05, "extra_key": "bad"},     "Extra inputs are not permitted"),
    ])
    def test_settings_invalid_rejected(self, kwargs: dict, expected_match: str):
        """Invalid settings must be rejected with a descriptive error."""
        with pytest.raises(ValidationError, match=expected_match):
            _RawTomlProfileSettings(**kwargs)

    @pytest.mark.parametrize("kwargs", [
        {"wait_get": None},
        {"wait_set": None},
        {"wait_internal": None},
        {"wait_get": None, "wait_set": None, "wait_internal": None},
    ])
    def test_settings_null_wait_time_accepted(self, kwargs: dict):
        """None is a valid value for any wait time in _RawTomlProfileSettings (fields are optional)."""
        s = _RawTomlProfileSettings(**kwargs)
        for field, val in kwargs.items():
            assert getattr(s, field) is None

    @pytest.mark.parametrize("missing_key", [
        "identity",
        "capabilities",
        "max_values",
        "value_redirects",
        "settings",
    ])
    def test_raw_profile_missing_required_table(self, missing_key: str):
        """Each of the 5 required top-level tables must be present."""
        profile_dict = {k: v for k, v in PROFILE_DICT_TEMPLATE.items() if k != missing_key}
        with pytest.raises(ValidationError, match="Field required"):
            _RawTomlProfile(**profile_dict)

    def test_raw_profile_extra_field_rejected(self):
        """Extra top-level keys must be rejected."""
        profile_dict = {**PROFILE_DICT_TEMPLATE, "extra_key": "bad"}
        with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
            _RawTomlProfile(**profile_dict)

    @pytest.mark.parametrize("max_values,expected_match", [
        ({"abc": 100},  "non-negative integer VCP codes"),
        ({"999": 100},  "does not correspond to a valid VCP command"),
        ({"16": -1},    "must be non-negative"),
    ])
    def test_max_values_invalid_rejected(self, max_values: dict, expected_match: str):
        """Invalid max_values entries must be rejected."""
        profile_dict = {**PROFILE_DICT_TEMPLATE, "max_values": max_values}
        with pytest.raises(ValidationError, match=expected_match):
            _RawTomlProfile(**profile_dict)

    @pytest.mark.parametrize("value_redirects,expected_match", [
        ({"invalid_feature": {"16": 27}},       "does not correspond to a valid command"),
        ({"input_source": {"abc": 27}},         "non-negative integer strings"),
        ({"input_source": {"16": -1}},          "must be non-negative"),
    ])
    def test_value_redirects_invalid_rejected(self, value_redirects: dict, expected_match: str):
        """Invalid value_redirects entries must be rejected."""
        profile_dict = {**PROFILE_DICT_TEMPLATE, "value_redirects": value_redirects}
        with pytest.raises(ValidationError, match=expected_match):
            _RawTomlProfile(**profile_dict)

    def test_empty_optional_tables_valid(self):
        """All three optional-content tables may be empty without error."""
        profile = _RawTomlProfile(**PROFILE_DICT_TEMPLATE)
        assert profile.max_values == {}
        assert profile.value_redirects == {}
        assert profile.settings.wait_get is None
        assert profile.settings.wait_set is None
        assert profile.settings.wait_internal is None


def test_profile_from_raw_transformations():
    """max_values str keys -> int; value_redirects inner str keys -> int; wait_* raw -> wait_*_time runtime."""
    raw = _RawTomlProfile(
        identity=PROFILE_IDENTITY_TEMPLATE,
        capabilities=_RawTomlCapabilities(raw="caps"),
        max_values={"16": 100, "18": 50},
        value_redirects={"input_source": {"16": 27}},
        settings=_RawTomlProfileSettings(wait_get=0.05, wait_set=0.1, wait_internal=0.04),
    )
    profile = MonitorProfile.from_raw(raw)
    assert profile.max_values == {16: 100, 18: 50}
    assert profile.value_redirects == {"input_source": {16: 27}}
    assert profile.wait_get_time == 0.05
    assert profile.wait_set_time == 0.1
    assert profile.wait_internal_time == 0.04


def test_profile_is_frozen(test_profile: MonitorProfile):
    """MonitorProfile and MonitorIdentity must be immutable."""
    with pytest.raises(ValidationError):
        test_profile.capabilities = "new"
    with pytest.raises(ValidationError):
        test_profile.identity.pnpid = "XYZ"


def test_get_profile_missing_file(tmp_path):
    """Non-existent profile path must raise MonitorBossError."""
    with pytest.raises(MonitorBossError):
        get_profile((tmp_path / "nonexistent.toml").as_posix())


def test_get_profile_invalid_toml(tmp_path):
    """Malformed TOML content must raise MonitorBossError."""
    bad_file = tmp_path / "bad.toml"
    bad_file.write_text("[[[ not valid toml")
    with pytest.raises(MonitorBossError):
        get_profile(bad_file.as_posix())


def test_get_profile_invalid_profile(tmp_path):
    """Valid TOML that fails Pydantic validation must raise MonitorBossError."""
    bad_file = tmp_path / "bad_profile.toml"
    bad_file.write_text("[identity]\npnpid = 123\n")
    with pytest.raises(MonitorBossError):
        get_profile(bad_file.as_posix())


# Valid EDID blob from example_profile.toml — used for new_profile_toml tests
_EXAMPLE_EDID = base64.b64decode(
    "AP///////wAQrLyhTElBMAUgAQOANR547pAlrFJPniUPUFSlSwBxT4GAqcDRwAEBAQEBAQEB"
    "AjqAGHE4LUBYLEUADyghAAAeAAAA/wBETjM5SDgzCiAgICAgAAAA/ABERUxMIFUyNDIySEUK"
    "AAAA/QA4TB5TEQAKICAgICAgARY="
)
_EXAMPLE_EDID_INFO = pyedid.parse_edid(_EXAMPLE_EDID)
_EXAMPLE_CAPS = "(prot(monitor)type(LCD)model(TEST))"


class TestNewProfileToml:
    """Tests for new_profile_toml."""

    def test_returns_toml_document(self):
        """new_profile_toml must return a TOMLDocument without raising."""
        doc = new_profile_toml(_EXAMPLE_EDID, _EXAMPLE_CAPS)
        assert doc is not None

    def test_identity_fields_populated_from_edid(self):
        """[identity] fields must match pyedid-parsed values from the EDID blob."""
        doc = new_profile_toml(_EXAMPLE_EDID, _EXAMPLE_CAPS)
        identity = doc[ProfileTomlCategories.identity.value]
        assert identity["pnpid"] == _EXAMPLE_EDID_INFO.manufacturer_pnp_id
        assert identity["model"] == _EXAMPLE_EDID_INFO.name
        assert identity["serial"] == _EXAMPLE_EDID_INFO.serial
        assert identity["year"] == _EXAMPLE_EDID_INFO.year
        assert identity["week"] == _EXAMPLE_EDID_INFO.week

    def test_edid_128_base64_is_first_128_bytes(self):
        """edid_128_base64 must be the base64 encoding of the first 128 bytes of the blob."""
        doc = new_profile_toml(_EXAMPLE_EDID, _EXAMPLE_CAPS)
        expected = base64.b64encode(_EXAMPLE_EDID[:128]).decode("utf-8")
        assert doc[ProfileTomlCategories.identity.value]["edid_128_base64"] == expected

    def test_capabilities_raw_matches_input(self):
        """[capabilities].raw must exactly match the caps_str argument."""
        doc = new_profile_toml(_EXAMPLE_EDID, _EXAMPLE_CAPS)
        assert doc[ProfileTomlCategories.capabilities.value]["raw"] == _EXAMPLE_CAPS

    def test_output_is_valid_parseable_profile(self, tmp_path):
        """The produced TOMLDocument must round-trip through get_profile without error,
        confirming all five required tables are present and their contents are valid."""
        doc = new_profile_toml(_EXAMPLE_EDID, _EXAMPLE_CAPS)
        write_profile(doc, tmp_path.as_posix(), "test_monitor.toml")
        profile = get_profile((tmp_path / "test_monitor.toml").as_posix())
        assert profile.capabilities == _EXAMPLE_CAPS

    def test_invalid_edid_raises_monitor_boss_error(self):
        """A bytes object that pyedid cannot parse must raise MonitorBossError."""
        with pytest.raises(MonitorBossError, match="could not parse EDID blob"):
            new_profile_toml(b"not a valid edid", _EXAMPLE_CAPS)


