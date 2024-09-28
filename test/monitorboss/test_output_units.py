import json
import sys

import pytest

from frozendict import frozendict

from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import indentation, info, output


mdata = info.MonitorData(42, ())
mdatajson = json.dumps(mdata.serialize())
feature1 = info.FeatureData("", 42, ())
feature1json = json.dumps(feature1.serialize())
feature2 = info.FeatureData("", 84, ())
feature2json = json.dumps(feature2.serialize())
feature3 = info.FeatureData("", VCPCodes.input_source.value, ())
feature3json = json.dumps(feature3.serialize())
feature4 = info.FeatureData("", VCPCodes.image_color_preset.value, ())
feature4json = json.dumps(feature4.serialize())
value1 = info.ValueData(12, "", ())
value1json = json.dumps(value1.serialize())
value2 = info.ValueData(34, "", ())
value2json = json.dumps(value2.serialize())
value3 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
value3json = json.dumps(value3.serialize())
value4 = info.ValueData(ColorPresetNames.ct5000k.value, "", ())
value4json = json.dumps(value4.serialize())
attributes = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
cmds = frozendict({"cmds_0": (feature1, feature2, feature3), "cmds_1": (feature1, feature2, feature4)})
vcps = frozendict({"vcp_0": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature3: (value3,)}),
                   "vcp_1": frozendict({feature1: (value1, value2), feature2: (value1, value2), feature4: (value4,)})})
errata = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})
data = info.CapabilityData(attributes, cmds, vcps, errata)


def test_caps_raw_json():
    assert output.caps_raw_output(mdata, "foo", True) == '{"caps": {"type": "raw", "monitor": ' + mdatajson + ', "data": "foo"}}'


def test_caps_raw_human():
    assert output.caps_raw_output(mdata, "foo", False) == f"Capability string for {mdata}:\nfoo"


def test_caps_full_json():
    pass
    

def test_extract_caps_summary_data():
    expected = ({'model': 'CAF3', 'type': 'LCD'}, {'vcp_0': {feature3: (value3,)}, 'vcp_1': {feature4: (value4,)}})

    assert output.extract_caps_summary_data(data) == expected


def test_caps_summary_json():
    expected = '{"caps": {"type": "summary", "monitor": ' + mdatajson + ', "data": {"model": "CAF3", "type": "LCD", "vcps": {"vcp_0": [{"feature": ' + feature3json + ', "params": [' + value3json + ']}], "vcp_1": [{"feature": ' + feature4json + ', "params": [' + value4json + ']}]}}}}'

    assert output.caps_summary_output(mdata, data, True) == expected

def test_caps_summary_human():
    expected = f'{mdata} - model: CAF3, type: LCD\nvcp_0:\n{indentation}* {feature3}: {value3}\nvcp_1:\n{indentation}* {feature4}: {value4}\n'

    assert output.caps_summary_output(mdata, data, False) == expected
