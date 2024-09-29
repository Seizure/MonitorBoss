import json
from textwrap import dedent

import test.pyddc
from pyddc import parse_capabilities
from pyddc.vcp_codes import VCPCodes
from test.pyddc.vcp_dummy import DummyVCP as VCP
import pyddc
pyddc.VCP = VCP
from monitorboss import config, cli, info, output, impl

mdata0 = info.MonitorData(0, ("foo",))
mdata1 = info.MonitorData(1, ("bar", "baz"))
mdata2 = info.MonitorData(2, ())

lum = VCPCodes.image_luminance


def test_list_human(test_conf_file, capsys):
    expected = output.list_mons_output([mdata0, mdata1, mdata2], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} list")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
    
    
def test_list_json(test_conf_file, capsys):
    expected = output.list_mons_output([mdata0, mdata1, mdata2], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json list")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_raw_human(test_conf_file, capsys):
    expected = output.caps_raw_output(mdata0, test.pyddc.CAPS_STR, False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps --raw 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_raw_json(test_conf_file, test_cfg, capsys):
    expected = output.caps_raw_output(mdata0, test.pyddc.CAPS_STR, True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json caps --raw 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_full_human(test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_full_output(mdata0, caps, False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
    
    
def test_caps_full_json(test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_full_output(mdata0, caps, True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json caps 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_summary_human(test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_summary_output(mdata0, caps, False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps --summary 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
    

def test_caps_summary_json(test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_summary_output(mdata0, caps, True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json caps --summary 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""

# TODO: I am setting the feature to what it currently is in below functions, because this affects the state of the
#  pyddc tests. there should be a way to have separate "Sessions" for each test, should figure out later


def test_get_feature_human(test_conf_file, test_cfg, capsys):
    code = VCPCodes.image_luminance
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(code.value, 75, cfg)
    expected = output.get_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, 80)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} get 0 lum")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_get_feature_json(test_conf_file, test_cfg, capsys):
    code = VCPCodes.image_luminance
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(code.value, 75, cfg)
    expected = output.get_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, 80)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json get 0 lum")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_set_feature_human(test_conf_file, test_cfg, capsys):
    code = VCPCodes.image_luminance
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(code.value, 75, cfg)
    expected = output.set_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} set 0 lum 75")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_set_feature_json(test_conf_file, test_cfg, capsys):
    code = VCPCodes.image_luminance
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(code.value, 75, cfg)
    expected = output.set_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json set 0 lum 75")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_tog_feature_human(test_conf_file, test_cfg, capsys):
    code = VCPCodes.image_luminance
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(code.value, 75, cfg)
    expected = output.tog_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, vdata)], False) + "\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} tog 0 lum 75 75")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_tog_feature_json(test_conf_file, test_cfg, capsys):
    code = VCPCodes.image_luminance
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(code.value, 75, cfg)
    expected = output.tog_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, vdata)], True) + "\n"
    # TODO: I am setting it to the same thing it was, because this affects the state of the pyddc tests.
    #   there should be a way to have separate "Sessions" for each test, should figure out later
    cli.run(f"--config {test_conf_file.as_posix()} --json tog 0 lum 75 75")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
