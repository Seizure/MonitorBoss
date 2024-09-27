import sys

import pytest

from frozendict import frozendict

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import cli, MonitorBossError, indentation, info


class TestCheckAttribute:

    def test_check_attr_alias_valid(self, test_cfg):
        assert cli._check_feature("src", test_cfg) == get_vcp_com(VCPCodes.input_source.value)

    def test_check_attr_name_valid(self, test_cfg):
        assert cli._check_feature("input_source", test_cfg) == get_vcp_com(VCPCodes.input_source.value)

    def test_check_attr_int_valid(self, test_cfg):
        assert cli._check_feature(f"{VCPCodes.input_source.value}", test_cfg) == get_vcp_com(VCPCodes.input_source.value)

    def test_check_attr_namealias_invalid(self, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_feature("foo", test_cfg)

    def test_check_attr_code_invalid(self, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_feature("1568", test_cfg)


class TestCheckMonitor:

    def test_check_mon_str_valid(self, test_cfg):
        assert cli._check_mon("baz", test_cfg) == 1

    def test_check_mon_str_invalid(self, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_mon("lol", test_cfg)

    # No need to test for invalid IDs here, as _check_mon has no concept of such.
    # That is handled by impl._get_monitor
    def test_check_mon_id(self, test_cfg):
        assert cli._check_mon("8", test_cfg) == 8


class TestCheckValue:

    def test_check_val_digits(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "5", test_cfg) == 5

    def test_check_val_param(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "dp1", test_cfg) == 15

    def test_check_val_alias(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "usb-c", test_cfg) == 27

    def test_check_val_invalid_yesparam_yesalias(self, capsys, test_cfg):
        try:
            cli._check_val(get_vcp_com(VCPCodes.input_source), "foo", test_cfg)
        except MonitorBossError as err:
            print(err, file=sys.stderr)
        output = capsys.readouterr()
        assert output.out == ""
        assert "PARAM NAMES" in output.err
        assert "CONFIG ALIASES" in output.err

    def test_check_val_invalid_yesparam_noalias(self, capsys, test_cfg):
        try:
            cli._check_val(get_vcp_com(VCPCodes.display_power_mode), "foo", test_cfg)
        except MonitorBossError as err:
            print(err, file=sys.stderr)
        output = capsys.readouterr()
        assert output.out == ""
        assert "PARAM NAMES" in output.err
        assert "CONFIG ALIASES" not in output.err

    def test_check_val_invalid_noparam_yesalias(self, capsys, test_cfg):
        # TODO: this will become relevant when we allow for aliases on all feature values
        pass

    def test_check_val_invalid_noparam_noalias(self, capsys, test_cfg):
        try:
            cli._check_val(get_vcp_com(VCPCodes.image_luminance), "foo", test_cfg)
        except MonitorBossError as err:
            print(err, file=sys.stderr)
        output = capsys.readouterr()
        assert output.out == ""
        assert "PARAM NAMES" not in output.err
        assert "CONFIG ALIASES" not in output.err


class TestSummaryUtils:

    def test_extract_caps_summary_data(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        feature3 = info.FeatureData("", VCPCodes.input_source.value, ())
        feature4 = info.FeatureData("", VCPCodes.image_color_preset.value, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(34, "", ())
        value3 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
        value4 = info.ValueData(ColorPresetNames.ct5000k.value, "", ())
        attributes = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
        cmds = frozendict({"cmds_0": (feature1, feature2, feature3), "cmds_1": (feature1, feature2, feature4)})
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature3: (value3,)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature4: (value4,)})})
        errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
        data = info.CapabilityData(attributes, cmds, vcps, errata)

        expected = ({'model': 'CAF3', 'type': 'LCD'}, {'vcp_0': {feature3: (value3,)}, 'vcp_1': {feature4: (value4,)}})

        assert cli._extract_caps_summary_data(data) == expected

    def test_caps_summary_json(self):
        mon = info.MonitorData(42, ())
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        feature3 = info.FeatureData("", VCPCodes.input_source.value, ())
        feature4 = info.FeatureData("", VCPCodes.image_color_preset.value, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(34, "", ())
        value3 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
        value4 = info.ValueData(ColorPresetNames.ct5000k.value, "", ())
        attributes = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
        cmds = frozendict({"cmds_0": (feature1, feature2, feature3), "cmds_1": (feature1, feature2, feature4)})
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature3: (value3,)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature4: (value4,)})})
        errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
        data = info.CapabilityData(attributes, cmds, vcps, errata)

        expected = '{"caps": {"type": "summary", "monitor": {"id": 42}, "data": {"model": "CAF3", "type": "LCD", "vcps": {"vcp_0": [{"feature": {"code": 96}, "params": [{"value": 18}]}], "vcp_1": [{"feature": {"code": 20}, "params": [{"value": 4}]}]}}}}'

        assert cli._caps_summary_json(mon, data) == expected

    def test_caps_summary_human(self):
        mon = info.MonitorData(42, ())
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        feature3 = info.FeatureData("", VCPCodes.input_source.value, ())
        feature4 = info.FeatureData("", VCPCodes.image_color_preset.value, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(34, "", ())
        value3 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
        value4 = info.ValueData(ColorPresetNames.ct5000k.value, "", ())
        attributes = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
        cmds = frozendict({"cmds_0": (feature1, feature2, feature3), "cmds_1": (feature1, feature2, feature4)})
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature3: (value3,)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature4: (value4,)})})
        errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
        data = info.CapabilityData(attributes, cmds, vcps, errata)

        expected = f'monitor #42model: CAF3, type: LCD\nvcp_0:\n{indentation}* 96: 18\nvcp_1:\n{indentation}* 20: 4\n'

        assert cli._caps_summary_human(mon, data) == expected

    # TODO: test presence/lack of _INDENT in json depending on logging level