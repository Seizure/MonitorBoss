from dataclasses import dataclass
from enum import Enum
from time import sleep

from monitorcontrol import VCP, VCPCommand, get_vcp_com

from monitorboss import MonitorBossError
from monitorboss.config import get_config


# def get_input_source(monitor: VCP) -> int:
#     try:
#         input_source_com = get_vcp_com(0x60)
#         return monitor.get_vcp_feature(input_source_com)[0]
#     except InputSourceValueError as err:
#         # Some monitors use non-standard codes that are outside of spec.
#         return err.value


@dataclass
class AttributeData:
    short_desc: str
    com: VCPCommand
    description: str
    notes: str


class Attribute(Enum):
    src = AttributeData("input source", get_vcp_com(0x60),
                        "(currently active) input source",
                        "Must be a valid source ID, or alias as defined by the application built-ins or config file additions")
    cnt = AttributeData("contrast", get_vcp_com(0x12),
                        "contrast",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    lum = AttributeData("luminance", get_vcp_com(0x10),
                        "luminance/brightness",
                        "Must be an integer, though valid values will be constrained between 0 - 100 on most monitors")
    pwr = AttributeData("power mode", get_vcp_com(0xD6),
                        "power mode/state",
                        "Must be a valid power state, as defined by built-in aliases")
    clr = AttributeData("color preset", get_vcp_com(0x14),
                        "(currently active) color preset",
                        "Must be a valid color temperature preset, as defined by built-in aliases")

    def __str__(self):
        return self.name


def list_monitors() -> list[VCP]:
    try:
        return VCP.get_vcps()
    except Exception as err:
        raise MonitorBossError(f"could not list monitors; are you using a laptop?") from err


def __get_monitor(index: int) -> VCP:
    monitors = list_monitors()
    try:
        return monitors[index]
    except IndexError as err:
        raise MonitorBossError(f"monitor #{index} does not exist.") from err


def get_vcp_capabilities(mon: int) -> dict:
    with __get_monitor(mon) as monitor:
        return monitor.get_vcp_capabilities()


def get_attribute(mon: int, attr: Attribute) -> (int, int):
    with __get_monitor(mon) as monitor:
        com = attr.value.com
        if not com.readable:
            raise MonitorBossError(f"'{attr.value.short_desc}' attribute is not readable.")
        try:
            return monitor.get_vcp_feature(com)
        except Exception as err:
            raise MonitorBossError(f"could not get {attr.value.short_desc} for monitor #{mon}.") from err


def set_attribute(mons: int | list[int], attr: Attribute, val: int) -> int:
    if isinstance(mons, int):
        mons = [mons]
    com = attr.value.com

    for mon in mons:
        with __get_monitor(mon) as monitor:
            if not com.writeable:
                raise MonitorBossError(f"`{attr.value.short_desc}` attribute is not writeable.")
            try:
                monitor.set_vcp_feature(com, val)
            except Exception as err:
                raise MonitorBossError(f"could not set {attr.value.short_desc} for monitor #{mon} to {val}.") from err
            # TODO: make this return val from a getter, it didn't work when we first tried this
            return val


def toggle_attribute(mons: int | list[int], attr: Attribute, val1: int, val2: int) -> int:
    if isinstance(mons, int):
        mons = [mons]
    com = attr.value.com

    for mon in mons:
        if not (com.readable and com.writeable):
            raise MonitorBossError(f"'{attr.value.short_desc}' attribute is not both readable and writeable.")
        try:
            cur_val = get_attribute(mon, attr)[0]
        except Exception as err:
            raise MonitorBossError(f"could not get current {attr.value.short_desc} for monitor #{mon}.") from err
        new_val = val2 if cur_val == val1 else val1
        try:
            set_attribute(mon, attr, new_val)
        except Exception as err:
            raise MonitorBossError(
                f"could not toggle {attr.value.short_desc} for monitor #{mon} to {new_val}.") from err
        return new_val


def signal_monitor(mon: int):
    cfg = get_config()
    wait = cfg.wait_time
    with __get_monitor(mon) as monitor:
        cur_lum, max_lum = get_attribute(mon, Attribute.lum)
        sleep(wait)
        set_attribute(mon, Attribute.lum, max_lum)
        sleep(wait)
        set_attribute(mon, Attribute.lum, 0)
        sleep(wait)
        set_attribute(mon, Attribute.lum, cur_lum)
