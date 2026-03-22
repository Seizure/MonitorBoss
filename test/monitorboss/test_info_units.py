import textwrap

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
    def test_MonitorData_serialize(self, mon, expected):
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

    cmds_0_substring = f"cmds_0: {f_data_noname_242_noalias}, {f_data_noname_243_alias}, {f_data_inputsource_96_alias}"
    cmds_1_substring = f"cmds_1: {f_data_noname_242_noalias}, {f_data_noname_243_alias}, {f_data_imageorientation_170_noalias}"
    vcp_0_substring = "vcp_0:\n" + \
                        f"{indentation}* {f_data_noname_242_noalias}: {v_data_1_noname_noalias}, {v_data_2_noname_alias}\n" + \
                        f"{indentation}* {f_data_noname_243_alias}: {v_data_1_noname_noalias}, {v_data_2_noname_alias}\n" + \
                        f"{indentation}* {f_data_inputsource_96_alias}: {v_data_3_name_noalias}"
    vcp_1_substring = f"vcp_1:\n" + \
                        f"{indentation}* {f_data_noname_242_noalias}: {v_data_1_noname_noalias}, {v_data_2_noname_alias}\n" + \
                        f"{indentation}* {f_data_noname_243_alias}: {v_data_1_noname_noalias}, {v_data_2_noname_alias}\n" + \
                        f"{indentation}* {f_data_imageorientation_170_noalias}: {v_data_17_name_alias}"

    attrs_serialized = {"model": "DUMMY", "foo": "bar", "baz": "qux", "type": "LCD"}
    cmds_0_serialized = {"cmds_0": [f_data_noname_242_noalias.serialize(), f_data_noname_243_alias.serialize(), f_data_inputsource_96_alias.serialize()]}
    cmds_1_serialized = {"cmds_1": [f_data_noname_242_noalias.serialize(), f_data_noname_243_alias.serialize(), f_data_imageorientation_170_noalias.serialize()]}
    vcp_0_serialized = {"vcp_0": [{"feature": f_data_noname_242_noalias.serialize(), "params": [v_data_1_noname_noalias.serialize(), v_data_2_noname_alias.serialize()]},
                                {"feature": f_data_noname_243_alias.serialize(), "params": [v_data_1_noname_noalias.serialize(), v_data_2_noname_alias.serialize()]},
                                {"feature": f_data_inputsource_96_alias.serialize(), "params": [v_data_3_name_noalias.serialize()]}]}
    vcp_1_serialized = {"vcp_1": [{"feature": f_data_noname_242_noalias.serialize(), "params": [v_data_1_noname_noalias.serialize(), v_data_2_noname_alias.serialize()]},
                                {"feature": f_data_noname_243_alias.serialize(), "params": [v_data_1_noname_noalias.serialize(), v_data_2_noname_alias.serialize()]},
                                {"feature": f_data_imageorientation_170_noalias.serialize(), "params": [v_data_17_name_alias.serialize()]}]}
    errata_both_serialized = {"errata": {"": ("foo", "bar"), "baz": ("qux", "corge")}}



    @pytest.mark.parametrize("attrs, expected", [
        (frozendict(), ""),
        (caps_attrs, "model: DUMMY\nfoo: bar\nbaz: qux\ntype: LCD"),
    ])
    def test_CapabilityData_attr_str(self, attrs, expected):
        caps = info.CapabilityData(attrs, frozendict(), frozendict(), frozendict())
        assert caps._attr_str() == expected

    @pytest.mark.parametrize("cmds, expected", [
        (frozendict(), ""),
        (caps_cmds_single, cmds_0_substring),
        (caps_cmds_multi, f"CMDS:\n" +
                    f"{indentation}{cmds_0_substring}\n" +
                    f"{indentation}{cmds_1_substring}"),
    ])
    def test_CapabilityData_cmds_str(self, cmds, expected):
        caps = info.CapabilityData(frozendict(), cmds, frozendict(), frozendict())
        assert caps._cmds_str() == expected

    @pytest.mark.parametrize("vcp, expected", [
        (frozendict(), ""),
        (caps_vcps_single, vcp_0_substring),
        (caps_vcps_multi, (f"VCP:\n" +
                        f"{textwrap.indent(vcp_0_substring, indentation)}\n" +
                        f"{textwrap.indent(vcp_1_substring, indentation)}")),
    ])
    def test_CapabilityData_vcp_str(self, vcp, expected):
        caps = info.CapabilityData(frozendict(), frozendict(), vcp, frozendict())
        assert caps._vcp_str() == expected

    @pytest.mark.parametrize("errata, expected", [
        (frozendict(), ""),
        (caps_errata_named, f"Errata:\n{indentation}baz: qux, corge"),
        (caps_errata_unnamed, "Errata: foo, bar"),
        (caps_errata_both, f"Errata:\n{indentation}foo, bar\n{indentation}baz: qux, corge"),
    ])
    def test_CapabilityData_errata_str(self, errata, expected):
        caps = info.CapabilityData(frozendict(), frozendict(), frozendict(), errata)
        assert caps._errata_str() == expected

    @pytest.mark.parametrize("has_errata", [
        (False,),
        (True,)
    ])
    def test_CapabilityData_serialize(self, has_errata):
        data = info.CapabilityData(caps_attrs, caps_cmds_multi, caps_vcps_multi, caps_errata_both if has_errata else frozendict())
        expected = {**caps_attrs,
                    "cmds":
                        {**self.cmds_0_serialized, **self.cmds_1_serialized},
                    "vcps":
                        {**self.vcp_0_serialized, **self.vcp_1_serialized},
                    **(self.errata_both_serialized if has_errata else frozendict()),
                    }
        assert data.serialize() == expected

    @pytest.mark.parametrize("attrs,cmds_val,vcps_val,errata_val", [
        (caps_attrs, caps_cmds_multi, caps_vcps_multi, caps_errata_both),
        (frozendict(), caps_cmds_multi, caps_vcps_multi, caps_errata_both),
        (caps_attrs, frozendict(), caps_vcps_multi, caps_errata_both),
        (caps_attrs, caps_cmds_multi, frozendict(), caps_errata_both),
        (caps_attrs, caps_cmds_multi, caps_vcps_multi, frozendict()),
    ])
    def test_CapabilityData_str(self, attrs, cmds_val, vcps_val, errata_val):
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


