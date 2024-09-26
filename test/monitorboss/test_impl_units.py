import pytest

from monitorboss import impl, MonitorBossError


def test_impl_get_monitor_valid():
    assert impl.get_monitor(1)


def test_impl_get_monitor_invalid():
    # TODO: is it weird that we allow negative indices, per pythonic behavior?
    # with pytest.raises(MonitorBossError):
    #     impl._get_monitor(-1)
    with pytest.raises(MonitorBossError):
        impl.get_monitor(3)
