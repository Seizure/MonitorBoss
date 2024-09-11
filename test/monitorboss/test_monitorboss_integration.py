from textwrap import dedent

import test.pyddc
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, info


def test_list_human(test_conf_file, capsys):
    expected = dedent("""\
    monitor #0 (foo)
    monitor #1 (bar, baz)
    monitor #2
    """)
    cli.run(f"--config {test_conf_file.as_posix()} list")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""
    
    
def test_list_json(test_conf_file, capsys):
    pass  # TODO: stub


def test_caps_raw_human(test_conf_file, capsys):
    expected = test.pyddc.CAPS_STR + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps --raw 0")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_caps_raw_json(test_conf_file, capsys):
    pass  # TODO: stub


# TODO: this is going to be annoying, do it properly later
def test_caps_dict_human(test_conf_file, capsys):
    cli.run(f"--config {test_conf_file.as_posix()} caps 0")
    output = capsys.readouterr()
    assert output.out  # TODO: actually test something meaningful
    assert output.err == ""
    
    
def test_caps_dict_json(test_conf_file, capsys):
    pass  # TODO: stub


# TODO: this is going to be annoying, do it properly later
def test_caps_summary_human(test_conf_file, capsys):
    cli.run(f"--config {test_conf_file.as_posix()} caps --summary 0")
    output = capsys.readouterr()
    assert output.out  # TODO: actually test something meaningful
    assert output.err == ""
    

def test_caps_summary_json(test_conf_file, capsys):
    pass  # TODO: stub


def test_get_feature_human(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    fstring = info.feature_str(info.feature_data(com, cfg))
    mstring = info.monitor_str(info.monitor_data(1, cfg))
    vstring = info.value_str(info.value_data(com, 75, cfg))
    expected = f"{fstring} for {mstring} is {vstring} (Maximum: 75)\n"
    cli.run(f"--config {test_conf_file.as_posix()} get 1 lum")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_get_feature_json(test_conf_file, capsys):
    pass  # TODO: stub


def test_set_feature_human(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    fstring = info.feature_str(info.feature_data(com, cfg))
    mstring = info.monitor_str(info.monitor_data(1, cfg))
    vstring = info.value_str(info.value_data(com, 75, cfg))
    expected = f"set {fstring} for {mstring} to {vstring}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} set bar lum 75")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_set_feature_json(test_conf_file, capsys):
    pass  # TODO: stub


def test_tog_feature_human(test_conf_file, capsys):
    com = get_vcp_com(VCPCodes.image_luminance)
    cfg = config.get_config(test_conf_file.as_posix())
    fstring = info.feature_str(info.feature_data(com, cfg))
    mstring = info.monitor_str(info.monitor_data(1, cfg))
    vstring = info.value_str(info.value_data(com, 75, cfg))
    expected = f"toggled {fstring} for {mstring} from {vstring} to {vstring}\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} tog bar lum 75 75")
    output = capsys.readouterr()
    assert output.out == expected
    assert output.err == ""


def test_tog_feature_json(test_conf_file, capsys):
    pass  # TODO: stub
