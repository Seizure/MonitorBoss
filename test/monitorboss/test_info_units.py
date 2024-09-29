from frozendict import frozendict

from monitorboss import info, indentation
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes


class TestInfoFeatureData:

    def test_FeatureData_serialize_yesname_yesaliases(self):
        data = info.FeatureData("foo", 42, ('foo', 'bar', 'baz'))
        assert data.serialize() == {"name": "foo", "code": 42, "aliases": ('foo', 'bar', 'baz')}

    def test_FeatureData_serialize_noname_noaliases(self):
        data = info.FeatureData("", 42, ())
        assert data.serialize() == {"code": 42}

    def test_FeatureData_str_yesname(self):
        data = info.FeatureData("foo", 42, ())
        assert str(data) == "foo (42)"

    def test_FeatureData_str_noname(self):
        data = info.FeatureData("", 42, ())
        assert str(data) == "42"

    def test_feature_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        com = get_vcp_com(code)
        data = info.FeatureData(com.name, com.code, ('src', 'source', 'input'))
        assert info.feature_data(code.value, test_cfg) == data

    def test_feature_data_no_com(self, test_cfg):
        data = info.FeatureData("", 9001, ())
        assert info.feature_data(9001, test_cfg) == data


class TestInfoValueData:

    def test_ValueData_serialize_yesparam_yesaliases(self):
        data = info.ValueData(75, 'foo', ('bar', 'baz'))
        assert data.serialize() == {"value": 75, "param": 'foo', "aliases": ('bar', 'baz')}

    def test_ValueData_serialize_noparam_yesaliases(self):
        data = info.ValueData(75, '', ('bar', 'baz'))
        assert data.serialize() == {"value": 75, "aliases": ('bar', 'baz')}

    def test_ValueData_serialize_yesparam_noaliases(self):
        data = info.ValueData(75, 'foo', ())
        assert data.serialize() == {"value": 75, "param": 'foo'}

    def test_ValueData_serialize_noparam_noaliases(self):
        data = info.ValueData(75, '', ())
        assert data.serialize() == {"value": 75}

    def test_ValueData_str_noparam_noalias(self):
        data = info.ValueData(24, "", ())
        assert str(data) == "24"

    def test_ValueData_str_yesparam_noalias(self):
        data = info.ValueData(24, "foo", ())
        assert str(data) == "24 (PARAM: foo)"

    def test_ValueData_str_noparam_yesalias(self):
        data = info.ValueData(24, "", ('foo', 'bar'))
        assert str(data) == "24 (ALIASES: foo, bar)"

    def test_ValueData_str_yesparam_yesalias(self):
        data = info.ValueData(24, "foo", ("bar", "baz"))
        assert str(data) == "24 (PARAM: foo | ALIASES: bar, baz)"

    def test_value_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        data = info.ValueData(17, "hdmi1", ("hdmi",))
        assert data == info.value_data(code, 17, test_cfg)

    def test_value_data_no_com(self, test_cfg):
        data = info.ValueData(17, "", ())
        assert data == info.value_data(9001, 17, test_cfg)


class TestInfoMonitorData:

    def test_MonitorData_yesserialize(self):
        data = info.MonitorData(1, ('foo', 'bar', 'baz'))
        assert data.serialize() == {"id": 1, "aliases": ('foo', 'bar', 'baz')}

    def test_MonitorData_serialize_noaliases(self):
        data = info.MonitorData(1, ())
        assert data.serialize() == {"id": 1}

    def test_MonitorData_str_noalias(self):
        data = info.MonitorData(2, ())
        assert str(data) == "monitor #2"

    def test_MonitorData_str_onealias(self):
        data = info.MonitorData(0, ("foo",))
        assert str(data) == "monitor #0 (foo)"

    def test_MonitorData_str_multialias(self):
        data = info.MonitorData(1, ("bar", "baz"))
        assert str(data) == "monitor #1 (bar, baz)"

    def test_monitor_data(self, test_cfg):
        data = info.MonitorData(1, ("bar", "baz"))
        assert info.monitor_data(1, test_cfg) == data


