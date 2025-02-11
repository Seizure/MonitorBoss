import json
import textwrap

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

# Potential argument perms for _get_feature are:
#     - None, None, None, err
#     - mon, cur, None, None
#     - mon, cur, max, None
#     - mon, None, None, err
get_monvalues = [(None, None, None, Exception("Dummy exception")),
                 (mdata0, value0, None, None),
                 (mdata1, value1, 100, None),
                 (mdata0, None, None, Exception("Dummy exception"))]

# Potential argument perms for _set_feature are:
#     - None, None, err
#     - mon, new, None
#     - mon, None, err
set_monvalues = [(None, None, Exception("Dummy exception")),
                 (mdata0, value0, None),
                 (mdata1, None, Exception("Dummy exception"))]

# Potential argument perms for _tog_feature are:
#     - None, None, None, err
#     - mon, original, new, None
#     - mon, None, None, err
tog_monvalues = [(None, None, None, Exception("Dummy exception")),
                 (mdata0, value0, value1, None),
                 (mdata1, None, None, Exception("Dummy exception"))]

def test_list_mons_json():
    expected = json.dumps({"list": [{"monitor": mdata0.serialize()}, {"monitor": mdata1.serialize()}]})
    assert output.list_mons_output([mdata0, mdata1], True) == expected


def test_list_mons_human():
    expected = f"{mdata0}\n{mdata1}"
    assert output.list_mons_output([mdata0, mdata1], False) == expected


def test_get_feature_json():
    expected = json.dumps({"get": {"feature": feature1.serialize(),
                                   "values": [{"error": "Dummy exception"},
                                              {"monitor": mdata0.serialize(), "value": value0.serialize()},
                                              {"monitor": mdata1.serialize(), "value": value1.serialize(), "max_value": 100},
                                              {"monitor": mdata0.serialize(), "error": "Dummy exception"}]}})
    assert output.get_feature_output(feature1, get_monvalues, True) == expected


def test_get_feature_human():
    expected = f"{feature1} for {mdata0} is {value0}\n{feature1} for {mdata0} is ERROR: Dummy exception\n{feature1} for {mdata1} is {value1} (Maximum: 100)"
    assert output.get_feature_output(feature1, get_monvalues, False) == expected



def test_set_feature_json():
    expected = json.dumps({"set": {"feature": feature1.serialize(),
                                   "values": [{"error": "Dummy exception"},
                                              {"monitor": mdata0.serialize(), "value": value0.serialize()},
                                              {"monitor": mdata1.serialize(), "error": "Dummy exception"}]}})
    assert output.set_feature_output(feature1, set_monvalues, True) == expected


def test_set_feature_human():
    expected = f"set {feature1} for {mdata0} to {value0}\nset {feature1} for {mdata0} to ERROR: Dummy exception\nset {feature1} for {mdata1} to {value1}"
    assert output.set_feature_output(feature1, set_monvalues, False) == expected


def test_tog_feature_json():
    expected = json.dumps({"toggle": {"feature": feature1.serialize(),
                                      "values": [{"error": "Dummy exception"},
                                                 {"monitor": mdata0.serialize(), "original_value": value0.serialize(), "new_value": value1.serialize()},
                                                 {"monitor": mdata1.serialize(), "error": "Dummy exception"}]}})
    assert output.tog_feature_output(feature1, tog_monvalues, True) == expected


def test_tog_feature_human():
    expected = f"toggled {feature1} for {mdata0} from {value0} to {value1}\ntoggled {feature1} for {mdata1} from {value2} to {value3}"
    assert output.tog_feature_output(feature1, tog_monvalues, False) == expected


def test_caps_raw_json():
    expected = json.dumps({"caps": [
                {"monitor": mdata0.serialize(), "data": "foo"},
                {"monitor": mdata1.serialize(), "data": "bar"}],
            "type": "raw"})
    assert output.caps_raw_output([(mdata0, "foo"), (mdata1, "bar")], True) == expected


def test_caps_raw_human():
    expected = f"Capability string for {mdata0}:\n{indentation}foo\nCapability string for {mdata1}:\n{indentation}bar"
    assert output.caps_raw_output([(mdata0, "foo"), (mdata1, "bar")], False) == expected


def test_caps_parsed_json():
    expected = json.dumps({"caps": [
                {"monitor": mdata0.serialize(), "data": caps.serialize()},
                {"monitor": mdata1.serialize(), "data": caps.serialize()}],
            "type": "full"})
    assert output.caps_parsed_output([(mdata0, caps), (mdata1, caps)], True) == expected


def test_caps_parsed_human():
    expected = f"{mdata0}:\n{textwrap.indent(str(caps), indentation)}\n{mdata1}:\n{textwrap.indent(str(caps), indentation)}"
    assert output.caps_parsed_output([(mdata0, caps), (mdata1, caps)], False) == expected


def test_extract_caps_summary_data():
    assert monitorboss.info.capability_summary_data(caps) == caps_summary
