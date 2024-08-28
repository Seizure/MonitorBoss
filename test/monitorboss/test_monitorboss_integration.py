from textwrap import dedent

import pytest
import tomlkit

import test.pyddc
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.monitorboss import TEST_TOML_CONTENTS
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, MonitorBossError, impl

pytest_plugins = "pytester"


def test_list(pytester, capsys):
    expected = dedent("""\
    monitor #0 (foo)
    monitor #1 (bar, baz)
    monitor #2
    """)
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cli.run(f"--config {conf.as_posix()} list")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_caps_raw(pytester, capsys):
    expected = test.pyddc.CAPS_STR + "\n"
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cli.run(f"--config {conf.as_posix()} caps --raw 0")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


# TODO: this is going to be annoying, do it properly later
def test_caps_dict(pytester, capsys):
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cli.run(f"--config {conf.as_posix()} caps 0")
    output = capsys.readouterr()
    assert output.out # TODO: actually test something meaningful
    assert output.err == ""


# TODO: this is going to be annoying, do it properly later
def test_caps_summary(pytester, capsys):
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cli.run(f"--config {conf.as_posix()} caps --summary 0")
    output = capsys.readouterr()
    assert output.out  # TODO: actually test something meaningful
    assert output.err == ""


def test_get_attr(pytester, capsys):
    com = get_vcp_com(VCPCodes.input_source)
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cfg = config.get_config(conf.as_posix())
    expected = f"{cli._feature_str(com, cfg)} for {cli._monitor_str(1, cfg)} is {cli._value_str(com, 27, cfg)}\n"
    cli.run(f"--config {conf.as_posix()} get src 1")
    output = capsys.readouterr()
    assert output.out  == expected
    assert output.err == ""


def test_set_attr(pytester, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cfg = config.get_config(conf.as_posix())
    expected = f"set {cli._feature_str(com, cfg)} for {cli._monitor_str(1, cfg)} to {cli._value_str(com, 75, cfg)}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {conf.as_posix()} set lum 75 bar")
    output = capsys.readouterr()
    assert output.out  == expected
    assert output.err == ""


def test_tog_attr(pytester, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
    cfg = config.get_config(conf.as_posix())
    expected = f"toggled {cli._feature_str(com, cfg)} for {cli._monitor_str(1, cfg)} from {cli._value_str(com, 75, cfg)} to {cli._value_str(com, 75, cfg)}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {conf.as_posix()} tog lum 75 75 bar")
    output = capsys.readouterr()
    assert output.out  == expected
    assert output.err == ""


# # TODO: will need to change/add the CLI test functions when we support all codes, and command by int/name/alias
# class TestCLIGet:
#     """
#     CLI variances:
#         1. a) discrete vs b) continuous feature (whether to show the max) (2)
#         2. monitor has a) no aliases, b) one, or c) multiple (3)
#         3. monitor reference by a) id vs b) alias (in all cases, output should show the ID along with any/all aliases) (2)
#         4. whether the feature return value has a) a matching param name or b) not (2)
#         5. whether the feature return value has a) no matching aliases, b) one, or c) multiple (3)
#         6. a) single vs b) multi-monitor command (2)
#     """
#
#     # Between the below three functions, we test every variance mentioned.
#
#     # test 1a, 2a, 3a, 4a, 5b, 6a
#     def test_disc_nomonalias_monbyid_yesfeatparam_onefeatalias_singlemon(self, capsys, pytester):
#         toml_contents = """
#         [monitor_names]
#
#         [input_names]
#         17 = ["hdmi"]
#
#         [settings]
#         wait_get = 0
#         wait_set = 0
#         wait_internal = 0""".strip()
#         conf = pytester.makefile(".toml", test_toml=toml_contents)
#         with capsys.disabled():
#             run(f"--config {conf.as_posix()} set src hdmi1 0")
#         run(f"--config {conf.as_posix()} get src 0")
#         assert capsys.readouterr().out == "src for monitor #0 is 17 <hdmi1 | hdmi>\n"
#         assert capsys.readouterr().err == ""
#
#     # test 1b, 2b, 3b, 4b, 5a | 6a is repeated
#     def test_cont_onemonalias_monbyalias_nofeatparam_nofeatalias_singlemon(self, capsys, pytester):
#         toml_contents = """
#             [monitor_names]
#             0 = "foo"
#
#             [input_names]
#             17 = ["hdmi"]
#
#             [settings]
#             wait_get = 0
#             wait_set = 0
#             wait_internal = 0""".strip()
#         conf = pytester.makefile(".toml", test_toml=toml_contents)
#         run(f"--config {conf.as_posix()} get cnt foo")
#         assert capsys.readouterr().out == "cnt for monitor #0 <foo> is 75 (Maximum: 100)\n"
#         assert capsys.readouterr().err == ""
#
#     # test 2c, 5c, 6b | 1a, 3a, 3b, 4a are repeated
#     def test_disc_multimonalias_monbyboth_yesfeatparam_multifeatalias_multimon(self, capsys, pytester):
#         toml_contents = """
#             [monitor_names]
#             0 = ["foo", "bar"]
#
#             [input_names]
#             17 = ["hdmi", "qux"]
#
#             [settings]
#             wait_get = 0
#             wait_set = 0
#             wait_internal = 0""".strip()
#         conf = pytester.makefile(".toml", test_toml=toml_contents)
#         with capsys.disabled():
#             run(f"--config {conf.as_posix()} set src hdmi1 0")
#         run(f"--config {conf.as_posix()} get src bar 1")
#         assert capsys.readouterr().out == """src for monitor #0 <foo, bar> is 17 <hdmi1 | hdmi, qux> (Maximum: 100)\n"""
#         assert capsys.readouterr().err == ""
#
#
#     def test_get_discreet_by_alias(self, capsys, pytester):
#         conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
#         run(f"--config {conf.as_posix()} get src foo")
#         assert capsys.readouterr().out == "src for monitor \"foo\" is 27 (usbc)\n"
#         assert capsys.readouterr().err == ""
#
#     def test_get_discreet_by_id(self, capsys, pytester):
#         conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
#         run(f"--config {conf.as_posix()} get src 1")
#         assert capsys.readouterr().out == "src for monitor #1 is 27 (usbc, usb_c, usb-c)\n"
#         assert capsys.readouterr().err == ""
#
#     @pytest.mark.parametrize("feature_set", [INPUT_SOURCE, CONTRAST])
#     @pytest.mark.parametrize("monitor_set", ["foo", "baz 2", "2"])
#     @pytest.mark.parametrize("match_param", [True, False])
#     @pytest.mark.parametrize("match_alias", ["none", "single", "multi"])
#     def test_get(self, feature_set: pyddc.VCPCommand, monitor_set: str, match_param: bool, match_alias: str, capsys,
#                  pytester):
#         conf = pytester.makefile(".toml", test_toml=TEST_TOML_CONTENTS)
#
#         def generate_toml() -> str:
#             pass
#
#         def generate_command() -> str:
#             command = f"--config {conf.as_posix()} get "
#             command += feature_set.name + " "
#             command += monitor_set
#
#             return command
#
#         def generate_output() -> str:
#             output = ""
#             for m in monitor_set.split(" "):
#                 output += "src for monitor "
#                 if m.isdigit():
#                     output += "#"
#                 output += m + " "
#                 output += "is 27 "
