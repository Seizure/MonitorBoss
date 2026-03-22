import json
import textwrap

import pytest

from frozendict import frozendict

from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import indentation, output, info
from ..testdata import *


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"list": [{"monitor": m_data_0_foo.serialize()}, {"monitor": m_data_1_barbaz.serialize()}]})),
    (False, f"{m_data_0_foo}\n{m_data_1_barbaz}")
])
def test_list_mons(json_flag, expected):
    assert output.list_mons_output([m_data_0_foo, m_data_1_barbaz], json_flag) == expected


@pytest.mark.parametrize("json_flag,expected", [
    (True, json.dumps({"get": {"feature": f_data_noname_242_noalias.serialize(), "responses": [
                        {"monitor": m_data_0_foo.serialize(), "value": v_data_17_name_alias.serialize()},
                        {"monitor": m_data_1_barbaz.serialize(), "error": "could not get value for monitor 1"},
                        {"monitor": m_data_2_noalias.serialize(), "value": v_data_3_name_noalias.serialize(), "max_value": 100}]}})),
    (False, f"Getting {f_data_noname_242_noalias}:\n"
            f"{indentation}{m_data_0_foo} is {v_data_17_name_alias}\n"
            f"{indentation}{m_data_1_barbaz}: ERROR - could not get value for monitor 1\n"
            f"{indentation}{m_data_2_noalias} is {v_data_3_name_noalias} (Maximum: 100)")])
def test_get_feature(json_flag, expected):
    responses = [
        info.MonitorGetResponseData(mon=m_data_0_foo, error=None, value=v_data_17_name_alias, maximum=None),
        info.MonitorGetResponseData(mon=m_data_1_barbaz, error=Exception("could not get value for monitor 1"), value=None, maximum=None),
        info.MonitorGetResponseData(mon=m_data_2_noalias, error=None, value=v_data_3_name_noalias, maximum=100)
    ]
    assert output.get_feature_output(f_data_noname_242_noalias, responses, json_flag) == expected


@pytest.mark.parametrize("json_flag,expected", [
    (True, json.dumps({"set": {"feature": f_data_noname_242_noalias.serialize(), "responses": [
                        {"monitor": m_data_0_foo.serialize(), "value": v_data_3_name_noalias.serialize()},
                        {"monitor": m_data_1_barbaz.serialize(), "error": "monitor not responding"},
                        {"monitor": m_data_2_noalias.serialize(), "value": v_data_17_name_alias.serialize()}]}})),
    (False, f"Setting {f_data_noname_242_noalias}:\n"
            f"{indentation}set {m_data_0_foo} to {v_data_3_name_noalias}\n"
            f"{indentation}{m_data_1_barbaz}: ERROR - monitor not responding\n"
            f"{indentation}set {m_data_2_noalias} to {v_data_17_name_alias}")])
def test_set_feature(json_flag, expected):
    responses = [
        info.MonitorSetResponseData(mon=m_data_0_foo, error=None, value=v_data_3_name_noalias),
        info.MonitorSetResponseData(mon=m_data_1_barbaz, error=Exception("monitor not responding"), value=None),
        info.MonitorSetResponseData(mon=m_data_2_noalias, error=None, value=v_data_17_name_alias)
    ]
    assert output.set_feature_output(f_data_noname_242_noalias, responses, json_flag) == expected


