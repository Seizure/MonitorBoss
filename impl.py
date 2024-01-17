from enum import Enum

from monitorcontrol import get_monitors, InputSource, Monitor, PowerMode as PowerModeLower, VCPError
from monitorcontrol.monitorcontrol import InputSourceValueError


# TODO: make input source codes configurable.
# Seizure's Dell monitor's USB-C source has code 27. No idea how consistent this is.
input_sources = {27: InputSource.DP2}


class Attribute(Enum):
    SRC = "SRC"
    CNT = "CNT"
    LUM = "LUM"
    PWR = "PWR"
    VCP = "VCP"


class PowerMode(Enum):
    ON = PowerModeLower.on
    STANDBY = PowerModeLower.standby
    SUSPEND = PowerModeLower.suspend
    OFF_SOFT = PowerModeLower.off_soft
    OFF_HARD = PowerModeLower.off_hard


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


def get_attribute(mon: int, attr: Attribute) -> str | int:
    with __get_monitor(mon) as m:
        match attr:
            case Attribute.SRC:
                try:
                    return m.get_input_source().name
                except InputSourceValueError as e:
                    # Some monitors use non-standard codes that are outside of spec.
                    # Just return their code (int), instead of name (str).
                    return e.value
                except:
                    raise MonitorBossError(f"could not get input source for monitor #{mon}.")

            case Attribute.CNT:
                try:
                    return m.get_contrast()
                except:
                    raise MonitorBossError(f"could not get contrast for monitor #{mon}.")

            case Attribute.LUM:
                try:
                    return m.get_luminance()
                except:
                    raise MonitorBossError(f"could not get luminance for monitor #{mon}.")

            case Attribute.PWR:
                try:
                    return m.get_power_mode().name
                except:
                    raise MonitorBossError(f"Could not get power mode for monitor #{mon}.")

            case Attribute.VCP:
                try:
                    return m.get_vcp_capabilities().name
                except:
                    raise MonitorBossError(f"could not get VCP capabilities for monitor #{mon}.")

            case _:
                raise MonitorBossError(f"{attr} is not a valid attribute to get.")


def set_attribute(mon: int, attr: Attribute, val: InputSource | PowerMode | int):
    with __get_monitor(mon) as m:
        match attr:
            case Attribute.SRC:
                try:
                    m.set_input_source(val)
                except:
                    raise MonitorBossError(f"could not set input source for monitor #{mon}.")

            case Attribute.CNT:
                try:
                    m.set_contrast(val)
                except:
                    raise MonitorBossError(f"could not set contrast for monitor #{mon}.")

            case Attribute.LUM:
                try:
                    m.set_luminance(val)
                except:
                    raise MonitorBossError(f"could not set luminance for monitor #{mon}.")

            case Attribute.PWR:
                try:
                    m.set_power_mode(val)
                except:
                    raise MonitorBossError(f"could not set power mode for monitor #{mon}.")

            case _:
                raise MonitorBossError(f"{attr} is not a valid attribute to set.")


def toggle_attribute(mon: int, attr: Attribute, val1: InputSource | PowerMode | int,
                     val2: InputSource | PowerMode | int):
    def toggle(cur, val1, val2):
        return val2 if cur == val1 else val1

    with __get_monitor(mon) as m:
        match attr:
            case Attribute.SRC:
                try:
                    src = m.get_input_source()
                except InputSourceValueError as e:
                    # Some monitors use non-standard codes that are outside of spec.
                    if e.value in input_sources:
                        src = input_sources[e.value]
                    else:
                        raise MonitorBossError(f"input source {e.value} for monitor #{mon} is not a standard value.")
                except:
                    raise MonitorBossError(f"could not get input source for monitor #{mon}.")

                new_val = toggle(src, val1, val2)
                try:
                    m.set_input_source(new_val)
                except:
                    raise MonitorBossError(f"could not set input source for monitor #{mon} to {new_val}.")

            case Attribute.CNT:
                try:
                    cnt = m.get_contrast()
                except:
                    raise MonitorBossError(f"could not get contrast for monitor #{mon}.")

                new_val = toggle(cnt, val1, val2)
                try:
                    m.set_contrast(new_val)
                except:
                    raise MonitorBossError(f"could not set contrast for monitor #{mon} to {new_val}.")

            case Attribute.LUM:
                try:
                    lum = m.get_luminance()
                except:
                    raise MonitorBossError(f"could not get luminance for monitor #{mon}.")

                new_val = toggle(lum, val1, val2)
                try:
                    m.set_luminance(new_val)
                except:
                    raise MonitorBossError(f"could not set luminance for monitor #{mon} to {new_val}.")

            case Attribute.PWR:
                try:
                    pwr = m.get_power_mode()
                except:
                    raise MonitorBossError(f"could not get power mode for monitor #{mon}.")

                new_val = toggle(pwr, val1, val2)
                try:
                    m.set_power_mode(new_val)
                except:
                    raise MonitorBossError(f"could not set power mode for monitor #{mon} to {new_val}.")

            case _:
                raise MonitorBossError(f"{attr} is not a valid attribute to toggle.")
