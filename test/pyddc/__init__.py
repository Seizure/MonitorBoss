from __future__ import annotations

TEST_TOML_CONTENTS = """
[monitor_names]
0 = "foo"
1 = ["bar", "baz"]
# 2 has no alias

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
