from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from time import sleep

from pyddc import VCP, VCPCommand, get_vcp_com, VCPError
from pyddc.vcp_codes import VCPCodes

from monitorboss import MonitorBossError
from monitorboss.config import get_config

_log = getLogger(__name__)


@dataclass
class AttributeData:
    short_desc: str
    com: VCPCommand
    description: str
    notes: str


# TODO I'm not sure we need a short_desc var? Seems redundant to VCPCommand's "desc"
class Attribute(Enum):
    src = AttributeData("input source", get_vcp_com(VCPCodes.input_source),
                        "(currently active) input source",
                        "Must be a valid source ID, or alias as defined by the application built-ins or config file additions")
    cnt = AttributeData("contrast", get_vcp_com(VCPCodes.image_contrast),
                        "contrast",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    lum = AttributeData("luminance", get_vcp_com(VCPCodes.image_luminance),
                        "luminance/brightness",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    pwr = AttributeData("power mode", get_vcp_com(VCPCodes.display_power_mode),
                        "power mode/state",
                        "Must be a valid power state, as defined by built-in aliases")
    clr = AttributeData("color preset", get_vcp_com(VCPCodes.image_color_preset),
                        "(currently active) color preset",
                        "Must be a valid color temperature preset, as defined by built-in aliases")

    def __str__(self):
        return self.name


def list_monitors() -> list[VCP]:
    _log.debug("list monitors")
    try:
        return VCP.get_vcps()
    except VCPError as err:
        # this can only happen on Windows
        raise MonitorBossError(f"Failed to list VCPs.") from err


def __get_monitor(mon: int) -> VCP:
    _log.debug(f"get monitor: {mon}")
    monitors = list_monitors()
    try:
        return monitors[mon]
    except IndexError as err:
        raise MonitorBossError(f"monitor #{mon} does not exist.") from err


def get_vcp_capabilities(mon: int) -> str:
    _log.debug(f"get VCP capabilities for monitor #{mon}")
    with __get_monitor(mon) as monitor:
        try:
            return monitor.get_vcp_capabilities()
        except VCPError as err:
            raise MonitorBossError(f"Could not list information for monitor {mon}") from err


def get_attribute(mon: int, attr: Attribute, timeout: float) -> (int, int):
    _log.debug(f"get attribute: {attr} (for monitor #{mon})")
    with __get_monitor(mon) as monitor:
        try:
            val = monitor.get_vcp_feature(attr.value.com, timeout)
            _log.debug(f"get_vcp_feature for {attr} on monitor #{mon} returned {val.value} (max {val.max})")
            return val
        except VCPError as err:
            raise MonitorBossError(f"could not get {attr.value.short_desc} for monitor #{mon}.") from err
        except TypeError as err:
            print(err)
            raise MonitorBossError(f"{attr} is not a readable feature.") from err


def set_attribute(mon: int, attr: Attribute, val: int, timeout: float) -> int:
    _log.debug(f"set attribute: {attr} = {val} (for monitor #{mon})")
    with __get_monitor(mon) as monitor:
        try:
            monitor.set_vcp_feature(attr.value.com, val, timeout)
        except VCPError as err:
            raise MonitorBossError(f"could not set {attr.value.short_desc} for monitor #{mon} to {val}.") from err
        except TypeError as err:
            raise MonitorBossError(f"{attr} is not a writeable feature.") from err
        except ValueError as err:
            raise MonitorBossError(f"Provided value ({val}) is above the max for this feature ({attr})") from err
        # TODO: make this return val from a getter, it didn't work when we first tried this
        return val


@dataclass
class ToggledAttribute:
    old: int
    new: int


def toggle_attribute(mon: int, attr: Attribute, val1: int, val2: int, timeout: float) -> ToggledAttribute:
    _log.debug(f"toggle attribute: {attr} between {val1} and {val2} (for monitor #{mon})")
    cur_val = get_attribute(mon, attr, timeout).value
    new_val = val2 if cur_val == val1 else val1
    set_attribute(mon, attr, new_val, timeout)
    return ToggledAttribute(cur_val, new_val)


def signal_monitor(mon: int):
    _log.debug(f"signal monitor #{mon} (cycle its luminance)")
    cfg = get_config()
    timeout = cfg.wait_internal_time
    ddc_wait = cfg.wait_set_time
    visible_wait = max(ddc_wait, 1.0)
    lum = get_attribute(mon, Attribute.lum, timeout)
    sleep(ddc_wait)
    set_attribute(mon, Attribute.lum, lum.max, timeout)
    sleep(visible_wait)
    set_attribute(mon, Attribute.lum, 0, timeout)
    sleep(visible_wait)
    set_attribute(mon, Attribute.lum, lum.value, timeout)
