from textwrap import dedent

import monitorboss.info
import test.pyddc
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, info


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
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    fstring = monitorboss.info.feature_str(monitorboss.info.feature_data(com, cfg))
    mstring = monitorboss.info.monitor_str(monitorboss.info.monitor_data(1, cfg))
    vstring = monitorboss.info.value_str(monitorboss.info.value_data(com, 75, cfg))
    expected = f"{fstring} for {mstring} is {vstring} (Maximum: 75)\n"
    cli.run(f"--config {test_conf_file.as_posix()} get 1 lum")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_set_attr(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    fstring = monitorboss.info.feature_str(monitorboss.info.feature_data(com, cfg))
    mstring = monitorboss.info.monitor_str(monitorboss.info.monitor_data(1, cfg))
    vstring = monitorboss.info.value_str(monitorboss.info.value_data(com, 75, cfg))
    expected = f"set {fstring} for {mstring} to {vstring}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} set bar lum 75")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_tog_attr(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    fstring = monitorboss.info.feature_str(monitorboss.info.feature_data(com, cfg))
    mstring = monitorboss.info.monitor_str(monitorboss.info.monitor_data(1, cfg))
    vstring = monitorboss.info.value_str(monitorboss.info.value_data(com, 75, cfg))
    expected = f"toggled {fstring} for {mstring} from {vstring} to {vstring}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} tog bar lum 75 75")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""
