from frozendict import frozendict

import pytest

from monitorboss import info, indentation
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes


class TestInfoFeatureData:

    @pytest.mark.parametrize("name, aliases, expected", [
        ("foo", ('foo', 'bar', 'baz'), {"name": "foo", "code": 42, "aliases": ('foo', 'bar', 'baz')}),
        ("", (), {"code": 42}),
    ])
    def test_FeatureData_serialize(self, name, aliases, expected):
        data = info.FeatureData(name, 42, aliases)
        assert data.serialize() == expected

    @pytest.mark.parametrize("name, expected", [
        ("foo", "foo (42)"),
        ("", "42"),
    ])
    def test_FeatureData_str(self, name, expected):
        data = info.FeatureData(name, 42, ())
        assert str(data) == expected

    def test_feature_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        com = get_vcp_com(code)
        data = info.FeatureData(com.name, com.code, ('src', 'source', 'input'))
        assert info.feature_data(code.value, test_cfg) == data

    def test_feature_data_no_com(self, test_cfg):
        data = info.FeatureData("", 9001, ())
        assert info.feature_data(9001, test_cfg) == data


class TestInfoValueData:

    @pytest.mark.parametrize("param, aliases, expected", [
        ('foo', ('bar', 'baz'), {"value": 75, "param": 'foo', "aliases": ('bar', 'baz')}),
        ('', ('bar', 'baz'), {"value": 75, "aliases": ('bar', 'baz')}),
        ('foo', (), {"value": 75, "param": 'foo'}),
        ('', (), {"value": 75}),
    ])
    def test_ValueData_serialize(self, param, aliases, expected):
        data = info.ValueData(75, param, aliases)
        assert data.serialize() == expected

    @pytest.mark.parametrize("param, aliases, expected", [
        ("", (), "24"),
        ("foo", (), "24 (PARAM: foo)"),
        ("", ('foo', 'bar'), "24 (ALIASES: foo, bar)"),
        ("foo", ("bar", "baz"), "24 (PARAM: foo | ALIASES: bar, baz)"),
    ])
    def test_ValueData_str(self, param, aliases, expected):
        data = info.ValueData(24, param, aliases)
        assert str(data) == expected

    def test_value_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        data = info.ValueData(17, "hdmi1", ("hdmi",))
        assert data == info.value_data(code, 17, test_cfg)

    def test_value_data_no_com(self, test_cfg):
        data = info.ValueData(17, "", ())
        assert data == info.value_data(9001, 17, test_cfg)


class TestInfoMonitorData:

    @pytest.mark.parametrize("aliases, expected", [
        (('foo', 'bar', 'baz'), {"id": 1, "aliases": ('foo', 'bar', 'baz')}),
        ((), {"id": 1}),
    ])
    def test_MonitorData_serialize(self, aliases, expected):
        data = info.MonitorData(1, aliases)
        assert data.serialize() == expected

    @pytest.mark.parametrize("id, aliases, expected", [
        (2, (), "monitor #2"),
        (0, ("foo",), "monitor #0 (foo)"),
        (1, ("bar", "baz"), "monitor #1 (bar, baz)"),
    ])
    def test_MonitorData_str(self, id, aliases, expected):
        data = info.MonitorData(id, aliases)
        assert str(data) == expected

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

    @pytest.mark.parametrize("attrs, expected", [
        (frozendict(), ""),
        (attributes, "foo: bar\nbaz: qux"),
    ])
    def test_CapabilityData_attr_str(self, attrs, expected):
        data = info.CapabilityData(attrs, frozendict(), frozendict(), frozendict())
        assert data._attr_str() == expected

    @pytest.mark.parametrize("cmds_val, expected", [
        (frozendict(), ""),
        (cmds_single, f"cmds_0: {feature1}, {feature2}"),
        (cmds_multi, f"CMDS:\n{indentation}cmds_0: {feature1}, {feature2}\n{indentation}cmds_1: {feature1}, {feature2}"),
    ])
    def test_CapabilityData_cmds_str(self, cmds_val, expected):
        data = info.CapabilityData(frozendict(), cmds_val, frozendict(), frozendict())
        assert data._cmds_str() == expected

    @pytest.mark.parametrize("vcps_val, expected", [
        (frozendict(), ""),
        (vcps_single, f"vcp_0:\n{indentation}* {feature1}: {value1}, {value2}\n{indentation}* {feature2}: {value1}, {value2}"),
        (vcps_multi, (f"VCP:\n{indentation}vcp_0:\n{indentation}{indentation}* {feature1}: {value1}, {value2}\n" +
                     f"{indentation}{indentation}* {feature2}: {value1}, {value2}\n{indentation}vcp_1:\n" +
                     f"{indentation}{indentation}* {feature1}: {value1}, {value2}\n{indentation}{indentation}* {feature2}: {value1}, {value2}")),
    ])
    def test_CapabilityData_vcp_str(self, vcps_val, expected):
        data = info.CapabilityData(frozendict(), frozendict(), vcps_val, frozendict())
        assert data._vcp_str() == expected

    @pytest.mark.parametrize("errata_val, expected", [
        (frozendict(), ""),
        (errata_single_named, f"Errata:\n{indentation}baz: qux, corge"),
        (errata_single_blank, "Errata: foo, bar"),
        (errata_multi, f"Errata:\n{indentation}foo, bar\n{indentation}baz: qux, corge"),
    ])
    def test_CapabilityData_errata_str(self, errata_val, expected):
        data = info.CapabilityData(frozendict(), frozendict(), frozendict(), errata_val)
        assert data._errata_str() == expected

    @pytest.mark.parametrize("attrs,cmds_val,vcps_val,errata_val", [
        (attributes, cmds_multi, vcps_multi, errata_multi),
        (frozendict(), cmds_multi, vcps_multi, errata_multi),
        (attributes, frozendict(), vcps_multi, errata_multi),
        (attributes, cmds_multi, frozendict(), errata_multi),
        (attributes, cmds_multi, vcps_multi, frozendict()),
    ])
    def test_CapabilityData_str_combinations(self, attrs, cmds_val, vcps_val, errata_val):
        data = info.CapabilityData(attrs, cmds_val, vcps_val, errata_val)
        parts = []
        if attrs:
            parts.append(data._attr_str())
        if cmds_val:
            parts.append(data._cmds_str())
        if vcps_val:
            parts.append(data._vcp_str())
        if errata_val:
            parts.append(data._errata_str())
        expected = "\n".join(parts)
        assert str(data) == expected

    def test_capability_data(self):
        # TODO: this is going to be very annoying, and the function will be changing when PYDDC updates its caps output
        #   so we will do later
        pass
