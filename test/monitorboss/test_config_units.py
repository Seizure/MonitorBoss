import tomlkit

from monitorboss import config


# TODO: test reading, parsing, and validating of config

def test_config_auto_create(pytester):
    confpath = pytester.path.joinpath("test_config.toml")
    config.get_config(confpath.as_posix())
    assert confpath.exists()
    with open(confpath, "r", encoding="utf8") as file:
        contents = file.read()
    assert contents == tomlkit.dumps(config.default_toml())


def test_config_reset(pytester):
    conf = pytester.makefile(".toml", test_toml="trash")

    # sanity checking
    with open(conf, "r", encoding="utf8") as file:
        contents = file.read()
    assert contents == "trash"

    config.reset_config(conf.as_posix())
    with open(conf, "r", encoding="utf8") as file:
        contents = file.read()
    assert contents == tomlkit.dumps(config.default_toml())

# TODO: should probably eventually test more of the config functions,
#   but we're currently not even using them and they might change, so not bothering yet
