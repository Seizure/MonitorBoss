from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Union

from monitorcontrol import get_monitors, ColorPreset, InputSource, Monitor, PowerMode, VCPError
from monitorcontrol.monitorcontrol import InputSourceValueError


def get_input_source(monitor: Monitor) -> InputSource | int:
    try:
        return monitor.get_input_source()
    except InputSourceValueError as err:
        # Some monitors use non-standard codes that are outside of spec.
        return err.value


@dataclass
class AttributeData:
    shortdesc: str
    getter: Union[Callable[[Monitor], ...], None]
    setter: Union[Callable[[Monitor, ...], None], None]
    description: str
    notes: str


class Attribute(Enum):
    SRC = AttributeData("input source", get_input_source, Monitor.set_input_source,
                        "(currently active) input source",
                        "Must be a valid source ID, or alias as defined by the application built-ins or config file additions")
    CNT = AttributeData("contrast", Monitor.get_contrast, Monitor.set_contrast,
                        "contrast",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    LUM = AttributeData("luminance", Monitor.get_luminance, Monitor.set_luminance,
                        "luminance/brightness",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    PWR = AttributeData("power mode", Monitor.get_power_mode, Monitor.set_power_mode,
                        "power mode/state",
                        "Must be a valid power state, as defined by built-in aliases")
    CLR = AttributeData("color preset", Monitor.get_color_preset, Monitor.set_color_preset,
                        "(currently active) color preset",
                        "Must be a valid color temperature preset, as defined by built-in aliases")
    VCP = AttributeData("VCP capabilities", Monitor.get_vcp_capabilities, None,
                        "summary of the Virtual Control Panel's abilities",
                        "This attribute can only be read")


class MonitorBossError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def list_monitors() -> list[Monitor]:
    try:
        return get_monitors()
    except Exception as err:
        raise MonitorBossError(f"could not list monitors; are you using a laptop?") from err


def __get_monitor(index: int) -> Monitor:
    monitors = list_monitors()
    try:
        return monitors[index]
    except IndexError as err:
        raise MonitorBossError(f"monitor #{index} does not exist.") from err


def get_attribute(mon: int, attr: Attribute) -> ColorPreset | InputSource | PowerMode | int | dict:
    with __get_monitor(mon) as monitor:
        if attr.value.getter is None:
            raise MonitorBossError(f"cannot get a value for {attr.value.shortdesc}.")

        try:
            return attr.value.getter(monitor)
        except Exception as err:
            raise MonitorBossError(f"could not get {attr.value.shortdesc} for monitor #{mon}.") from err


def set_attribute(mons: int | list[int], attr: Attribute, val: ColorPreset | InputSource | PowerMode | int):
    if isinstance(mons, int):
        mons = [mons]

    for mon in mons:
        with __get_monitor(mon) as monitor:
            if attr.value.setter is None:
                raise MonitorBossError(f"cannot set a value for {attr.value.shortdesc}.")

            try:
                attr.value.setter(monitor, val)
            except Exception as err:
                raise MonitorBossError(f"could not set {attr.value.shortdesc} for monitor #{mon} to {val}.") from err


def toggle_attribute(
    mons: int | list[int],
    attr: Attribute,
    val1: ColorPreset | InputSource | PowerMode | int,
    val2: ColorPreset | InputSource | PowerMode | int,
):
    if isinstance(mons, int):
        mons = [mons]

    for mon in mons:
        with __get_monitor(mon) as monitor:
            if attr.value.getter is None or attr.value.setter is None:
                raise MonitorBossError(f"cannot toggle a value for {attr.value.shortdesc}.")

            try:
                cur_val = attr.value.getter(monitor)
            except Exception as err:
                raise MonitorBossError(f"could not get current {attr.value.shortdesc} for monitor #{mon}.") from err

            new_val = val2 if cur_val == val1 else val1

            try:
                attr.value.setter(monitor, new_val)
            except Exception as err:
                raise MonitorBossError(f"could not toggle {attr.value.shortdesc} for monitor #{mon} to {new_val}.") from err
