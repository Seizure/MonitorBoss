import pytest
pytest_plugins = "pytester"
import io
from contextlib import redirect_stdout, redirect_stderr

import tomlkit

from .vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config
from monitorboss.cli import run

TEST_TOML_CONTENTS = """
[monitor_names]
main = 0
foo = 1
bar = 2

[input_names]
usbc = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[settings]
wait = 0.0""".strip()


class TestConfig:

    def test_auto_create_config(self, pytester):
        confpath = pytester.path.joinpath("test_config.toml")
        config.get_config(confpath.as_posix())
        assert confpath.exists()

    def test_config_reset(self, pytester):
        conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
        contents: str

        with open(conf, "r", encoding="utf8") as file:
            contents = file.read().strip()
        assert contents == TEST_TOML_CONTENTS

        config.reset_config(conf.as_posix())
        with open(conf, "r", encoding="utf8") as file:
            contents = file.read().strip()
        assert contents == tomlkit.dumps(config.default_toml()).strip()

    # TODO: should probably eventually test more of the config functions,
    #   but we're currently not even using them and they might change, so not bothering yet



class TestCLIGet:
    """
    Factors which will affect output:
    - Whether the monitor was supplied as an ID or alias
    - Whether the attribute is continuous or discreet
    - Whether the returned value has a matching value in the code's param_names
    - Whether the returned value has a matching value in the config file's aliases

    Total of 16 tests to cover all combinations
    """
    def test_get_discreet_by_alias(self, capsys, pytester):
        conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
        run(f"--config {conf.as_posix()} get src foo")
        assert capsys.readouterr().out == "src for monitor foo is 27 (usbc)\n"
        assert capsys.readouterr().err == ""

    def test_get_discreet_by_id(self, capsys, pytester):
        conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
        run(f"--config {conf.as_posix()} get src 1")
        assert capsys.readouterr().out == "src for monitor #1 is 27 (usbc)\n"
        assert capsys.readouterr().err == ""
