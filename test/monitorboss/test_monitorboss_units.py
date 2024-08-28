import pytest
import tomlkit

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.monitorboss import TEST_TOML_CONTENTS
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, MonitorBossError, impl

pytest_plugins = "pytester"


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


# TODO: there is definitely a way to not have to reuse the same conf code every function, but I'll figure it out later
class TestCLIcheckers:

    def test_check_attr_valid(self):
        assert cli._check_attr("src") == impl.Attribute.src

    def test_check_attr_invalid(self):
        with pytest.raises(MonitorBossError):
            cli._check_attr("foo")

    def test_check_mon_str_valid(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        assert cli._check_mon("baz", conf) == 1

    def test_check_mon_str_invalid(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        with pytest.raises(MonitorBossError):
            cli._check_mon("lol", conf)

    def test_check_mon_id(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        assert cli._check_mon("8", conf) == 8

    # TODO: I skipped testing __check_val because there's a chance it will be changing radically as we
    #  implement all the other commands, and command aliases (see notes over impl.Attribute)


class TestCLIStrGens:

    def test_feature_str_com(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._feature_str(com, conf) == f"{com.desc} ({com.value})"

    def test_feature_str_int(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._feature_str(VCPCodes.input_source, conf) == f"{com.desc} ({com.value})"

    def test_monitor_str_noalias(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        assert cli._monitor_str(2, conf) == "monitor #2"

    def test_monitor_str_onealias(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        assert cli._monitor_str(0, conf) == "monitor #0 (foo)"

    def test_monitor_str_multialias(selfself, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        assert cli._monitor_str(1, conf) == "monitor #1 (bar, baz)"

    def test_value_str_com_noparam_noalias(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        com = get_vcp_com(VCPCodes.image_luminance)
        assert cli._value_str(com, 80, conf) == f"80"

    def test_value_str_int_yesparam_noalias(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        com = get_vcp_com(VCPCodes.display_power_mode)
        assert cli._value_str(com.value, 1, conf) == "1 (on)"

    def test_value_str_int_yesparam_onealias(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._value_str(com, 17, conf) == "17 (hdmi1 | hdmi)"

    def test_value_int_com_yesparam_multialias(self, pytester):
        conf = config.get_config(pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS).as_posix())
        com = get_vcp_com(VCPCodes.input_source)
        assert cli._value_str(com.value, 17, conf) == "17 (hdmi1 | hdmi)"

    def test_value_str_com_noparam_onealias(self, pytester):
        # TODO: this will become relevant when more alias features are added
        pass

    def test_value_str_com_noparam_multialias(self, pytester):
        # TODO: this will become relevant when more alias features are added
        pass