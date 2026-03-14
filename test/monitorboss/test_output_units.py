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


mdata0 = info.MonitorData(42, ())
mdata0json = json.dumps(mdata0.serialize())
mdata1 = info.MonitorData(43, ())
mdata1json = json.dumps(mdata1.serialize())
feature1 = info.FeatureData("", 42, ())
feature1json = json.dumps(feature1.serialize())
feature2 = info.FeatureData("", 84, ())
feature2json = json.dumps(feature2.serialize())
feature3 = info.FeatureData("", VCPCodes.input_source.value, ())
feature3json = json.dumps(feature3.serialize())
feature4 = info.FeatureData("", VCPCodes.image_color_preset.value, ())
feature4json = json.dumps(feature4.serialize())
value0 = info.ValueData(12, "", ())
value0json = json.dumps(value0.serialize())
value1 = info.ValueData(34, "", ())
value1json = json.dumps(value1.serialize())
value2 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
value2json = json.dumps(value2.serialize())
value3 = info.ValueData(ColorPresetNames.ct5000k.value, "", ())
value3json = json.dumps(value3.serialize())
attributes = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
attributes_summary = frozendict({"model": "CAF3", "type": "LCD"})
cmds = frozendict({"cmds_0": (feature1, feature2, feature3), "cmds_1": (feature1, feature2, feature4)})
vcps = frozendict({"vcp_0": frozendict({feature1: (value0, value1), feature2: (value0, value1), feature3: (value2,)}),
                   "vcp_1": frozendict({feature1: (value0, value1), feature2: (value0, value1), feature4: (value3,)})})
vcps_summary = frozendict({"vcp_0": frozendict({feature3: (value2,)}), "vcp_1": frozendict({feature4: (value3,)})})
errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
caps = info.CapabilityData(attributes, cmds, vcps, errata)
caps_summary = info.CapabilityData(attributes_summary, frozendict(), vcps_summary, frozendict())


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"list": [{"monitor": mdata0.serialize()}, {"monitor": mdata1.serialize()}]})),
    (False, f"{mdata0}\n{mdata1}")
])
def test_list_mons(json_flag, expected):
    assert output.list_mons_output([mdata0, mdata1], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"get": {"feature": feature1.serialize(),
                               "values": [{"monitor": mdata0.serialize(), "value": value0.serialize()},
                                          {"monitor": mdata1.serialize(), "value": value1.serialize(), "max_value": 100}]}})),
    (False, f"{feature1} for {mdata0} is {value0}\n{feature1} for {mdata1} is {value1} (Maximum: 100)")
])
def test_get_feature(json_flag, expected):
    assert output.get_feature_output(feature1, [(mdata0, value0, None), (mdata1, value1, 100)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"set": {"feature": feature1.serialize(),
                               "values": [{"monitor": mdata0.serialize(), "value": value0.serialize()},
                                          {"monitor": mdata1.serialize(), "value": value1.serialize()}]}})),
    (False, f"set {feature1} for {mdata0} to {value0}\nset {feature1} for {mdata1} to {value1}")
])
def test_set_feature(json_flag, expected):
    assert output.set_feature_output(feature1, [(mdata0, value0), (mdata1, value1)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"toggle": {"feature": feature1.serialize(), "values": [
        {"monitor": mdata0.serialize(), "original_value": value0.serialize(), "new_value": value1.serialize()},
        {"monitor": mdata1.serialize(), "original_value": value2.serialize(), "new_value": value3.serialize()}
    ]}})),
    (False, f"toggled {feature1} for {mdata0} from {value0} to {value1}\ntoggled {feature1} for {mdata1} from {value2} to {value3}")
])
def test_tog_feature(json_flag, expected):
    assert output.tog_feature_output(feature1, [(mdata0, value0, value1), (mdata1, value2, value3)], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"caps": [
                {"monitor": mdata0.serialize(), "data": "foo"},
                {"monitor": mdata1.serialize(), "data": "bar"}],
            "type": "raw"})),
    (False, f"Capability string for {mdata0}:\n{indentation}foo\nCapability string for {mdata1}:\n{indentation}bar")
])
def test_caps_raw(json_flag, expected):
    assert output.caps_raw_output([(mdata0, "foo"), (mdata1, "bar")], json_flag) == expected


@pytest.mark.parametrize("json_flag, expected", [
    (True, json.dumps({"caps": [
                {"monitor": mdata0.serialize(), "data": caps.serialize()},
                {"monitor": mdata1.serialize(), "data": caps.serialize()}],
            "type": "full"})),
    (False, f"{mdata0}:\n{textwrap.indent(str(caps), indentation)}\n{mdata1}:\n{textwrap.indent(str(caps), indentation)}")
])
def test_caps_parsed(json_flag, expected):
    assert output.caps_parsed_output([(mdata0, caps), (mdata1, caps)], json_flag) == expected


def test_extract_caps_summary_data():
    assert monitorboss.info.capability_summary_data(caps) == caps_summary
