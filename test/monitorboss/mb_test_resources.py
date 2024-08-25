from monitorboss import config
from tomlkit import dumps

doc = config.default_toml()

TEST_TOML_CONTENTS = dumps(doc)


# feature_set = [get_vcp, {"name": "cnt", "discrete": False, "match_param": False}]  # discrete vs continous code; also matching param_name vs not
# TODO: will need to change/add to this when we support all codes, and command by int/name
# monitor_set = ["foo", "2", "bar"]  # alias vs id for monitor; also testing 1 to 3 monitors
# match_param = [True, False]  # whether there is a matching value in the code's param_names
# match_alias = ["none", "single", "multi"]  # whether the returned value has matching values in the config file's aliases

# 48 perms

