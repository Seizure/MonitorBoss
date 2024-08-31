import pytest
import tomlkit

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, MonitorBossError, impl


class TestConfig:

    # TODO: test reading/parsing of config

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


# TODO: there is definitely a way to not have to reuse the same conf code every function, but I'll figure it out later
class TestCLIcheckers:

    def test_check_attr_valid(self):
        assert cli._check_attr("src") == impl.Attribute.src

    def test_check_attr_invalid(self):
        with pytest.raises(MonitorBossError):
            cli._check_attr("foo")

    def test_check_mon_str_valid(self, test_cfg):
        assert cli._check_mon("baz", test_cfg) == 1

    def test_check_mon_str_invalid(self, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_mon("lol", test_cfg)

    def test_check_mon_id(self, test_cfg):
        assert cli._check_mon("8", test_cfg) == 8

    # TODO: I skipped testing __check_val because there's a chance it will be changing radically as we
    #  implement all the other commands, and command aliases (see notes over impl.Attribute)


class TestCLIStrGens:

    def test_feature_str_com(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._feature_str(com, test_cfg) == f"{com.desc} ({com.value})"

    def test_feature_str_int(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._feature_str(VCPCodes.input_source, test_cfg) == f"{com.desc} ({com.value})"

    def test_monitor_str_noalias(self, test_cfg):
        assert cli._monitor_str(2, test_cfg) == "monitor #2"

    def test_monitor_str_onealias(self, test_cfg):
        assert cli._monitor_str(0, test_cfg) == "monitor #0 (foo)"

    def test_monitor_str_multialias(self, test_cfg):
        assert cli._monitor_str(1, test_cfg) == "monitor #1 (bar, baz)"

    def test_value_str_com_noparam_noalias(self, test_cfg):
        com = get_vcp_com(VCPCodes.image_luminance)
        assert cli._value_str(com, 80, test_cfg) == f"80"

    def test_value_str_int_yesparam_noalias(self, test_cfg):
        com = get_vcp_com(VCPCodes.display_power_mode)
        assert cli._value_str(com.value, 1, test_cfg) == "1 (on)"

    def test_value_str_int_yesparam_onealias(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._value_str(com, 17, test_cfg) == "17 (hdmi1 | hdmi)"

    def test_value_int_com_yesparam_multialias(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._value_str(com.value, 17, test_cfg) == "17 (hdmi1 | hdmi)"

    def test_value_str_com_noparam_onealias(self, test_cfg):
        # TODO: this will become relevant when more alias features are added
        pass

    def test_value_str_com_noparam_multialias(self, test_cfg):
        # TODO: this will become relevant when more alias features are added
        pass
