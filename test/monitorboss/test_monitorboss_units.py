import pytest
import tomlkit

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, MonitorBossError, impl


class TestConfig:

    # TODO: test reading, parsing, and validating of config

    def test_auto_create_config(self, pytester):
        confpath = pytester.path.joinpath("test_config.toml")
        config.get_config(confpath.as_posix())
        assert confpath.exists()
        with open(confpath, "r", encoding="utf8") as file:
            contents = file.read()
        assert contents == tomlkit.dumps(config.default_toml())

    def test_config_reset(self, pytester):
        conf = pytester.makefile(".toml", test_toml="trash")

        # sanity checking
        with open(conf, "r", encoding="utf8") as file:
            contents = file.read()
        assert contents == "trash"

        config.reset_config(conf.as_posix())
        with open(conf, "r", encoding="utf8") as file:
            contents = file.read()
        assert contents == tomlkit.dumps(config.default_toml())

    # TODO: should probably eventually test more of the config functions,
    #   but we're currently not even using them and they might change, so not bothering yet


class TestImpl:

    def test_impl_get_monitor_valid(self):
        assert impl._get_monitor(1)

    def test_impl_get_monitor_invalid(self):
        # TODO: is it weird that we allow negative indices, per pythonic behavior?
        # with pytest.raises(MonitorBossError):
        #     impl._get_monitor(-1)
        with pytest.raises(MonitorBossError):
            impl._get_monitor(3)


class TestCLIcheckers:

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

    def test_check_mon_str_valid(self, test_cfg):
        assert cli._check_mon("baz", test_cfg) == 1

    def test_check_mon_str_invalid(self, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_mon("lol", test_cfg)

    # No need to test for invalid IDs here, as _check_mon has no concept of such.
    # That is handled by impl._get_monitor
    def test_check_mon_id(self, test_cfg):
        assert cli._check_mon("8", test_cfg) == 8

    # TODO: I skipped testing _check_val because because it needs to radically change for scaling to more commands


class TestCLIStrGens:

    def test_feature_str_com(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._feature_str(com, test_cfg) == f"{com.name} ({com.value})"

    def test_feature_str_int(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._feature_str(VCPCodes.input_source, test_cfg) == f"{com.name} ({com.value})"

    def test_monitor_str_noalias(self, test_cfg):
        assert cli._monitor_str(2, test_cfg) == "monitor #2"

    def test_monitor_str_onealias(self, test_cfg):
        assert cli._monitor_str(0, test_cfg) == "monitor #0 (foo)"

    def test_monitor_str_multialias(self, test_cfg):
        assert cli._monitor_str(1, test_cfg) == "monitor #1 (bar, baz)"

    def test_value_noparam_noalias(self, test_cfg):
        com = get_vcp_com(VCPCodes.image_luminance)
        assert cli._value_str(com, 80, test_cfg) == f"80"

    def test_value_yesparam_noalias(self, test_cfg):
        com = get_vcp_com(VCPCodes.display_power_mode)
        assert cli._value_str(com, 1, test_cfg) == "1 (on)"

    def test_value_str_int_yesparam_onealias(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._value_str(com, 17, test_cfg) == "17 (hdmi1 | hdmi)"

    def test_value_str_com_noparam_onealias(self, test_cfg):
        # TODO: this will become relevant when we allow for aliases on all coms
        pass

    def test_value_str_com_noparam_multialias(self, test_cfg):
        # TODO: this will become relevant when we allow for aliases on all coms
        pass
