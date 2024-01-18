from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

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
    desc: str
    getter: Union[Callable[[Monitor], ...], None]
    setter: Union[Callable[[Monitor, ...], None], None]


class Attribute(Enum):
    SRC = AttributeData("input source", get_input_source, Monitor.set_input_source)
    CNT = AttributeData("contrast", Monitor.get_contrast, Monitor.set_contrast)
    LUM = AttributeData("luminance", Monitor.get_luminance, Monitor.set_luminance)
    PWR = AttributeData("power mode", Monitor.get_power_mode, Monitor.set_power_mode)
    CLR = AttributeData("color preset", Monitor.get_color_preset, Monitor.set_color_preset)
    VCP = AttributeData("VCP capabilities", Monitor.get_vcp_capabilities, None)


class MonitorBossError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def list_monitors() -> List[Monitor]:
    try:
        return get_monitors()
    except:
        raise MonitorBossError(f"could not list monitors; are you using a laptop?")


def __get_monitor(index: int) -> Monitor:
    monitors = list_monitors()
    try:
        return monitors[index]
    except IndexError:
        raise MonitorBossError(f"monitor #{index} does not exist.")


def get_attribute(mon: int, attr: Attribute) -> str | int | dict:
    with __get_monitor(mon) as monitor:
        if attr.value.getter is None:
            raise MonitorBossError(f"cannot get a value for {attr.value.desc}.")

        try:
            val = attr.value.getter(monitor)
        except:
            raise MonitorBossError(f"could not get {attr.value.desc} for monitor #{mon}.")

        if isinstance(val, Enum):
            # ColorPreset, InputSource, and PowerMode are Enums.
            # ColorPreset values all start with "COLOR_TEMP_". PowerMode values are lowercase.
            val = val.name.upper().removeprefix("COLOR_TEMP_")

        return val


def set_attribute(mons: int | List[int], attr: Attribute, val: ColorPreset | InputSource | PowerMode | int):
    if isinstance(mons, int):
        mons = [mons]

    for mon in mons:
        with __get_monitor(mon) as monitor:
            if attr.value.setter is None:
                raise MonitorBossError(f"cannot set a value for {attr.value.desc}.")

            try:
                attr.value.setter(monitor, val)
            except:
                raise MonitorBossError(f"could not set {attr.value.desc} for monitor #{mon} to {val}.")


def toggle_attribute(mons: int | List[int], attr: Attribute, val1: ColorPreset | InputSource | PowerMode | int,
                     val2: ColorPreset | InputSource | PowerMode | int):
    if isinstance(mons, int):
        mons = [mons]

    for mon in mons:
        with __get_monitor(mon) as monitor:
            if attr.value.getter is None or attr.value.setter is None:
                raise MonitorBossError(f"cannot toggle a value for {attr.value.desc}.")

            try:
                cur_val = attr.value.getter(monitor)
            except:
                raise MonitorBossError(f"could not get current {attr.value.desc} for monitor #{mon}.")

            new_val = val2 if cur_val == val1 else val1

            try:
                attr.value.setter(monitor, new_val)
            except:
                raise MonitorBossError(f"could not toggle {attr.value.desc} for monitor #{mon} to {new_val}.")