@pytest.mark.parametrize("json_flag,expected", [
    (True, json.dumps({"toggle": {"feature": f_data_noname_242_noalias.serialize(), "responses": [
                        {"monitor": m_data_0_foo.serialize(), "original_value": v_data_3_name_noalias.serialize(), "new_value": v_data_17_name_alias.serialize()},
                        {"monitor": m_data_1_barbaz.serialize(), "error": "failed to read current value"},
                        {"monitor": m_data_2_noalias.serialize(), "original_value": v_data_2_noname_alias.serialize(), "new_value": v_data_1_noname_noalias.serialize()}]}})),
    (False, f"Toggling {f_data_noname_242_noalias}:\n"
            f"{indentation}toggled {m_data_0_foo} from {v_data_3_name_noalias} to {v_data_17_name_alias}\n"
            f"{indentation}{m_data_1_barbaz}: ERROR - failed to read current value\n"
            f"{indentation}toggled {m_data_2_noalias} from {v_data_2_noname_alias} to {v_data_1_noname_noalias}")
])
def test_tog_feature(json_flag, expected):
    responses = [
        info.MonitorToggleResponseData(mon=m_data_0_foo, error=None, original_value=v_data_3_name_noalias, new_value=v_data_17_name_alias),
        info.MonitorToggleResponseData(mon=m_data_1_barbaz, error=Exception("failed to read current value"), original_value=None, new_value=None),
        info.MonitorToggleResponseData(mon=m_data_2_noalias, error=None, original_value=v_data_2_noname_alias, new_value=v_data_1_noname_noalias)
    ]
    assert output.tog_feature_output(f_data_noname_242_noalias, responses, json_flag) == expected


@pytest.mark.parametrize("json_flag,expected", [
    (True, json.dumps({"caps": [
                {"monitor": m_data_0_foo.serialize(), "data": "foo"},
                {"monitor": m_data_1_barbaz.serialize(), "error": "could not retrieve capabilities"},
                {"monitor": m_data_2_noalias.serialize(), "data": "bar"}],
            "type": "raw"})),
    (False, f"Capabilities:\n{indentation}Capability string for {m_data_0_foo}:\n{textwrap.indent(textwrap.indent('foo', indentation), indentation)}\n{indentation}{m_data_1_barbaz}: ERROR - could not retrieve capabilities\n{indentation}Capability string for {m_data_2_noalias}:\n{textwrap.indent(textwrap.indent('bar', indentation), indentation)}")
])
def test_caps_raw(json_flag, expected):
    responses = [
        info.MonitorCapsResponseData(mon=m_data_0_foo, error=None, data="foo"),
        info.MonitorCapsResponseData(mon=m_data_1_barbaz, error=Exception("could not retrieve capabilities"), data=None),
        info.MonitorCapsResponseData(mon=m_data_2_noalias, error=None, data="bar")
    ]
    assert output.caps_raw_output(responses, json_flag) == expected

caps_data_0 = info.CapabilityData(caps_attrs, caps_cmds_multi, caps_vcps_single, caps_errata_both)
caps_data_1 = info.CapabilityData(caps_attrs, caps_cmds_single, caps_vcps_multi, frozendict())


@pytest.mark.parametrize("json_flag,expected", [
    (True, json.dumps({"caps": [
                {"monitor": m_data_0_foo.serialize(), "data": caps_data_0.serialize()},
                {"monitor": m_data_1_barbaz.serialize(), "error": "ddc communication failed"},
                {"monitor": m_data_2_noalias.serialize(), "data": caps_data_1.serialize()}],
            "type": "parsed"})),
    (False, "Capabilities:\n" + textwrap.indent(f"{m_data_0_foo}:\n{textwrap.indent(str(caps_data_0), indentation)}", indentation) + f"\n{indentation}{m_data_1_barbaz}: ERROR - ddc communication failed\n" + textwrap.indent(f"{m_data_2_noalias}:\n{textwrap.indent(str(caps_data_1), indentation)}", indentation))
])
def test_caps_parsed(json_flag, expected):
    responses = [
        info.MonitorCapsResponseData(mon=m_data_0_foo, error=None, data=caps_data_0),
        info.MonitorCapsResponseData(mon=m_data_1_barbaz, error=Exception("ddc communication failed"), data=None),
        info.MonitorCapsResponseData(mon=m_data_2_noalias, error=None, data=caps_data_1)
    ]
    assert output.caps_parsed_output(responses, json_flag) == expected
