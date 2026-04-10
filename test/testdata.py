from frozendict import frozendict

from monitorboss import info
from pyddc.vcp_codes import VCPCodes
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

# CapabilityData models
caps_attrs = frozendict({"model": "DUMMY", "foo": "bar", "baz": "qux", "type": "LCD"})
caps_cmds_single = frozendict({"cmds_0": (f_data_noname_242_noalias, f_data_noname_243_alias, f_data_inputsource_96_alias)})
caps_cmds_multi = frozendict({"cmds_0": (f_data_noname_242_noalias, f_data_noname_243_alias, f_data_inputsource_96_alias), "cmds_1": (f_data_noname_242_noalias, f_data_noname_243_alias, f_data_imageorientation_170_noalias)})
caps_vcps_single =  frozendict({"vcp_0": frozendict({f_data_noname_242_noalias: (v_data_1_noname_noalias, v_data_2_noname_alias), f_data_noname_243_alias: (v_data_1_noname_noalias, v_data_2_noname_alias), f_data_inputsource_96_alias: (v_data_3_name_noalias,)})})
caps_vcps_multi = frozendict({"vcp_0": frozendict({f_data_noname_242_noalias: (v_data_1_noname_noalias, v_data_2_noname_alias), f_data_noname_243_alias: (v_data_1_noname_noalias, v_data_2_noname_alias), f_data_inputsource_96_alias: (v_data_3_name_noalias,)}),
                            "vcp_1": frozendict({f_data_noname_242_noalias: (v_data_1_noname_noalias, v_data_2_noname_alias), f_data_noname_243_alias: (v_data_1_noname_noalias, v_data_2_noname_alias), f_data_imageorientation_170_noalias: (v_data_17_name_alias,)})})
caps_errata_unnamed = frozendict({"": ("foo", "bar")})
caps_errata_named = frozendict({"baz": ("qux", "corge")})
caps_errata_both = frozendict({"": ("foo", "bar"), "baz": ("qux", "corge")})

# VCP commands
input_command = get_vcp_com(VCPCodes.input_source)
lum_command = get_vcp_com(VCPCodes.image_luminance)
reset_command = get_vcp_com(VCPCodes.restore_factory_default)
active_control = get_vcp_com(VCPCodes.active_control)

# Templates
lum_template = SupportedCodeTemplate(VCPCodes.image_luminance.value, None, 75, 80)
source_template = SupportedCodeTemplate(VCPCodes.input_source.value, [15, 17, 257], 257, None)

edid_blob = b'\x00\xff\xff\xff\xff\xff\xff\x00\x34\x53\x23\x4f\x65\x65\xfc\x03' \
           b'\x01\x22\x01\x04\xa2\x30\x1b\x78\xf7\xee\x91\xa3\x54\x4c\x99\x26' \
           b'\x0f\x50\x54\x25\x4a\x00\x81\xc0\x81\x80\x95\x00\xb3\x00\x01\x01' \
           b'\x01\x01\x01\x01\x01\x01\x02\x3a\x80\x18\x71\x38\x2d\x40\x58\x2c' \
           b'\x45\x00\xe0\x0e\x11\x00\x00\x1e\x00\x00\x00\xfd\x00\x30\x3e\x1e' \
           b'\x53\x11\x02\x00\x00\x0f\x0a\x00\x00\x00\x00\x00\x00\xfc\x00\x44' \
           b'\x45\x4c\x4c\x20\x50\x32\x34\x31\x39\x48\x0a\x20\x00\x00\x00\x10' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01' \
           b'\xd3\x02\x03\x13\x70\x47\x01\x02\x03\x04\x05\x10\x1f\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' \
           b'\x00\x00\x00\x00\x00\x00\x00\xf3'

vcp_template = VCPTemplate(supported_codes = [lum_template, source_template],
                           caps_str = "(prot(monitor)type(LCD)model(DUMM13)cmds(04)vcp(10 60(01 0F 11 ) )mccs_ver(2.1))",
                           edid_blob = edid_blob,
                           faulty = False)

