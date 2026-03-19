import json
import textwrap

import pytest

from frozendict import frozendict

from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import indentation, output
from ..testdata import *


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"list": [{"monitor": m_data_0_foo.serialize()}, {"monitor": m_data_1_barbaz.serialize()}]})),
    (False, f"{m_data_0_foo}\n{m_data_1_barbaz}")
])
def test_list_mons(json_flag, expected):
    assert output.list_mons_output([m_data_0_foo, m_data_1_barbaz], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"get": {"feature": f_data_noname_242_noalias.serialize(),
                               "values": [{"monitor": m_data_0_foo.serialize(), "value": v_data_17_name_alias.serialize()},
                                          {"monitor": m_data_1_barbaz.serialize(), "value": v_data_3_name_noalias.serialize(), "max_value": 100}]}})),
    (False, f"{f_data_noname_242_noalias} for {m_data_0_foo} is {v_data_17_name_alias}\n{f_data_noname_242_noalias} for {m_data_1_barbaz} is {v_data_3_name_noalias} (Maximum: 100)")
])
def test_get_feature(json_flag, expected):
    assert output.get_feature_output(f_data_noname_242_noalias, [(m_data_0_foo, v_data_17_name_alias, None), (m_data_1_barbaz, v_data_3_name_noalias, 100)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"set": {"feature": f_data_noname_242_noalias.serialize(),
                               "values": [{"monitor": m_data_0_foo.serialize(), "value": v_data_3_name_noalias.serialize()},
                                          {"monitor": m_data_1_barbaz.serialize(), "value": v_data_17_name_alias.serialize()}]}})),
    (False, f"set {f_data_noname_242_noalias} for {m_data_0_foo} to {v_data_3_name_noalias}\nset {f_data_noname_242_noalias} for {m_data_1_barbaz} to {v_data_17_name_alias}")
])
def test_set_feature(json_flag, expected):
    assert output.set_feature_output(f_data_noname_242_noalias, [(m_data_0_foo, v_data_3_name_noalias), (m_data_1_barbaz, v_data_17_name_alias)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"toggle": {"feature": f_data_noname_242_noalias.serialize(), "values": [
        {"monitor": m_data_0_foo.serialize(), "original_value": v_data_3_name_noalias.serialize(), "new_value": v_data_17_name_alias.serialize()},
        {"monitor": m_data_1_barbaz.serialize(), "original_value": v_data_2_noname_alias.serialize(), "new_value": v_data_1_noname_noalias.serialize()}
    ]}})),
    (False, f"toggled {f_data_noname_242_noalias} for {m_data_0_foo} from {v_data_3_name_noalias} to {v_data_17_name_alias}\ntoggled {f_data_noname_242_noalias} for {m_data_1_barbaz} from {v_data_2_noname_alias} to {v_data_1_noname_noalias}")
])
def test_tog_feature(json_flag, expected):
    assert output.tog_feature_output(f_data_noname_242_noalias, [(m_data_0_foo, v_data_3_name_noalias, v_data_17_name_alias), (m_data_1_barbaz, v_data_2_noname_alias, v_data_1_noname_noalias)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"caps": [
                {"monitor": m_data_0_foo.serialize(), "data": "foo"},
                {"monitor": m_data_1_barbaz.serialize(), "data": "bar"}],
            "type": "raw"})),
    (False, f"Capability string for {m_data_0_foo}:\n{indentation}foo\nCapability string for {m_data_1_barbaz}:\n{indentation}bar")
])
def test_caps_raw(json_flag, expected):
    assert output.caps_raw_output([(m_data_0_foo, "foo"), (m_data_1_barbaz, "bar")], json_flag) == expected

caps_data_0 = info.CapabilityData(caps_attrs, caps_cmds_multi, caps_vcps_single, caps_errata_both)
caps_data_1 = info.CapabilityData(caps_attrs, caps_cmds_single, caps_vcps_multi, frozendict())

@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"caps": [
                {"monitor": m_data_0_foo.serialize(), "data": caps_data_0.serialize()},
                {"monitor": m_data_1_barbaz.serialize(), "data": caps_data_1.serialize()}],
            "type": "full"})),
    (False, f"{m_data_0_foo}:\n{textwrap.indent(str(caps_data_0), indentation)}\n{m_data_1_barbaz}:\n{textwrap.indent(str(caps_data_1), indentation)}")
])
def test_caps_parsed(json_flag, expected):
    assert output.caps_parsed_output([(m_data_0_foo, caps_data_0), (m_data_1_barbaz, caps_data_1)], json_flag) == expected