class TestMonitorGetResponseData:
    """Tests for MonitorGetResponseData - get_feature operations"""

    @pytest.mark.parametrize("mon, error, value, maximum, expected", [
        (m_data_0_foo, None, v_data_17_name_alias, None, {"monitor": m_data_0_foo.serialize(), "value": v_data_17_name_alias.serialize()}),
        (m_data_1_barbaz, None, v_data_3_name_noalias, 100, {"monitor": m_data_1_barbaz.serialize(), "value": v_data_3_name_noalias.serialize(), "max_value": 100}),
        (m_data_2_noalias, Exception("could not get brightness for monitor #2."), None, None, {"monitor": m_data_2_noalias.serialize(), "error": "could not get brightness for monitor #2."}),
    ])
    def test_serialize(self, mon, error, value, maximum, expected):
        response = info.MonitorGetResponseData(mon=mon, error=error, value=value, maximum=maximum)
        result = response.serialize()
        assert result == expected

    @pytest.mark.parametrize("mon, error, value, maximum, expected", [
        (m_data_0_foo, None, v_data_17_name_alias, None, f"{m_data_0_foo} is {v_data_17_name_alias}"),
        (m_data_1_barbaz, None, v_data_3_name_noalias, 100, f"{m_data_1_barbaz} is {v_data_3_name_noalias} (Maximum: 100)"),
        (m_data_2_noalias, Exception("could not get brightness for monitor #2."), None, None, f"{m_data_2_noalias}: ERROR - could not get brightness for monitor #2."),
    ])
    def test_str(self, mon, error, value, maximum, expected):
        response = info.MonitorGetResponseData(mon=mon, error=error, value=value, maximum=maximum)
        assert str(response) == expected


class TestMonitorSetResponseData:
    """Tests for MonitorSetResponseData - set_feature operations"""

    @pytest.mark.parametrize("mon, error, value, expected", [
        (m_data_0_foo, None, v_data_3_name_noalias, {"monitor": m_data_0_foo.serialize(), "value": v_data_3_name_noalias.serialize()}),
        (m_data_1_barbaz, Exception("could not set brightness for monitor #1 to 50."), None, {"monitor": m_data_1_barbaz.serialize(), "error": "could not set brightness for monitor #1 to 50."}),
    ])
    def test_serialize(self, mon, error, value, expected):
        response = info.MonitorSetResponseData(mon=mon, error=error, value=value)
        result = response.serialize()
        assert result == expected

    @pytest.mark.parametrize("mon, error, value, expected", [
        (m_data_0_foo, None, v_data_3_name_noalias, f"set {m_data_0_foo} to {v_data_3_name_noalias}"),
        (m_data_1_barbaz, Exception("could not set brightness for monitor #1 to 50."), None, f"{m_data_1_barbaz}: ERROR - could not set brightness for monitor #1 to 50."),
    ])
    def test_str(self, mon, error, value, expected):
        response = info.MonitorSetResponseData(mon=mon, error=error, value=value)
        assert str(response) == expected


