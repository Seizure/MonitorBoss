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

    def test_config_auto_create(self, pytester):
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

    def test_check_val_param(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "dp1", test_cfg) == 15

    def test_check_val_alias(self, test_cfg):
        assert cli._check_val(get_vcp_com(VCPCodes.input_source), "usb-c", test_cfg) == 27

    def test_check_val_invalid_yesparam_yesalias(self, capsys, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_val(get_vcp_com(VCPCodes.input_source), "foo", test_cfg)
            output = capsys.readouterr()
            assert output.out == ""
            assert "PARAM NAMES" in output.err
            assert "CONFIG ALIASES" in output.err

    def test_check_val_invalid_yesparam_noalias(self, capsys, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_val(get_vcp_com(VCPCodes.image_luminance), "foo", test_cfg)
            output = capsys.readouterr()
            assert output.out == ""
            assert "PARAM NAMES" in output.err
            assert "CONFIG ALIASES" not in output.err

    def test_check_val_invalid_noparam_yesalias(self, capsys, test_cfg):
        # TODO: this will become relevant when we allow for aliases on all feature values
        pass

    def test_check_val_invalid_noparam_noalias(self, capsys, test_cfg):
        with pytest.raises(MonitorBossError):
            cli._check_val(get_vcp_com(VCPCodes.image_luminance), "foo", test_cfg)
            output = capsys.readouterr()
            assert output.out == ""
            assert "PARAM NAMES" not in output.err
            assert "CONFIG ALIASES" not in output.err


class TestInfoFeatureData:

    def test_FeatureData_serialize_yesaliases(self):
        com = get_vcp_com(VCPCodes.input_source)
        data = info.FeatureData(com.name, com.code, tuple(['foo', 'bar', 'baz']))
        assert data.serialize() == {"name": "input_source", "code": 96, "aliases": ('foo', 'bar', 'baz')}

    # TODO: make this one test no name
    def test_FeatureData_serialize_noaliases(self):
        com = get_vcp_com(VCPCodes.input_source)
        data = info.FeatureData(com.name, com.code, tuple())
        assert data.serialize() == {"name": "input_source", "code": 96}

    def test_FeatureData_str_found_com(self):
        com = get_vcp_com(VCPCodes.input_source)
        data = info.FeatureData(com.name, com.code, tuple())
        assert data.__str__() == f"{com.name} ({com.code})"

    def test_FeatureData_str_no_com(self):
        # TODO: test for if no known com
        pass

    def test_feature_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        com = get_vcp_com(code)
        data = info.FeatureData(com.name, com.code, tuple(['src', 'source', 'input']))
        assert info.feature_data(code.value, test_cfg) == data

    def test_feature_data_no_com(self, test_cfg):
        # TODO: stub - test when code is not known com
        pass


class TestInfoValueData:

    def test_ValueData_serialize_yesparam_yesaliases(self):
        data = info.ValueData(75, 'foo', tuple(['bar', 'baz']))
        assert data.serialize() == {"value": 75, "param": 'foo', "aliases": ('bar', 'baz')}

    def test_ValueData_serialize_noparam_yesaliases(self):
        data = info.ValueData(75, '', tuple(['bar', 'baz']))
        assert data.serialize() == {"value": 75, "aliases": ('bar', 'baz')}

    def test_ValueData_serialize_yesparam_noaliases(self):
        data = info.ValueData(75, 'foo', tuple())
        assert data.serialize() == {"value": 75, "param": 'foo'}

    def test_ValueData_serialize_noparam_noaliases(self):
        data = info.ValueData(75, '', tuple())
        assert data.serialize() == {"value": 75}

    def test_ValueData_str_noparam_noalias(self):
        data = info.ValueData(24, "", tuple())
        assert data.__str__() == "24"

    def test_ValueData_str_yesparam_noalias(self):
        data = info.ValueData(24, "foo", tuple())
        assert data.__str__() == "24 (PARAM: foo)"

    def test_ValueData_str_noparam_yesalias(self):
        data = info.ValueData(24, "", tuple(['foo', 'bar']))
        assert data.__str__() == "24 (ALIASES: foo, bar)"

    def test_ValueData_str_yesparam_yesalias(self):
        data = info.ValueData(24, "foo", tuple(["bar", "baz"]))
        assert data.__str__() == "24 (PARAM: foo | ALIASES: bar, baz)"

    def test_value_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        data = info.ValueData(17, "hdmi1", tuple(["hdmi"]))
        assert data == info.value_data(code, 17, test_cfg)

    def test_value_data_no_com(self, test_cfg):
        # TODO: stub - test when code is not known com
        pass


class TestInfoMonitorData:

    def test_MonitorData_yesserialize(self):
        data = info.MonitorData(1, tuple(['foo', 'bar', 'baz']))
        assert data.serialize() == {"id": 1, "aliases": ('foo', 'bar', 'baz')}

    def test_MonitorData_serialize_noaliases(self):
        data = info.MonitorData(1, tuple())
        assert data.serialize() == {"id": 1}

    def test_MonitorData_str_noalias(self):
        data = info.MonitorData(2, tuple())
        assert data.__str__() == "monitor #2"

    def test_MonitorData_str_onealias(self):
        data = info.MonitorData(0, tuple(["foo"]))
        assert data.__str__() == "monitor #0 (foo)"

    def test_MonitorData_str_multialias(self):
        data = info.MonitorData(1, tuple(["bar", "baz"]))
        assert data.__str__() == "monitor #1 (bar, baz)"

    def test_monitor_data(self, test_cfg):
        data = info.MonitorData(1, tuple(['bar', 'baz']))
        assert info.monitor_data(1, test_cfg) == data


class TestInfoCapabilitydata:

    def test_CapabilityData_serialize_no_errata(self):
        # TODO: stub
        pass

    def test_CapabilityData_serialize_yes_errata(self):
        # TODO: stub
        pass

    def test_CapabilityData_str(self):
        # TODO: stub
        pass


    def test_capability_data(self):
        # TODO: stub
        pass
