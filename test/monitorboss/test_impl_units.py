import pytest

import pyddc
from test.pyddc.vcp_dummy import DummyVCP as VCP
pyddc.VCP = VCP

from monitorboss import impl, MonitorBossError
from test.testdata import edid_blob


# TODO: test the rest of the impl functions

def test_impl_get_monitor_valid():
    assert impl.get_monitor(1)


def test_impl_get_monitor_invalid():
    # TODO: is it weird that we allow negative indices, per pythonic behavior?
    # with pytest.raises(MonitorBossError):
    #     impl._get_monitor(-1)
    with pytest.raises(MonitorBossError):
        impl.get_monitor(3)


def test_impl_get_edid_blob_valid():
    result = impl.get_edid_blob(0)
    assert result == edid_blob


def test_impl_get_edid_blob_vcperror():
    # Monitor index 1 uses FAULTY_VCP_TEMPLATE, so get_edid_blob raises VCPError
    # which impl should wrap in MonitorBossError
    with pytest.raises(MonitorBossError):
        impl.get_edid_blob(1)
