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

    def test_CapabilityData_serialize_no_errata(self, test_cfg):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(24, "", ())
        attributes = frozendict({"foo": "bar", "baz": "qux"})
        cmds = frozendict({"cmds_0": (feature1, feature2), "cmds_1": (feature1, feature2)})
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
        data = info.CapabilityData(attributes, cmds, vcps, frozendict())

        expected = {"foo": "bar", "baz": "qux",
                    "cmds":
                        {"cmds_0": [feature1.serialize(), feature2.serialize()],
                         "cmds_1": [feature1.serialize(), feature2.serialize()]},
                    "vcps":
                        {"vcp_0": [
                            {"feature": feature1.serialize(), "params": [value1.serialize(), value2.serialize()]},
                            {"feature": feature2.serialize(), "params": [value1.serialize(), value2.serialize()]}
                        ],
                            "vcp_1": [
                                {"feature": feature1.serialize(), "params": [value1.serialize(), value2.serialize()]},
                            {"feature": feature2.serialize(), "params": [value1.serialize(), value2.serialize()]}
                            ]}}

        assert data.serialize() == expected

    def test_CapabilityData_serialize_yes_errata(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(24, "", ())
        attributes = frozendict({"foo": "bar", "baz": "qux"})
        cmds = frozendict({"cmds_0": (feature1, feature2), "cmds_1": (feature1, feature2)})
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
        errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
        data = info.CapabilityData(attributes, cmds, vcps, errata)

        expected = {"foo": "bar", "baz": "qux",
                    "cmds":
                        {"cmds_0": [feature1.serialize(), feature2.serialize()],
                         "cmds_1": [feature1.serialize(), feature2.serialize()]},
                    "vcps":
                        {"vcp_0": [
                            {"feature": feature1.serialize(), "params": [value1.serialize(), value2.serialize()]},
                            {"feature": feature2.serialize(), "params": [value1.serialize(), value2.serialize()]}
                        ],
                            "vcp_1": [
                                {"feature": feature1.serialize(), "params": [value1.serialize(), value2.serialize()]},
                                {"feature": feature2.serialize(), "params": [value1.serialize(), value2.serialize()]}
                            ]},
                    "errata": {"": ("foo", "bar"), "baz": ("qux", "corge")}}

        assert data.serialize() == expected

    def test_CapabilityData_attr_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())

        assert data._attr_str() == ""

    def test_CapabilityData_attr_str_present(self):
        attributes = frozendict({"foo": "bar", "baz": "qux"})
        data = info.CapabilityData(attributes, frozendict(), frozendict(), frozendict())

        assert data._attr_str() == "foo: bar\nbaz: qux\n"

    def test_CapabilityData_cmds_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())

        assert data._cmds_str() == ""

    def test_CapabilityData_cmds_str_single(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        cmds = frozendict({"cmds_0": (feature1, feature2)})
        data = info.CapabilityData(frozendict(), cmds, frozendict(), frozendict())

        assert data._cmds_str() == f"cmds_0: {feature1}, {feature2}\n"

    def test_CapabilityData_cmds_str_multi(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        cmds = frozendict({"cmds_0": (feature1, feature2), "cmds_1": (feature1, feature2)})
        data = info.CapabilityData(frozendict(), cmds, frozendict(), frozendict())

        assert data._cmds_str() == f"CMDS:\n{indentation}cmds_0: {feature1}, {feature2}\n{indentation}cmds_1: {feature1}, {feature2}\n"

    def test_CapabilityData_vcp_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())

        assert data._vcp_str() == ""

    def test_CapabilityData_vcp_str_single(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(24, "", ())
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
        data = info.CapabilityData(frozendict(), frozendict(), vcps, frozendict())

        assert data._vcp_str() == f"vcp_0:\n{indentation}* {feature1}: {value1}, {value2}\n{indentation}* {feature2}: {value1}, {value2}\n"

    def test_CapabilityData_vcp_str_multi(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(24, "", ())
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
        data = info.CapabilityData(frozendict(), frozendict(), vcps, frozendict())

        assert data._vcp_str() == (f"VCP:\n{indentation}vcp_0:\n{indentation}{indentation}* {feature1}: {value1}, {value2}\n" +
                                   f"{indentation}{indentation}* {feature2}: {value1}, {value2}\n{indentation}vcp_1:\n" +
                                   f"{indentation}{indentation}* {feature1}: {value1}, {value2}\n{indentation}{indentation}* {feature2}: {value1}, {value2}\n")

    def test_CapabilityData_errata_str_empty(self):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), frozendict())

        assert data._errata_str() == ""

    def test_CapabilityData_errata_str_single_named(self):
        errata = frozendict({"baz": ("qux", "corge")})
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), errata)

        assert data._errata_str() == f"Errata:\n{indentation}baz: qux, corge"

    def test_CapabilityData_errata_str_single_blank(self):
        errata = frozendict({"": ("foo", "bar")})
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), errata)

        assert data._errata_str() == "Errata: foo, bar"

    def test_CapabilityData_errata_str_multi(self):
        errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), errata)

        assert data._errata_str() == f"Errata:\n{indentation}foo, bar\n{indentation}baz: qux, corge"

    def test_CapabilityData_str(self):
        feature1 = info.FeatureData("", 42, ())
        feature2 = info.FeatureData("", 84, ())
        value1 = info.ValueData(12, "", ())
        value2 = info.ValueData(24, "", ())
        attributes = frozendict({"foo": "bar", "baz": "qux"})
        cmds = frozendict({"cmds_0": (feature1, feature2), "cmds_1": (feature1, feature2)})
        vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2)}),
                           "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2)})})
        errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
        data = info.CapabilityData(attributes, cmds, vcps, errata)

        expected = f"{data._attr_str()}{data._cmds_str()}{data._vcp_str()}{data._errata_str()}"

        assert str(data) == expected

    def test_capability_data(self):
        # TODO: this is going to be very annoying, and the function will be changing when PYDDC updates its caps output
        #   so we will do later
        pass
