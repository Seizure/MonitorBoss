from collections import namedtuple
from dataclasses import dataclass
from enum import Enum
from time import sleep

from monitorcontrol import VCP, VCPCommand, get_vcp_com, VCPError

from monitorboss import MonitorBossError
from monitorboss.config import get_config


@dataclass
class AttributeData:
    short_desc: str
    com: VCPCommand
    description: str
    notes: str


class Attribute(Enum):
    src = AttributeData("input source", get_vcp_com(96),
                        "(currently active) input source",
                        "Must be a valid source ID, or alias as defined by the application built-ins or config file additions")
    cnt = AttributeData("contrast", get_vcp_com(18),
                        "contrast",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    lum = AttributeData("luminance", get_vcp_com(16),
                        "luminance/brightness",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    pwr = AttributeData("power mode", get_vcp_com(214),
                        "power mode/state",
                        "Must be a valid power state, as defined by built-in aliases")
    clr = AttributeData("color preset", get_vcp_com(20),
                        "(currently active) color preset",
                        "Must be a valid color temperature preset, as defined by built-in aliases")

    def __str__(self):
        return self.name


def list_monitors() -> list[VCP]:
    try:
        return VCP.get_vcps()
    except VCPError as err:
        # this can only happen in Windows
        raise MonitorBossError(f"Failed to list VCPs.") from err


def __get_monitor(index: int) -> VCP:
    monitors = list_monitors()
    try:
        return monitors[index]
    except IndexError as err:
        raise MonitorBossError(f"monitor #{index} does not exist.") from err


def get_vcp_capabilities(mon: int) -> str:
    with __get_monitor(mon) as monitor:
        try:
            return monitor.get_vcp_capabilities()
        except VCPError as err:
            raise MonitorBossError(f"Could not list information for monitor {mon}") from err


def get_attribute(mon: int, attr: Attribute) -> (int, int):
    with __get_monitor(mon) as monitor:
        try:
            return monitor.get_vcp_feature(attr.value.com)
        except VCPError as err:
            raise MonitorBossError(f"could not get {attr.value.short_desc} for monitor #{mon}.") from err


def set_attribute(mon: int, attr: Attribute, val: int) -> int:
    with __get_monitor(mon) as monitor:
        try:
            monitor.set_vcp_feature(attr.value.com, val)
        except VCPError as err:
            raise MonitorBossError(f"could not set {attr.value.short_desc} for monitor #{mon} to {val}.") from err
        # TODO: make this return val from a getter, it didn't work when we first tried this
        return val


def toggle_attribute(mon: int, attr: Attribute, val1: int, val2: int) -> (int, int):
    cur_val = get_attribute(mon, attr).value
    new_val = val2 if cur_val == val1 else val1
    set_attribute(mon, attr, new_val)
    Vals = namedtuple("Vals", ["mon", "old", "new"])
    return Vals(mon, cur_val, new_val)


def signal_monitor(mon: int):
    cfg = get_config()
    wait = cfg.wait_time

    cur_lum, max_lum = get_attribute(mon, Attribute.lum)
    sleep(wait)
    set_attribute(mon, Attribute.lum, max_lum)
    sleep(wait)
    set_attribute(mon, Attribute.lum, 0)
    sleep(wait)
    set_attribute(mon, Attribute.lum, cur_lum)
