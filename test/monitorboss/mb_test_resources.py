from monitorboss import config

TEST_TOML_CONTENTS = """
[monitor_names]
0 = "foo"
1 = ["bar", "baz"]
2 = "qux"

[input_names]
27 = ["usbc", "usb_c", "usb-c"] # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[settings]
wait_get = 0
wait_set = 0
wait_internal = 0""".strip()


# feature_set = [get_vcp, {"name": "cnt", "discrete": False, "match_param": False}]  # discrete vs continous code; also matching param_name vs not
# TODO: will need to change/add to this when we support all codes, and command by int/name
# monitor_set = ["foo", "2", "bar"]  # alias vs id for monitor; also testing 1 to 3 monitors
# match_param = [True, False]  # whether there is a matching value in the code's param_names
# match_alias = ["none", "single", "multi"]  # whether the returned value has matching values in the config file's aliases

# 48 perms

