from dataclasses import dataclass
from logging import getLogger
from time import sleep

from pyddc import VCP, VCPCommand, get_vcp_com, VCPError, VCPFeatureReturn
from pyddc.vcp_codes import VCPCodes

from monitorboss import MonitorBossError
from monitorboss.config import get_config

_log = getLogger(__name__)


def list_monitors() -> list[VCP]:
    _log.debug("list monitors")
    try:
        return VCP.get_vcps()
    except VCPError as err:
        # this can only happen on Windows
        raise MonitorBossError(f"Failed to list VCPs.") from err


def get_monitor(mon: int) -> VCP:
    _log.debug(f"get monitor: {mon}")
    monitors = list_monitors()
    try:
        return monitors[mon]
    except IndexError as err:
        raise MonitorBossError(f"monitor #{mon} does not exist.") from err


def get_vcp_capabilities(mon: int) -> str:
    _log.debug(f"get VCP capabilities for monitor #{mon}")
    with get_monitor(mon) as monitor:
        try:
            return monitor.get_vcp_capabilities()
        except VCPError as err:
            raise MonitorBossError(f"Could not list information for monitor {mon}") from err


def get_feature(mon: int, feature: VCPCommand, timeout: float) -> VCPFeatureReturn:
    _log.debug(f"get feature: {feature.name} (for monitor #{mon})")
    with get_monitor(mon) as monitor:
        try:
            val = monitor.get_vcp_feature(feature, timeout)
            _log.debug(f"get_vcp_feature for {feature.name} on monitor #{mon} returned {val.value} (max {val.max})")
            return val
        except VCPError as err:
            raise MonitorBossError(f"could not get {feature.name} for monitor #{mon}.") from err
        except TypeError as err:
            raise MonitorBossError(f"{feature.name} is not a readable feature.") from err


def set_feature(mon: int, feature: VCPCommand, val: int, timeout: float) -> int:
    _log.debug(f"set feature: {feature.name} = {val} (for monitor #{mon})")
    with get_monitor(mon) as monitor:
        try:
            monitor.set_vcp_feature(feature, val, timeout)
        except VCPError as err:
            raise MonitorBossError(f"could not set {feature.name} for monitor #{mon} to {val}.") from err
        except TypeError as err:
            raise MonitorBossError(f"{feature.name} is not a writeable feature.") from err
        except ValueError as err:
            raise MonitorBossError(f"Provided value ({val}) is above the max for this feature ({feature.name})") from err
        return val


@dataclass
class ToggledFeature:
    old: int
    new: int


def toggle_feature(mon: int, feature: VCPCommand, val1: int, val2: int, timeout: float) -> ToggledFeature:
    _log.debug(f"toggle feature: {feature.name} between {val1} and {val2} (for monitor #{mon})")
    cur_val = get_feature(mon, feature, timeout).value
    new_val = val2 if cur_val == val1 else val1
    set_feature(mon, feature, new_val, timeout)
    return ToggledFeature(cur_val, new_val)


def signal_monitor(mon: int, set_wait: float, internal_wait: float) -> None:
    _log.debug(f"signal monitor #{mon} (cycle its luminance)")
    visible_wait = max(set_wait, 1.0)
    lum = get_feature(mon, get_vcp_com(VCPCodes.image_luminance), internal_wait)
    sleep(set_wait)
    set_feature(mon, get_vcp_com(VCPCodes.image_luminance), lum.max, internal_wait)
    sleep(visible_wait)
    set_feature(mon, get_vcp_com(VCPCodes.image_luminance), 0, internal_wait)
    sleep(visible_wait)
    set_feature(mon, get_vcp_com(VCPCodes.image_luminance), lum.value, internal_wait)
