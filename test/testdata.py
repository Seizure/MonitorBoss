# Test data constants for MonitorBoss tests

from frozendict import frozendict

from monitorboss import info
from pyddc.vcp_codes import VCPCodes, InputSourceNames, ColorPresetNames
from pyddc import get_vcp_com
from test.pyddc.vcp_dummy import VCPTemplate, SupportedCodeTemplate

# MonitorData instances
m_data_0_foo = info.MonitorData(0, ("foo",))
m_data_1_barbaz = info.MonitorData(1, ("bar", "baz"))
m_data_2_noalias = info.MonitorData(2, ())

# FeatureData instances
f_data_noname_42_noalias = info.FeatureData("", 42, ())
f_data_noname_84_noalias = info.FeatureData("", 84, ())
feature_data_input_source = info.FeatureData("", VCPCodes.input_source.value, ())
feature_data_color_preset = info.FeatureData("", VCPCodes.image_color_preset.value, ())

# ValueData instances
value_data_12 = info.ValueData(12, "", ())
value_data_24 = info.ValueData(24, "", ())
value_data_34 = info.ValueData(34, "", ())
value_data_75 = info.ValueData(75, "", ())
value_data_hdmi2 = info.ValueData(InputSourceNames.hdmi2.value, "", ())
value_data_ct5000k = info.ValueData(ColorPresetNames.ct5000k.value, "", ())

# ValueData instances with params and aliases
value_data_24_empty = info.ValueData(24, "", ())
value_data_24_foo = info.ValueData(24, "foo", ())
value_data_24_aliases = info.ValueData(24, "", ('foo', 'bar'))
value_data_24_full = info.ValueData(24, "foo", ("bar", "baz"))

# Complex structures for CapabilityData
attributes_full = frozendict({"model": "CAF3", "foo": "bar", "baz": "qux", "type": "LCD"})
attributes_summary = frozendict({"model": "CAF3", "type": "LCD"})
cmds_full = frozendict({"cmds_0": (f_data_noname_42_noalias, f_data_noname_84_noalias, feature_data_input_source), "cmds_1": (f_data_noname_42_noalias, f_data_noname_84_noalias, feature_data_color_preset)})
vcps_full = frozendict({"vcp_0": frozendict({f_data_noname_42_noalias: (value_data_12, value_data_34), f_data_noname_84_noalias: (value_data_12, value_data_34), feature_data_input_source: (value_data_hdmi2,)}),
                       "vcp_1": frozendict({f_data_noname_42_noalias: (value_data_12, value_data_34), f_data_noname_84_noalias: (value_data_12, value_data_34), feature_data_color_preset: (value_data_ct5000k,)})})
vcps_summary = frozendict({"vcp_0": frozendict({feature_data_input_source: (value_data_hdmi2,)}), "vcp_1": frozendict({feature_data_color_preset: (value_data_ct5000k,)})})
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
