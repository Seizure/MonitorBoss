import pytest

from pyddc import get_vcp_com, VCPCommand

pytest_plugins = "pytester"

import tomlkit

from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config
from monitorboss.cli import run

import test.monitorboss.mb_test_resources as tr

INPUT_SOURCE = get_vcp_com(96)
CONTRAST = get_vcp_com(18)

class TestConfig:

    def test_auto_create_config(self, pytester):
        confpath = pytester.path.joinpath("test_config.toml")
        config.get_config(confpath.as_posix())
        assert confpath.exists()

    def test_config_reset(self, pytester):
        conf = pytester.makefile(".toml", test_toml=tr.TEST_TOML_CONTENTS)

        with open(conf, "r", encoding="utf8") as file:
            contents = file.read().strip()
        assert contents == tr.TEST_TOML_CONTENTS

        config.reset_config(conf.as_posix())
        with open(conf, "r", encoding="utf8") as file:
            contents = file.read().strip()
        assert contents == tomlkit.dumps(config.default_toml()).strip()

    # TODO: should probably eventually test more of the config functions,
    #   but we're currently not even using them and they might change, so not bothering yet



class TestCLIGet:
    """
    Factors which will affect output:
    - Whether the attribute is continuous or discreet
    - Whether the monitor was supplied as an ID or alias
        - test single vs multiple monitors
    - Whether the returned value has a matching value in the code's param_names
    - Whether the returned value has matching values in the config file's aliases
        - test single vs multiple matching values

    Total of 64 tests to cover all combinations
    """

    def test_get_discreet_by_alias(self, capsys, pytester):
        conf = pytester.makefile(".toml", test_toml=tr.TEST_TOML_CONTENTS)
        run(f"--config {conf.as_posix()} get src foo")
        assert capsys.readouterr().out == "src for monitor \"foo\" is 27 (usbc)\n"
        assert capsys.readouterr().err == ""

    def test_get_discreet_by_id(self, capsys, pytester):
        conf = pytester.makefile(".toml", test_toml=tr.TEST_TOML_CONTENTS)
        run(f"--config {conf.as_posix()} get src 1")
        assert capsys.readouterr().out == "src for monitor #1 is 27 (usbc, usb_c, usb-c)\n"
        assert capsys.readouterr().err == ""

    @pytest.mark.parametrize("feature_set", [INPUT_SOURCE, CONTRAST])
    @pytest.mark.parametrize("monitor_set", ["foo", "baz 2", "2"])
    @pytest.mark.parametrize("match_param", [True, False])
    @pytest.mark.parametrize("match_alias", ["none", "single", "multi"])
    def test_get(self, feature_set: VCPCommand, monitor_set: str, match_param: bool, match_alias: str, capsys, pytester):
        conf = pytester.makefile(".toml", test_toml=tr.TEST_TOML_CONTENTS)

        def generate_toml() -> str:
            pass

        def generate_command() -> str:
            command = f"--config {conf.as_posix()} get "
            command += feature_set.name + " "
            command += monitor_set

            return command

        def generate_output() -> str:
            output = ""
            for m in monitor_set.split(" "):
                output += "src for monitor "
                if m.isdigit():
                    output += "#"
                output += m + " "
                output += "is 27 "



