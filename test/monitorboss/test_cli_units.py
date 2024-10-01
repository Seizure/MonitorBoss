import sys

import pytest

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import cli, MonitorBossError


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
        try:
            cli._check_val(get_vcp_com(VCPCodes.image_luminance), "foo", test_cfg)
        except MonitorBossError as err:
            print(err, file=sys.stderr)
        output = capsys.readouterr()
        assert output.out == ""
        assert "PARAM NAMES" not in output.err
        assert "CONFIG ALIASES" in output.err

    def test_check_val_invalid_noparam_noalias(self, capsys, test_cfg):
        try:
            cli._check_val(get_vcp_com(VCPCodes.image_contrast), "foo", test_cfg)
        except MonitorBossError as err:
            print(err, file=sys.stderr)
        output = capsys.readouterr()
        assert output.out == ""
        assert "PARAM NAMES" not in output.err
        assert "CONFIG ALIASES" not in output.err

    # TODO: test presence/lack of _INDENT in json depending on logging level