class TestMonitorToggleResponseData:
    """Tests for MonitorToggleResponseData - toggle_feature operations"""

    @pytest.mark.parametrize("mon, error, original_value, new_value, expected", [
        (m_data_0_foo, None, v_data_3_name_noalias, v_data_17_name_alias, {"monitor": m_data_0_foo.serialize(), "original_value": v_data_3_name_noalias.serialize(), "new_value": v_data_17_name_alias.serialize()}),
        (m_data_1_barbaz, None, v_data_1_noname_noalias, v_data_2_noname_alias, {"monitor": m_data_1_barbaz.serialize(), "original_value": v_data_1_noname_noalias.serialize(), "new_value": v_data_2_noname_alias.serialize()}),
        (m_data_2_noalias, Exception("could not toggle brightness for monitor #0."), None, None, {"monitor": m_data_2_noalias.serialize(), "error": "could not toggle brightness for monitor #0."}),
    ])
    def test_serialize(self, mon, error, original_value, new_value, expected):
        response = info.MonitorToggleResponseData(mon=mon, error=error, original_value=original_value, new_value=new_value)
        result = response.serialize()
        assert result == expected

    @pytest.mark.parametrize("mon, error, original_value, new_value, expected", [
        (m_data_0_foo, None, v_data_3_name_noalias, v_data_17_name_alias, f"toggled {m_data_0_foo} from {v_data_3_name_noalias} to {v_data_17_name_alias}"),
        (m_data_1_barbaz, None, v_data_1_noname_noalias, v_data_2_noname_alias, f"toggled {m_data_1_barbaz} from {v_data_1_noname_noalias} to {v_data_2_noname_alias}"),
        (m_data_2_noalias, Exception("could not toggle brightness for monitor #0."), None, None, f"{m_data_2_noalias}: ERROR - could not toggle brightness for monitor #0."),
    ])
    def test_str(self, mon, error, original_value, new_value, expected):
        response = info.MonitorToggleResponseData(mon=mon, error=error, original_value=original_value, new_value=new_value)
        assert str(response) == expected


class TestMonitorCapsResponseData:
    """Tests for MonitorCapsResponseData - capabilities operations"""

    @pytest.mark.parametrize("mon, error, data, expected", [
        (m_data_0_foo, None, "(prot(monitor)type(LCD)model(TEST))", {"monitor": m_data_0_foo.serialize(), "data": "(prot(monitor)type(LCD)model(TEST))"}),
        (m_data_1_barbaz, None, info.CapabilityData(caps_attrs, caps_cmds_multi, caps_vcps_single, frozendict()), {"monitor": m_data_1_barbaz.serialize(), "data": info.CapabilityData(caps_attrs, caps_cmds_multi, caps_vcps_single, frozendict()).serialize()}),
        (m_data_2_noalias, Exception("could not get capabilities for monitor #1."), None, {"monitor": m_data_2_noalias.serialize(), "error": "could not get capabilities for monitor #1."}),
    ])
    def test_serialize(self, mon, error, data, expected):
        response = info.MonitorCapsResponseData(mon=mon, error=error, data=data)
        result = response.serialize()
        assert result == expected

    @pytest.mark.parametrize("mon, error, data, expected", [
        (m_data_0_foo, None, "foo bar baz", f"Capability string for {m_data_0_foo}:\n{indentation}foo bar baz"),
        (m_data_1_barbaz, None, info.CapabilityData(caps_attrs, frozendict(), frozendict(), frozendict()), f"{m_data_1_barbaz}:\n{textwrap.indent(str(info.CapabilityData(caps_attrs, frozendict(), frozendict(), frozendict())), indentation)}"),
        (m_data_2_noalias, Exception("could not get capabilities for monitor #1."), None, f"{m_data_2_noalias}: ERROR - could not get capabilities for monitor #1."),
    ])
    def test_str(self, mon, error, data, expected):
        response = info.MonitorCapsResponseData(mon=mon, error=error, data=data)
        assert str(response) == expected
