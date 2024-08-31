from textwrap import dedent

import test.pyddc
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli


def test_list(test_conf_file, capsys):
    expected = dedent("""\
    monitor #0 (foo)
    monitor #1 (bar, baz)
    monitor #2
    """)
    cli.run(f"--config {test_conf_file.as_posix()} list")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_caps_raw(test_conf_file, capsys):
    expected = test.pyddc.CAPS_STR + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps --raw 0")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


# TODO: this is going to be annoying, do it properly later
def test_caps_dict(test_conf_file, capsys):
    cli.run(f"--config {test_conf_file.as_posix()} caps 0")
    output = capsys.readouterr()
    assert output.out  # TODO: actually test something meaningful
    assert output.err == ""


# TODO: this is going to be annoying, do it properly later
def test_caps_summary(test_conf_file, capsys):
    cli.run(f"--config {test_conf_file.as_posix()} caps --summary 0")
    output = capsys.readouterr()
    assert output.out  # TODO: actually test something meaningful
    assert output.err == ""


def test_get_attr(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.input_source)
    cfg = config.get_config(test_conf_file.as_posix())
    expected = f"{cli._feature_str(com, cfg)} for {cli._monitor_str(1, cfg)} is {cli._value_str(com, 27, cfg)}\n"
    cli.run(f"--config {test_conf_file.as_posix()} get src 1")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_set_attr(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    expected = f"set {cli._feature_str(com, cfg)} for {cli._monitor_str(1, cfg)} to {cli._value_str(com, 75, cfg)}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} set lum 75 bar")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_tog_attr(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    expected = f"toggled {cli._feature_str(com, cfg)} for {cli._monitor_str(1, cfg)} from {cli._value_str(com, 75, cfg)} to {cli._value_str(com, 75, cfg)}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} tog lum 75 75 bar")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""
