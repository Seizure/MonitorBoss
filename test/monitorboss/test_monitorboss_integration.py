import json
from textwrap import dedent

import pytest

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


@pytest.mark.parametrize("json_flag", [False, True])
def test_list(json_flag, test_conf_file, capsys):
    expected = output.list_mons_output([mdata0, mdata1, mdata2], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} list".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [False, True])
def test_caps_raw(json_flag, test_conf_file, capsys):
    expected = output.caps_raw_output([(mdata0, impl.get_vcp_capabilities(0))], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} caps --raw 0".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [False, True])
def test_caps_full(json_flag, test_conf_file, test_cfg, capsys):
    caps = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    expected = output.caps_parsed_output([(mdata0, caps)], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} caps 0".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [False, True])
def test_caps_summary(json_flag, test_conf_file, test_cfg, capsys):
    caps = info.capability_summary_data(info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg))
    expected = output.caps_parsed_output([(mdata0, caps)], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} caps --summary 0".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [False, True])
def test_get_feature(json_flag, test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(lum.value, 75, cfg)
    expected = output.get_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata, 80)], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} get 0 lum".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag, value", [
    (False, 24),
    (True, 35),
])
def test_set_feature(json_flag, value, test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata = info.value_data(lum.value, value, cfg)
    expected = output.set_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata)], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} set 0 lum {value}".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [False, True])
def test_tog_feature(json_flag, test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata1 = info.value_data(lum.value, 75, cfg)
    vdata2 = info.value_data(lum.value, 42, cfg)
    expected = output.tog_feature_output(info.feature_data(lum, test_cfg), [(mdata0, vdata1, vdata2)], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} tog 0 lum 42 21".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
