from dataclasses import dataclass
from enum import Enum

from monitorcontrol import get_monitors, InputSource, Monitor, PowerMode, VCPError
from monitorcontrol.monitorcontrol import InputSourceValueError


# TODO: make input source codes configurable.
# Seizure's Dell monitor's USB-C source has code 27. No idea how consistent this is.
input_sources = {27: InputSource.DP2}


@dataclass
class AttributeData:
    desc: str
    getter: ...
    setter: ...


class Attribute(Enum):
    SRC = AttributeData("input source", Monitor.get_input_source, Monitor.set_input_source)
    CNT = AttributeData("contrast", Monitor.get_contrast, Monitor.set_contrast)
    LUM = AttributeData("luminance", Monitor.get_luminance, Monitor.set_luminance)
    PWR = AttributeData("power mode", Monitor.get_power_mode, Monitor.set_power_mode)
    VCP = AttributeData("VCP capabilities", Monitor.get_vcp_capabilities, None)


class MonitorBossError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


def __get_monitor(index: int) -> Monitor:
    try:
        monitors = get_monitors()
    except:
        raise MonitorBossError(f"could not get monitors; are you using a laptop?")
    try:
        return monitors[index]
    except IndexError:
        raise MonitorBossError(f"monitor #{index} does not exist.")


def get_attribute(mon: int, attr: Attribute) -> str | int | dict:
    with __get_monitor(mon) as m:
        if attr.value.getter is None:
            raise MonitorBossError(f"cannot get a value for {attr.value.desc}.")

        try:
            val = attr.value.getter(m)
        except InputSourceValueError as e:
            # Some monitors use non-standard codes that are outside of spec.
            val = e.value
        except:
            raise MonitorBossError(f"could not get {attr.value.desc} for monitor #{mon}.")

        if isinstance(val, Enum):
            # InputSource and PowerMode are Enums; PowerMode values are lowercase.
            val = val.name.upper()

        return val


def set_attribute(mon: int, attr: Attribute, val: InputSource | PowerMode | int):
    with __get_monitor(mon) as m:
        if attr.value.setter is None:
            raise MonitorBossError(f"cannot set a value for {attr.value.desc}.")

        try:
            value.setter(m, val)
        except:
            raise MonitorBossError(f"could not set {attr.value.desc} for monitor #{mon}.")


def toggle_attribute(mon: int, attr: Attribute, val1: InputSource | PowerMode | int,
                     val2: InputSource | PowerMode | int):
    with __get_monitor(mon) as m:
        if attr.value.getter is None or attr.value.setter is None:
            raise MonitorBossError(f"cannot toggle a value for {attr.value.desc}.")

        try:
            cur_val = attr.value.getter(m)
        except InputSourceValueError as e:
            # Some monitors use non-standard codes that are outside of spec.
            if e.value in input_sources:
                cur_val = input_sources[e.value]
            else:
                raise MonitorBossError(f"{attr.value.desc} {e.value} for monitor #{mon} is not a standard value.")
        except:
            raise MonitorBossError(f"could not get {attr.value.desc} for monitor #{mon}.")

        new_val = val2 if cur_val == val1 else val1

        try:
            attr.value.setter(m, new_val)
        except:
            raise MonitorBossError(f"could not set {attr.value.desc} for monitor #{mon} to {new_val}.")
