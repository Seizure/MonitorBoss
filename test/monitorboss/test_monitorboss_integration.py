import json
from textwrap import dedent

import test.pyddc
from pyddc import parse_capabilities
from pyddc.vcp_codes import VCPCodes
from test.pyddc import vcp_dummy
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
    expected = output.caps_raw_output([(mdata0, impl.get_vcp_capabilities(0))], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps --raw 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_raw_json(test_conf_file, test_cfg, capsys):
    expected = output.caps_raw_output([(mdata0, impl.get_vcp_capabilities(0))], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json caps --raw 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_full_human(test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_parsed_output([(mdata0, caps)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
    
    
def test_caps_full_json(test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_parsed_output([(mdata0, caps)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json caps 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_caps_summary_human(test_conf_file, test_cfg, capsys):
    caps = info.capability_summary_data(info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg))
    expected = output.caps_parsed_output([(mdata0, caps)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} caps --summary 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
    

def test_caps_summary_json(test_conf_file, test_cfg, capsys):
    caps = info.capability_summary_data(info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg))
    expected = output.caps_parsed_output([(mdata0, caps)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json caps --summary 0")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_get_feature_human(test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(lum.value, 75, cfg)
    expected = output.get_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, 80, None)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} get 0 lum")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_get_feature_json(test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(lum.value, 75, cfg)
    expected = output.get_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, 80, None)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json get 0 lum")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_set_feature_human(test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(lum.value, 24, cfg)
    expected = output.set_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} set 0 lum 24")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_set_feature_json(test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(lum.value, 35, cfg)
    expected = output.set_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json set 0 lum 35")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_tog_feature_human(test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata1 = info.value_data(lum.value, 75, cfg)
    vdata2 = info.value_data(lum.value, 42, cfg)
    expected = output.tog_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata1, vdata2)], False) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} tog 0 lum 42 21")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


def test_tog_feature_json(test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata1 = info.value_data(lum.value, 75, cfg)
    vdata2 = info.value_data(lum.value, 42, cfg)
    expected = output.tog_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata1, vdata2)], True) + "\n"
    cli.run(f"--config {test_conf_file.as_posix()} --json tog 0 lum 42 21")
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
