from frozendict import frozendict

import pytest

from monitorboss import info, indentation
from monitorboss.info import MonitorData
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from ..testdata import *


class TestInfoFeatureData:

    @pytest.mark.parametrize("feature, expected", [
        (f_data_noname_242_noalias, {"code": 242}),
        (f_data_noname_243_alias, {"code": 243, "aliases": ('custom', 'custom_feature')}),
        (f_data_imageorientation_170_noalias, {"name": "image_orientation", "code": 170}),
        (f_data_inputsource_96_alias, {"name": "input_source", "code": 96, "aliases": ('src', 'source', 'input')}),
    ])
    def test_FeatureData_serialize(self, feature, expected):
        assert feature.serialize() == expected

    @pytest.mark.parametrize("feature, expected", [
        (f_data_noname_242_noalias, "242"),
        (f_data_noname_243_alias, "243"),
        (f_data_imageorientation_170_noalias, "image_orientation (170)"),
        (f_data_inputsource_96_alias, "input_source (96)"),
    ])
    def test_FeatureData_str(self, feature, expected):
        assert str(feature) == expected

    def test_feature_data_found_com(self, test_cfg):
        code = VCPCodes.input_source
        com = get_vcp_com(code)
        data = info.FeatureData(com.name, com.code, ('src', 'source', 'input'))
        assert info.feature_data(code.value, test_cfg) == data

    def test_feature_data_no_com(self, test_cfg):
        data = info.FeatureData("", 9001, ())
        assert info.feature_data(9001, test_cfg) == data


class TestInfoValueData:

    @pytest.mark.parametrize("value, expected", [
        (v_data_17_name_alias, {"value": 17, "param": 'hdmi1', "aliases": ('hdmi',)}),
        (v_data_2_noname_alias, {"value": 2, "aliases": ('cus', 'tom')}),
        (v_data_3_name_noalias, {"value": 3, "param": 'ct4000k'}),
        (v_data_1_noname_noalias, {"value": 1}),
    ])
    def test_ValueData_serialize(self, value: info.ValueData, expected):
        assert value.serialize() == expected

    @pytest.mark.parametrize("data, expected", [
        (v_data_1_noname_noalias, "1"),
        (v_data_3_name_noalias, "3 (PARAM: ct4000k)"),
        (v_data_2_noname_alias, "2 (ALIASES: cus, tom)"),
        (v_data_17_name_alias, "17 (PARAM: hdmi1 | ALIASES: hdmi)"),
    ])
    def test_ValueData_str(self, data, expected):
        assert str(data) == expected

    def test_value_data_found_com(self, test_cfg):
        assert info.value_data(96, 17, test_cfg) == v_data_17_name_alias

    def test_value_data_no_com(self, test_cfg):
        assert info.value_data(9001, 1, test_cfg) == v_data_1_noname_noalias


class TestInfoMonitorData:

    @pytest.mark.parametrize("mon, expected", [
        (m_data_0_foo, {"id": 0, "aliases": ('foo',)}),
        (m_data_1_barbaz, {"id": 1, "aliases": ('bar', 'baz')}),
        (m_data_2_noalias, {"id": 2})
    ])
    def test_MonitorData_serialize(self, mon: MonitorData, expected):
        assert mon.serialize() == expected

    @pytest.mark.parametrize("mon, expected", [
        (m_data_2_noalias, "monitor #2"),
        (m_data_0_foo, "monitor #0 (foo)"),
        (m_data_1_barbaz, "monitor #1 (bar, baz)"),
    ])
    def test_MonitorData_str(self, mon, expected):
        assert str(mon) == expected

    def test_monitor_data(self, test_cfg):
        assert info.monitor_data(1, test_cfg) == m_data_1_barbaz


