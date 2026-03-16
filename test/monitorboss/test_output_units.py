import json
import textwrap

import pytest

from frozendict import frozendict

import monitorboss.info
from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import indentation, info, output
from ..testdata import *


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"list": [{"monitor": m_data_0_foo.serialize()}, {"monitor": m_data_1_barbaz.serialize()}]})),
    (False, f"{m_data_0_foo}\n{m_data_1_barbaz}")
])
def test_list_mons(json_flag, expected):
    assert output.list_mons_output([m_data_0_foo, m_data_1_barbaz], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"get": {"feature": f_data_noname_242_noalias.serialize(),
                               "values": [{"monitor": m_data_0_foo.serialize(), "value": value_data_12.serialize()},
                                          {"monitor": m_data_1_barbaz.serialize(), "value": value_data_34.serialize(), "max_value": 100}]}})),
    (False, f"{f_data_noname_242_noalias} for {m_data_0_foo} is {value_data_12}\n{f_data_noname_242_noalias} for {m_data_1_barbaz} is {value_data_34} (Maximum: 100)")
])
def test_get_feature(json_flag, expected):
    assert output.get_feature_output(f_data_noname_242_noalias, [(m_data_0_foo, value_data_12, None), (m_data_1_barbaz, value_data_34, 100)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"set": {"feature": f_data_noname_242_noalias.serialize(),
                               "values": [{"monitor": m_data_0_foo.serialize(), "value": value_data_12.serialize()},
                                          {"monitor": m_data_1_barbaz.serialize(), "value": value_data_34.serialize()}]}})),
    (False, f"set {f_data_noname_242_noalias} for {m_data_0_foo} to {value_data_12}\nset {f_data_noname_242_noalias} for {m_data_1_barbaz} to {value_data_34}")
])
def test_set_feature(json_flag, expected):
    assert output.set_feature_output(f_data_noname_242_noalias, [(m_data_0_foo, value_data_12), (m_data_1_barbaz, value_data_34)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"toggle": {"feature": f_data_noname_242_noalias.serialize(), "values": [
        {"monitor": m_data_0_foo.serialize(), "original_value": value_data_12.serialize(), "new_value": value_data_34.serialize()},
        {"monitor": m_data_1_barbaz.serialize(), "original_value": value_data_hdmi2.serialize(), "new_value": value_data_ct5000k.serialize()}
    ]}})),
    (False, f"toggled {f_data_noname_242_noalias} for {m_data_0_foo} from {value_data_12} to {value_data_34}\ntoggled {f_data_noname_242_noalias} for {m_data_1_barbaz} from {value_data_hdmi2} to {value_data_ct5000k}")
])
def test_tog_feature(json_flag, expected):
    assert output.tog_feature_output(f_data_noname_242_noalias, [(m_data_0_foo, value_data_12, value_data_34), (m_data_1_barbaz, value_data_hdmi2, value_data_ct5000k)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"caps": [
                {"monitor": m_data_0_foo.serialize(), "data": "foo"},
                {"monitor": m_data_1_barbaz.serialize(), "data": "bar"}],
            "type": "raw"})),
    (False, f"Capability string for {m_data_0_foo}:\n{indentation}foo\nCapability string for {m_data_1_barbaz}:\n{indentation}bar")
])
def test_caps_raw(json_flag, expected):
    assert output.caps_raw_output([(m_data_0_foo, "foo"), (m_data_1_barbaz, "bar")], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"caps": [
                {"monitor": m_data_0_foo.serialize(), "data": capability_data_full.serialize()},
                {"monitor": m_data_1_barbaz.serialize(), "data": capability_data_full.serialize()}],
            "type": "full"})),
    (False, f"{m_data_0_foo}:\n{textwrap.indent(str(capability_data_full), indentation)}\n{m_data_1_barbaz}:\n{textwrap.indent(str(capability_data_full), indentation)}")
])
def test_caps_parsed(json_flag, expected):
    assert output.caps_parsed_output([(m_data_0_foo, capability_data_full), (m_data_1_barbaz, capability_data_full)], json_flag) == expected


def test_extract_caps_summary_data():
    assert monitorboss.info.capability_summary_data(capability_data_full) == capability_data_summary
