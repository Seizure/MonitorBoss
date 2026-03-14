import sys

import pytest

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import cli, MonitorBossError


class TestCheckAttribute:

    @pytest.mark.parametrize("input_val", [
        "src", # test by attr alias
        "input_source", # test by attr name
        f"{VCPCodes.input_source.value}",
    ])
    def test_check_attr_valid(self, input_val, test_cfg):
        assert cli._check_feature(input_val, test_cfg) == get_vcp_com(VCPCodes.input_source.value)

    @pytest.mark.parametrize("input_val", [
        "foo", # test invalid attr alias
        "1568", # test invalid attr int
    ])
    def test_check_attr_invalid(self, input_val, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_feature(input_val, test_cfg)


class TestCheckMonitor:

    @pytest.mark.parametrize("input_val, expected", [
        ("baz", 1),
        ("8", 8),
    ])
    def test_check_mon_valid(self, input_val, expected, test_cfg):
        assert cli._check_mon(input_val, test_cfg) == expected

    # _check_mon has no concept of invalid int IDs, that is handled by impl._get_monitor.
    # so no need to check for that here
    def test_check_mon_str_invalid(self, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_mon("lol", test_cfg)


class TestCheckValue:

    @pytest.mark.parametrize("value_str, expected", [
        ("5", 5),
        ("dp1", 15),
        ("usb-c", 27),
    ])
    def test_check_val_valid(self, value_str, expected, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), value_str, test_cfg) == expected

    @pytest.mark.parametrize("feature_code, value_str, has_param, has_alias", [
        (VCPCodes.input_source, "foo", True, True),
        (VCPCodes.display_power_mode, "foo", True, False),
        (VCPCodes.image_luminance, "foo", False, True),
        (VCPCodes.image_contrast, "foo", False, False),
    ])
    def test_check_val_invalid(self, capsys, test_cfg, feature_code, value_str, has_param, has_alias):
        try:
            cli._check_val(get_vcp_com(feature_code), value_str, test_cfg)
        except MonitorBossError as err:
            print(err, file=sys.stderr)
        output = capsys.readouterr()
        assert output.out == ""
        if has_param:
            assert "PARAM NAMES" in output.err
        else:
            assert "PARAM NAMES" not in output.err
        if has_alias:
            assert "CONFIG ALIASES" in output.err
        else:
            assert "CONFIG ALIASES" not in output.err

    # TODO: test presence/lack of _INDENT in json depending on logging level