class TestInfoCapabilitydata:

    value1 = info.ValueData(12, "", ())
    value2 = info.ValueData(24, "", ())
    attributes = frozendict({"foo": "bar", "baz": "qux"})
    cmds_single = frozendict({"cmds_0": (f_data_noname_242_noalias, f_data_noname_243_alias)})
    cmds_multi = frozendict({"cmds_0": (f_data_noname_242_noalias, f_data_noname_243_alias), "cmds_1": (f_data_noname_242_noalias, f_data_noname_243_alias)})
    vcps_single = frozendict({"vcp_0": frozendict({f_data_noname_242_noalias: (value1, value2), f_data_noname_243_alias: (value1, value2)})})
    vcps_multi = frozendict({"vcp_0": frozendict({f_data_noname_242_noalias: (value1, value2), f_data_noname_243_alias: (value1, value2)}),
                       "vcp_1": frozendict({f_data_noname_242_noalias: (value1, value2), f_data_noname_243_alias: (value1, value2)})})
    errata_single_blank = frozendict({"": ("foo", "bar")})
    errata_single_named = frozendict({"baz": ("qux", "corge")})
    errata_multi = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})

    def test_CapabilityData_serialize_no_errata(self):
        data = info.CapabilityData(self.attributes, self.cmds_multi, self.vcps_multi, frozendict())
        expected = {"foo": "bar", "baz": "qux",
                    "cmds":
                        {"cmds_0": [f_data_noname_242_noalias.serialize(), f_data_noname_243_alias.serialize()],
                         "cmds_1": [f_data_noname_242_noalias.serialize(), f_data_noname_243_alias.serialize()]},
                    "vcps":
                        {"vcp_0": [
                            {"feature": f_data_noname_242_noalias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                            {"feature": f_data_noname_243_alias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                        ],
                            "vcp_1": [
                                {"feature": f_data_noname_242_noalias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                            {"feature": f_data_noname_243_alias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                            ]}}
        assert data.serialize() == expected

    def test_CapabilityData_serialize_yes_errata(self):
        data = info.CapabilityData(self.attributes, self.cmds_multi, self.vcps_multi, self.errata_multi)
        expected = {"foo": "bar", "baz": "qux",
                    "cmds":
                        {"cmds_0": [f_data_noname_242_noalias.serialize(), f_data_noname_243_alias.serialize()],
                         "cmds_1": [f_data_noname_242_noalias.serialize(), f_data_noname_243_alias.serialize()]},
                    "vcps":
                        {"vcp_0": [
                            {"feature": f_data_noname_242_noalias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                            {"feature": f_data_noname_243_alias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
                        ],
                            "vcp_1": [
                                {"feature": f_data_noname_242_noalias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]},
                                {"feature": f_data_noname_243_alias.serialize(), "params": [self.value1.serialize(), self.value2.serialize()]}
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
        (cmds_single, f"cmds_0: {f_data_noname_242_noalias}, {f_data_noname_243_alias}"),
        (cmds_multi, f"CMDS:\n{indentation}cmds_0: {f_data_noname_242_noalias}, {f_data_noname_243_alias}\n{indentation}cmds_1: {f_data_noname_242_noalias}, {f_data_noname_243_alias}"),
    ])
    def test_CapabilityData_cmds_str(self, cmds_val, expected):
        data = info.CapabilityData(frozendict(), cmds_val, frozendict(), frozendict())
        assert data._cmds_str() == expected

    @pytest.mark.parametrize("vcps_val, expected", [
        (frozendict(), ""),
        (vcps_single, f"vcp_0:\n{indentation}* {f_data_noname_242_noalias}: {value1}, {value2}\n{indentation}* {f_data_noname_243_alias}: {value1}, {value2}"),
        (vcps_multi, (f"VCP:\n{indentation}vcp_0:\n{indentation}{indentation}* {f_data_noname_242_noalias}: {value1}, {value2}\n" +
                     f"{indentation}{indentation}* {f_data_noname_243_alias}: {value1}, {value2}\n{indentation}vcp_1:\n" +
                     f"{indentation}{indentation}* {f_data_noname_242_noalias}: {value1}, {value2}\n{indentation}{indentation}* {f_data_noname_243_alias}: {value1}, {value2}")),
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

    def test_capability_summary_data(self):
        # TODO: this is going to be very annoying, and the function will be changing when PYDDC updates its caps output
        #   so we will do later
        pass
