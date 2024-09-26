from monitorboss import info
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes


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

    def test_CapabilityData_attr_str_empty(self):
        # TODO: stub
        pass

    def test_CapabilityData_attr_str_present(self):
        # TODO: stub
        pass

    def test_CapabilityData_cmds_str_empty(self):
        # TODO: stub
        pass

    def test_CapabilityData_cmds_str_single(self):
        # TODO: stub
        pass

    def test_CapabilityData_cmds_str_multi(self):
        # TODO: stub
        pass

    def test_CapabilityData_vcp_str_empty(self):
        # TODO: stub
        pass

    def test_CapabilityData_vcp_str_single(self):
        # TODO: stub
        pass

    def test_CapabilityData_vcp_str_multi(self):
        # TODO: stub
        pass

    def test_CapabilityData_errata_str_empty(self):
        # TODO: stub
        pass

    def test_CapabilityData_errata_str_single_named(self):
        # TODO: stub
        pass

    def test_CapabilityData_errata_str_single_blank(self):
        # TODO: stub
        pass

    def test_CapabilityData_errata_str_multi(self):
        # TODO: stub
        pass

    def test_CapabilityData_str(self):
        # TODO: stub
        pass

    def test_capability_data(self):
        # TODO: stub
        pass
