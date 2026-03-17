# Test data constants for MonitorBoss tests

from frozendict import frozendict

from monitorboss import info
from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from pyddc import get_vcp_com
from test.pyddc.vcp_dummy import VCPTemplate, SupportedCodeTemplate

TEST_TOML_CONTENTS = """
[monitor_names]
0 = "foo" # monitor with single aliase
1 = ["bar", "baz"] # monitor with multiple aliases
# monitor 2 has no aliases 

[feature_aliases]
16 = ['lum', 'luminance', 'brightness']
18 = ['cnt', 'contrast']
20 = ['clr', 'color', 'clrpreset']
96 = ['src', 'source', 'input']
214 = ['pwr', 'power', 'powermode']

[value_aliases.input_source]
27 = ["usbc", "usb-c"] # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers
17 = "hdmi"

[value_aliases.image_luminance]
25 = "night"
75 = ["day", "bright"]

[settings]
wait_get = 0
wait_set = 0
wait_internal = 0""".strip()

# MonitorData models
m_data_0_foo = info.MonitorData(0, ("foo",)) # monitor with single alias
m_data_1_barbaz = info.MonitorData(1, ("bar", "baz")) # monitor with multiple aliases
m_data_2_noalias = info.MonitorData(2, ()) # monitor with no aliases

# FeatureData models
f_data_noname_242_noalias = info.FeatureData("", 242, ()) # feature with no name or alias
f_data_noname_243_alias = info.FeatureData("", 243, ("custom", "custom_feature")) # feature with no name, but aliases # TODO when we add capability to add custom features, this should be reflected in the TOML
f_data_imageorientation_170_noalias = info.FeatureData("image_orientation", 170, ()) # feature with name, but no aliases
f_data_inputsource_96_alias = info.FeatureData("input_source", 96, ("src", "source", "input")) # feature with name and aliases

# ValueData models
v_data_1_noname_noalias = info.ValueData(1, "", ()) # value with no name or alias
v_data_2_noname_alias = info.ValueData(2, "", ("cus", "tom")) # value with no name, but multiple aliases
v_data_3_name_noalias = info.ValueData(3, "ct4000k", ()) # value with name, but no aliases (image_color_preset)
v_data_17_name_alias = info.ValueData(17, "hdmi1", ("hdmi",)) # value with name and single alias (input_source)


value_data_12 = info.ValueData(12, "", ())
value_data_34 = info.ValueData(34, "", ())
value_data_hdmi2 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
value_data_ct5000k = info.ValueData(ColorPresetNames.ct5000k.value, "", ())

# ValueData instances with params and aliases
value_data_24_noname_noalias = info.ValueData(24, "", ())
value_data_24_foo_noalias = info.ValueData(24, "foo", ())
value_data_24_noname_alias = info.ValueData(24, "", ('foo', 'bar'))
value_data_24_foo_alias = info.ValueData(24, "foo", ("bar", "baz"))

# Complex structures for CapabilityData
attributes_full = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
attributes_summary = frozendict({"model": "CAF3", "type": "LCD"})
cmds_full = frozendict({"cmds_0": (f_data_noname_242_noalias, f_data_noname_243_alias, f_data_inputsource_96_alias), "cmds_1": (f_data_noname_242_noalias, f_data_noname_243_alias, f_data_imageorientation_170_noalias)})
vcps_full = frozendict({"vcp_0": frozendict({f_data_noname_242_noalias: (value_data_12, value_data_34), f_data_noname_243_alias: (value_data_12, value_data_34), f_data_inputsource_96_alias: (value_data_hdmi2,)}),
                       "vcp_1": frozendict({f_data_noname_242_noalias: (value_data_12, value_data_34), f_data_noname_243_alias: (value_data_12, value_data_34), f_data_imageorientation_170_noalias: (value_data_ct5000k,)})})
vcps_summary = frozendict({"vcp_0": frozendict({f_data_inputsource_96_alias: (value_data_hdmi2,)}), "vcp_1": frozendict({f_data_imageorientation_170_noalias: (value_data_ct5000k,)})})
errata_full = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})

capability_data_full = info.CapabilityData(attributes_full, cmds_full, vcps_full, errata_full)
capability_data_summary = info.CapabilityData(attributes_summary, frozendict(), vcps_summary, frozendict())

# VCP commands
input_command = get_vcp_com(VCPCodes.input_source)
lum_command = get_vcp_com(VCPCodes.image_luminance)
reset_command = get_vcp_com(VCPCodes.restore_factory_default)
active_control = get_vcp_com(VCPCodes.active_control)

# Templates
lum_template = SupportedCodeTemplate(VCPCodes.image_luminance.value, None, 75, 80)
source_template = SupportedCodeTemplate(VCPCodes.input_source.value, [15, 17, 257], 257, None)

vcp_template = VCPTemplate([lum_template, source_template],
                           "(prot(monitor)type(LCD)model(DUMM13)cmds(04)vcp(10 60(01 0F 11 ) )mccs_ver(2.1))",
                           False)

