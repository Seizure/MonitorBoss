import pytest
import tomlkit

from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, MonitorBossError, impl, info


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
        assert impl.get_monitor(1)

    def test_impl_get_monitor_invalid(self):
        # TODO: is it weird that we allow negative indices, per pythonic behavior?
        # with pytest.raises(MonitorBossError):
        #     impl._get_monitor(-1)
        with pytest.raises(MonitorBossError):
            impl.get_monitor(3)


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

    def test_check_val_digits(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "5", test_cfg) == 5

    def test_check_val_text_param(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "dp1", test_cfg) == 15

    def test_check_val_text_alias(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "usb-c", test_cfg) == 27

    def test_check_val_text_invalid_yesparam_yesalias(self, capsys, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_val(get_vcp_com(VCPCodes.input_source), "foo", test_cfg)
            output = capsys.readouterr()
            assert output.out == ""
            assert "PARAM NAMES" in output.err
            assert "CONFIG ALIASES" in output.err

    def test_check_val_text_invalid_yesparam_noalias(self, capsys, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_val(get_vcp_com(VCPCodes.image_luminance), "foo", test_cfg)
            output = capsys.readouterr()
            assert output.out == ""
            assert "PARAM NAMES" in output.err
            assert "CONFIG ALIASES" not in output.err

    def test_check_val_text_invalid_noparam_yesalias(self, capsys, test_cfg):
        # TODO: this will become relevant when we allow for aliases on all feature values
        pass

    def test_check_val_text_invalid_noparam_noalias(self, capsys, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_val(get_vcp_com(VCPCodes.image_luminance), "foo", test_cfg)
            output = capsys.readouterr()
            assert output.out == ""
            assert "PARAM NAMES" not in output.err
            assert "CONFIG ALIASES" not in output.err


class TestInfoData:

    def FeatureData_serialize(self):
        pass  # TODO: stub

    def test_feature_data(self, test_cfg):
        com = get_vcp_com(VCPCodes.input_source)
        data = info.FeatureData(com, ['src', 'source', 'input'])
        assert info.feature_data(com, test_cfg) == data

    def MonitorData_serialize(self):
        pass  # TODO: stub

    def test_monitor_data(self, test_cfg):
        data = info.MonitorData(1, ['bar', 'baz'])
        assert info.monitor_data(1, test_cfg) == data

    def ValueData_serialize(self):
        pass  # TODO: stub

    def test_value_data(self, test_cfg):
        data = info.ValueData(17, "hdmi1", ["hdmi"])
        com = get_vcp_com(VCPCodes.input_source)
        assert data == info.value_data(com, 17, test_cfg)


class TestInfoStr:

    def test_feature_str(self):
        com = get_vcp_com(VCPCodes.input_source)
        data = info.FeatureData(com, [])
        assert info.feature_str(data) == f"{com.name} ({com.value})"

    def test_monitor_str_noalias(self):
        data = info.MonitorData(2, [])
        assert info.monitor_str(data) == "monitor #2"

    def test_monitor_str_onealias(self):
        data = info.MonitorData(0, ["foo"])
        assert info.monitor_str(data) == "monitor #0 (foo)"

    def test_monitor_str_multialias(self):
        data = info.MonitorData(1, ["bar", "baz"])
        assert info.monitor_str(data) == "monitor #1 (bar, baz)"

    def test_value_str_noparam_noalias(self):
        data = info.ValueData(80, "", [])
        assert info.value_str(data) == "80"

    def test_value_str_yesparam_noalias(self):
        data = info.ValueData(1, "on", [])
        assert info.value_str(data) == "1 (PARAM: on)"

    def test_value_str_noparam_yesalias(self):
        pass  # TODO: this will become relevant when we allow for aliases on all feature values

    def test_value_str_yesparam_yesalias(self):
        data = info.ValueData(17, "hdmi1", ["hdmi", "HDMI"])
        assert info.value_str(data) == "17 (PARAM: hdmi1 | ALIASES: hdmi, HDMI)"