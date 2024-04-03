from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Union, Any
from time import sleep

import monitorcontrol.monitorcontrol as mc
from monitorcontrol.monitorcontrol import ColorPreset, InputSource, PowerMode
from monitorcontrol.monitorcontrol import InputSourceValueError
from monitorcontrol.vcp import VCP

from monitorboss import MonitorBossError
from monitorboss.config import get_config


def get_input_source(monitor: VCP) -> Union[InputSource, int]:
    try:
        return mc.get_input_source(monitor)
    except InputSourceValueError as err:
        # Some monitors use non-standard codes that are outside of spec.
        return err.value


@dataclass
class AttributeData:
    shortdesc: str
    getter: Union[Callable[[VCP], ...], Any]
    setter: Union[Callable[[VCP, ...], Any], Any]
    description: str
    notes: str


class Attribute(Enum):
    src = AttributeData("input source", get_input_source, mc.set_input_source,
                        "(currently active) input source",
                        "Must be a valid source ID, or alias as defined by the application built-ins or config file additions")
    cnt = AttributeData("contrast", mc.get_contrast, mc.set_contrast,
                        "contrast",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    lum = AttributeData("luminance", mc.get_luminance, mc.set_luminance,
                        "luminance/brightness",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    pwr = AttributeData("power mode", mc.get_power_mode, mc.set_power_mode,
                        "power mode/state",
                        "Must be a valid power state, as defined by built-in aliases")
    clr = AttributeData("color preset", mc.get_color_preset, mc.set_color_preset,
                        "(currently active) color preset",
                        "Must be a valid color temperature preset, as defined by built-in aliases")
    vcp = AttributeData("VCP capabilities", mc.get_capabilities, None,
                        "summary of the Virtual Control Panel's abilities",
                        "This attribute can only be read")
    def __str__(self):
        return self.name

def list_monitors() -> list[VCP]:
    try:
        return mc.get_vcps()
    except Exception as err:
        raise MonitorBossError(f"could not list monitors; are you using a laptop?") from err


def __get_monitor(index: int) -> VCP:
    monitors = list_monitors()
    try:
        return monitors[index]
    except IndexError as err:
        raise MonitorBossError(f"monitor #{index} does not exist.") from err


def get_attribute(mon: int, attr: Attribute) -> Union[ColorPreset, InputSource, PowerMode, int, dict]:
    with __get_monitor(mon) as monitor:
        if attr.value.getter is None:
            raise MonitorBossError(f"cannot get a value for {attr.value.shortdesc}.")

        try:
            return attr.value.getter(monitor)
        except Exception as err:
            raise MonitorBossError(f"could not get {attr.value.shortdesc} for monitor #{mon}.") from err


def set_attribute(mons: Union[int, list[int]], attr: Attribute, val: Union[
    ColorPreset, InputSource, PowerMode, int]) -> Union[ColorPreset, InputSource, PowerMode, int, dict]:
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

            # TODO: make this return val from a getter, it didnt work when we first tried this
            return val


def toggle_attribute(
    mons: Union[int, list[int]],
    attr: Attribute,
    val1: Union[ColorPreset, InputSource, PowerMode, int],
    val2: Union[ColorPreset, InputSource, PowerMode, int],
) -> Union[ColorPreset, InputSource, PowerMode, int, dict]:
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

            return new_val


def signal_monitor(mon: int):
    cfg = get_config()
    wait = cfg.wait_time
    with __get_monitor(mon) as monitor:
        lum = Attribute.lum.value.getter(monitor)
        sleep(wait)
        Attribute.lum.value.setter(monitor, 100)
        sleep(wait)
        Attribute.lum.value.setter(monitor, 0)
        sleep(wait)
        Attribute.lum.value.setter(monitor, lum)