class TestInfoCapabilitydata:

    feature1 = info.FeatureData("", 42, ())
    feature2 = info.FeatureData("", 84, ())
    value1 = info.ValueData(12, "", ())
    value2 = info.ValueData(24, "", ())
    attributes = frozendict({"foo": "bar", "baz": "qux"})
    cmds_single = frozendict({"cmds_0": (feature1, feature2)})
    cmds_multi = frozendict({"cmds_0": (feature1, feature2), "cmds_1": (feature1, feature2)})
    vcps_single = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
    vcps_multi = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)}),
                       "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
    errata_single_blank = frozendict({"": ("foo", "bar")})
    errata_single_named = frozendict({"baz": ("qux", "corge")})
    errata_multi = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})

    def test_CapabilityData_serialize_no_errata(self, test_cfg):
        data = info.CapabilityData(self.attributes, self.cmds_multi, self.vcps_multi, frozendict())
        expected = {"foo": "bar", "baz": "qux",
                    "cmds":
                        {"cmds_0": [self.feature1.serialize(), self.feature2.serialize()],
                         "cmds_1": [self.feature1.serialize(), self.feature2.serialize()]},
                    "vcps":
                        {"vcp_0": [
                            {"feature": self.feature1.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                            {"feature": self.feature2.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                        ],
                            "vcp_1": [
                                {"feature": self.feature1.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                            {"feature": self.feature2.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                            ]}}
        assert data.serialize() == expected

    def test_CapabilityData_serialize_yes_errata(self):
        data = info.CapabilityData(self.attributes, self.cmds_multi, self.vcps_multi, self.errata_multi)
        expected = {"foo": "bar", "baz": "qux",
                    "cmds":
                        {"cmds_0": [self.feature1.serialize(), self.feature2.serialize()],
                         "cmds_1": [self.feature1.serialize(), self.feature2.serialize()]},
                    "vcps":
                        {"vcp_0": [
                            {"feature": self.feature1.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                            {"feature": self.feature2.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                        ],
                            "vcp_1": [
                                {"feature": self.feature1.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                                {"feature": self.feature2.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                            ]},
                    "errata": {"": ("foo", "bar"), "baz": ("qux", "corge")}}
        assert data.serialize() == expected

    def test_CapabilityData_attr_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())
        assert data._attr_str() == ""

    def test_CapabilityData_attr_str_present(self):
        data = info.CapabilityData(self.attributes, frozendict(), frozendict(), frozendict())
        expected = "foo: bar\nbaz: qux"
        assert data._attr_str() == expected

    def test_CapabilityData_cmds_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())
        assert data._cmds_str() == ""

    def test_CapabilityData_cmds_str_single(self):
        data = info.CapabilityData(frozendict(), self.cmds_single, frozendict(), frozendict())
        expected = f"cmds_0: {self.feature1}, {self.feature2}"
        assert data._cmds_str() == expected

    def test_CapabilityData_cmds_str_multi(self):
        data = info.CapabilityData(frozendict(), self.cmds_multi, frozendict(), frozendict())
        expected = f"CMDS:\n{indentation}cmds_0: {self.feature1}, {self.feature2}\n{indentation}cmds_1: {self.feature1}, {self.feature2}"
        assert data._cmds_str() == expected

    def test_CapabilityData_vcp_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())
        assert data._vcp_str() == ""

    def test_CapabilityData_vcp_str_single(self):
        data = info.CapabilityData(frozendict(), frozendict(), self.vcps_single, frozendict())
        expected = f"vcp_0:\n{indentation}* {self.feature1}: {self.value1}, {self.value2}\n{indentation}* {self.feature2}: {self.value1}, {self.value2}"
        assert data._vcp_str() == expected

    def test_CapabilityData_vcp_str_multi(self):
        data = info.CapabilityData(frozendict(), frozendict(), self.vcps_multi, frozendict())
        expected = (f"VCP:\n{indentation}vcp_0:\n{indentation}{indentation}* {self.feature1}: {self.value1}, {self.value2}\n" +
                    f"{indentation}{indentation}* {self.feature2}: {self.value1}, {self.value2}\n{indentation}vcp_1:\n" +
                    f"{indentation}{indentation}* {self.feature1}: {self.value1}, {self.value2}\n{indentation}{indentation}* {self.feature2}: {self.value1}, {self.value2}")
        assert data._vcp_str() == expected

    def test_CapabilityData_errata_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())
        assert data._errata_str() == ""

    def test_CapabilityData_errata_str_single_named(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), self.errata_single_named)
        expected = f"Errata:\n{indentation}baz: qux, corge"
        assert data._errata_str() == expected

    def test_CapabilityData_errata_str_single_blank(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), self.errata_single_blank)
        expected = "Errata: foo, bar"
        assert data._errata_str() == expected

    def test_CapabilityData_errata_str_multi(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), self.errata_multi)
        expected = f"Errata:\n{indentation}foo, bar\n{indentation}baz: qux, corge"
        assert data._errata_str() == expected

    def test_CapabilityData_str_all(self):
        data = info.CapabilityData(self.attributes, self.cmds_multi, self.vcps_multi, self.errata_multi)
        expected = f"{data._attr_str()}\n{data._cmds_str()}\n{data._vcp_str()}\n{data._errata_str()}"
        assert str(data) == expected

    def test_CapabilityData_str_missing_attr(self):
        data = info.CapabilityData(frozendict(), self.cmds_multi, self.vcps_multi, self.errata_multi)
        expected = f"{data._attr_str()}\n{data._cmds_str()}\n{data._vcp_str()}\n{data._errata_str()}"
        assert str(data) == expected

    def test_CapabilityData_str_missing_cmds(self):
        data = info.CapabilityData(self.attributes, frozendict(), self.vcps_multi, self.errata_multi)
        expected = f"{data._attr_str()}\n{data._cmds_str()}\n{data._vcp_str()}\n{data._errata_str()}"
        assert str(data) == expected

    def test_CapabilityData_str_missing_vcp(self):
        data = info.CapabilityData(self.attributes, self.cmds_multi, frozendict(), self.errata_multi)
        expected = f"{data._attr_str()}\n{data._cmds_str()}\n{data._vcp_str()}\n{data._errata_str()}"
        assert str(data) == expected

    def test_CapabilityData_str_missing_errata(self):
        data = info.CapabilityData(self.attributes, self.cmds_multi, self.vcps_multi, frozendict())
        expected = f"{data._attr_str()}\n{data._cmds_str()}\n{data._vcp_str()}\n{data._errata_str()}"
        assert str(data) == expected

    def test_capability_data(self):
        # TODO: this is going to be very annoying, and the function will be changing when PYDDC updates its caps output
        #   so we will do later
        pass
