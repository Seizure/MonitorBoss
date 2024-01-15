
import sys
from enum import Enum

import monitorcontrol
from monitorcontrol import get_monitors, InputSource, Monitor, VCPError
from monitorcontrol.monitorcontrol import InputSourceValueError


class Attribute(Enum):
    SRC = "SRC"
    CNT = "CNT"
    LUM = "LUM"
    PWR = "PWR"
    VCP = "VCP"


# for some dumbass reason the author of monitorcontrol made his enums use different case.
# We'll wrap around his and normalize it here.
# TODO: but we can can also probably just do case changes on both ends, not just one, and get rid of this; casefold()
class PowerMode(Enum):
    ON = monitorcontrol.PowerMode.on
    STANDBY = monitorcontrol.PowerMode.standby
    SUSPEND = monitorcontrol.PowerMode.suspend
    OFF_SOFT = monitorcontrol.PowerMode.off_soft
    OFF_HARD = monitorcontrol.PowerMode.off_hard


def __get_monitor_by_index(i: int) -> Monitor:
    return get_monitors()[i]


def get_attribute(mon: int, attr: Attribute) -> str | int | dict:
    print(f'get_attribute(mon={mon}, attr={attr}')
    m = __get_monitor_by_index(mon)

    with m:
        match attr:
            case Attribute.SRC:
                try:
                    return m.get_input_source().name
                except InputSourceValueError as e:
                    return e.value
                # except VCPError:
                #     print('error while getting input source', file=sys.stderr)
                #     return None

            case Attribute.CNT:
                return m.get_contrast()
            case Attribute.LUM:
                return m.get_luminance()
            case Attribute.PWR:
                return m.get_power_mode().name
            case Attribute.VCP:
                return m.get_vcp_capabilities()
            case _:
                raise Exception(f"{attr} is not a valid attribute.")


def set_attribute(mon: int, attr: Attribute, val: InputSource | PowerMode | int):
    print(f'set_attribute(mon={mon}, attr={attr}, val={val}')
    # TODO run a get after to see if it worked, and throw an error if not?
    m = __get_monitor_by_index(mon)

    with m:
        match attr:
            case Attribute.SRC:
                m.set_input_source(val)
            case Attribute.CNT:
                m.set_contrast(val)
            case Attribute.LUM:
                m.set_luminance(val)
            case Attribute.PWR:
                m.set_power_mode(val)
            case _:
                raise Exception(f"{attr} is not a valid attribute.")


def toggle_attribute(mon: int, attr: Attribute, val1: InputSource | PowerMode | int, val2: InputSource | PowerMode | int):
    print(f'toggle_attribute(mon={mon}, attr={attr}, val1={val1}, val2={val2}')
    m = __get_monitor_by_index(mon)

    with m:
        match attr:
            case Attribute.SRC:
                # Some monitors use non-standard codes that are outside of spec. If they do, monitorcontrol throws an error. So we need to catch that.
                # TODO: Maybe there's a cleaner way to do this? Is it possible to scan a monitor's sources and cross-check them somehow?
                try:
                    src = m.get_input_source()
                except InputSourceValueError as e:
                    src = e.value
                    if src == 27:  # 27 is the (non-spec) USB-C source on my Dell monitor. No idea how consistent this is
                        src = InputSource.DP2  # DP2, which is a standard spec source, seems to be an alias for the USB-C source on my monitor. No idea how consistent this is either
                    else:
                        raise Exception(f"{src} is not a known source ID. Sorry bud")
                # except VCPError:
                #     print('error while getting input source', file=sys.stderr)
                #     return None
                # print(f"current source = {src}")
                # print(f'toggle between {val1} and {val2}')
                new_val = val1 if src == val2 else val2 if src == val1 else val1
                # print(f'setting source to {new_val}')
                return m.set_input_source(new_val)
            case Attribute.CNT:
                cnt = m.get_contrast()
                return m.set_contrast(val1 if cnt == val2 else val2 if cnt == val1 else val1)
            case Attribute.LUM:
                lum = m.get_luminance()
                return m.set_luminance(val1 if lum == val2 else val2 if lum == val1 else val1)
            case Attribute.PWR:
                pwr = m.get_power_mode()
                return m.set_power_mode(val1 if pwr == val2 else val2 if pwr == val1 else val1)
            case _:
                raise Exception(f"{attr} is not a valid attribute.")
