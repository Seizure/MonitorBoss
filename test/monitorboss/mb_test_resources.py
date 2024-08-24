TEST_TOML_CONTENTS = """
[monitor_names]
main = 0
foo = 1
bar = 2

[input_names]
usbc = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[settings]
wait = 0.0""".strip()

feature_set = ["src", "cnt"] # discreet vs continous code
# TODO: will need to change/add to this when we support all codes, and command by int/name
monitor_set = ["foo 1"] # test for both monitor alias and ID at the same time