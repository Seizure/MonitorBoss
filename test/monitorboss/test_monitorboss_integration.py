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
from ..testdata import *

lum = VCPCodes.image_luminance


@pytest.mark.parametrize("json_flag", [
    False,
    True,
])
def test_list(json_flag, test_conf_file, capsys):
    expected = output.list_mons_output([m_data_0_foo, m_data_1_barbaz, m_data_2_noalias], json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} list".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [
    False,
    True,
])
def test_caps_raw(json_flag, test_conf_file, capsys):
    responses = [
        info.MonitorCapsResponseData(mon=m_data_0_foo, error=None, data=impl.get_vcp_capabilities(0)),
        info.MonitorCapsResponseData(mon=m_data_1_barbaz, error=Exception("Could not list information for monitor 1"), data=None),
        info.MonitorCapsResponseData(mon=m_data_2_noalias, error=None, data=impl.get_vcp_capabilities(2))
    ]
    expected = output.caps_raw_output(responses, json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} caps --raw 0 1 2".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [
    False,
    True,
])
def test_caps_full(json_flag, test_conf_file, test_cfg, capsys):
    caps_0 = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg)
    caps_2 = info.capability_data(parse_capabilities(impl.get_vcp_capabilities(2)), test_cfg)
    responses = [
        info.MonitorCapsResponseData(mon=m_data_0_foo, error=None, data=caps_0),
        info.MonitorCapsResponseData(mon=m_data_1_barbaz, error=Exception("Could not list information for monitor 1"), data=None),
        info.MonitorCapsResponseData(mon=m_data_2_noalias, error=None, data=caps_2)
    ]
    expected = output.caps_parsed_output(responses, json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} caps 0 1 2".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [
    False, True])
def test_caps_summary(json_flag, test_conf_file, test_cfg, capsys):
    caps_0 = info.capability_summary_data(info.capability_data(parse_capabilities(impl.get_vcp_capabilities(0)), test_cfg))
    caps_2 = info.capability_summary_data(info.capability_data(parse_capabilities(impl.get_vcp_capabilities(2)), test_cfg))
    responses = [
        info.MonitorCapsResponseData(mon=m_data_0_foo, error=None, data=caps_0),
        info.MonitorCapsResponseData(mon=m_data_1_barbaz, error=Exception("Could not list information for monitor 1"), data=None),
        info.MonitorCapsResponseData(mon=m_data_2_noalias, error=None, data=caps_2)
    ]
    expected = output.caps_parsed_output(responses, json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} caps --summary 0 1 2".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [
    False,
    True,
])
def test_get_feature(json_flag, test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata_0 = info.value_data(lum.value, 75, cfg)
    vdata_2 = info.value_data(lum.value, 75, cfg)
    responses = [
        info.MonitorGetResponseData(mon=m_data_0_foo, error=None, value=vdata_0, maximum=80),
        info.MonitorGetResponseData(mon=m_data_1_barbaz, error=Exception("could not get image_luminance for monitor #1."), value=None, maximum=None),
        info.MonitorGetResponseData(mon=m_data_2_noalias, error=None, value=vdata_2, maximum=80)
    ]
    expected = output.get_feature_output(info.feature_data(lum, test_cfg), responses, json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} get 0 1 2 lum".strip()
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
    responses = [
        info.MonitorSetResponseData(mon=m_data_0_foo, error=None, value=vdata),
        info.MonitorSetResponseData(mon=m_data_1_barbaz, error=Exception(f"could not set image_luminance for monitor #1 to {value}."), value=None),
        info.MonitorSetResponseData(mon=m_data_2_noalias, error=None, value=vdata)
    ]
    expected = output.set_feature_output(info.feature_data(lum, test_cfg), responses, json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} set 0 1 2 lum {value}".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""


@pytest.mark.parametrize("json_flag", [
    False,
    True,
])
def test_tog_feature(json_flag, test_conf_file, test_cfg, capsys):
    cfg = config.get_config(test_conf_file.as_posix())
    vdata1 = info.value_data(lum.value, 75, cfg)
    vdata2 = info.value_data(lum.value, 42, cfg)
    responses = [
        info.MonitorToggleResponseData(mon=m_data_0_foo, error=None, original_value=vdata1, new_value=vdata2),
        info.MonitorToggleResponseData(mon=m_data_1_barbaz, error=Exception("could not get image_luminance for monitor #1."), original_value=None, new_value=None),
        info.MonitorToggleResponseData(mon=m_data_2_noalias, error=None, original_value=vdata1, new_value=vdata2)
    ]
    expected = output.tog_feature_output(info.feature_data(lum, test_cfg), responses, json_flag) + "\n"
    cmd = f"--config {test_conf_file.as_posix()} {'--json' if json_flag else ''} tog 0 1 2 lum 42 21".strip()
    cli.run(cmd)
    capture = capsys.readouterr()
    assert capture.out == expected
    assert capture.err == ""
