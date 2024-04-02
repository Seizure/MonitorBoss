from typing import List, Union
import enum

from .vcp import VCP
from .vcp.vcp_codes import get_vcp_com


@enum.unique
class ColorPreset(enum.Enum):
    COLOR_TEMP_4000K = 0x03
    COLOR_TEMP_5000K = 0x04
    COLOR_TEMP_6500K = 0x05
    COLOR_TEMP_7500K = 0x06
    COLOR_TEMP_8200K = 0x07
    COLOR_TEMP_9300K = 0x08
    COLOR_TEMP_10000K = 0x09
    COLOR_TEMP_11500K = 0x0A
    COLOR_TEMP_USER1 = 0x0B
    COLOR_TEMP_USER2 = 0x0C
    COLOR_TEMP_USER3 = 0x0D


@enum.unique
class PowerMode(enum.Enum):
    on = 0x01
    standby = 0x02
    suspend = 0x03
    off_soft = 0x04
    off_hard = 0x05


@enum.unique
class InputSource(enum.Enum):
    OFF = 0x00
    ANALOG1 = 0x01
    ANALOG2 = 0x02
    DVI1 = 0x03
    DVI2 = 0x04
    COMPOSITE1 = 0x05
    COMPOSITE2 = 0x06
    SVIDEO1 = 0x07
    SVIDEO2 = 0x08
    TUNER1 = 0x09
    TUNER2 = 0x0A
    TUNER3 = 0x0B
    CMPONENT1 = 0x0C
    CMPONENT2 = 0x0D
    CMPONENT3 = 0x0E
    DP1 = 0x0F
    DP2 = 0x10
    HDMI1 = 0x11
    HDMI2 = 0x12


class InputSourceValueError(ValueError):
    def __init__(self, message: str, value: int):
        super().__init__(message)
        self.value = value


def get_luminance(vcp: VCP) -> int:
    code = get_vcp_com("image_luminance")
    return vcp.get_vcp_feature(code)[0]


def set_luminance(vcp: VCP, value: int):
    code = get_vcp_com("image_luminance")
    vcp.set_vcp_feature(code, value)


def get_color_preset(vcp: VCP) -> int:
    code = get_vcp_com("image_color_preset")
    return vcp.get_vcp_feature(code)[0]


def set_color_preset(vcp: VCP, value: Union[int, str, ColorPreset]):
    if isinstance(value, str):
        mode_value = getattr(ColorPreset, value).value
    elif isinstance(value, int):
        mode_value = ColorPreset(value).value
    elif isinstance(value, ColorPreset):
        mode_value = value.value
    else:
        raise TypeError("unsupported color preset: " + repr(type(value)))

    code = get_vcp_com("image_color_preset")
    vcp.set_vcp_feature(code, mode_value)


def get_contrast(vcp: VCP) -> int:
    code = get_vcp_com("image_contrast")
    return vcp.get_vcp_feature(code)[0]


def set_contrast(vcp: VCP, value: int):
    code = get_vcp_com("image_contrast")
    vcp.set_vcp_feature(code, value)


def get_power_mode(vcp: VCP) -> PowerMode:
    code = get_vcp_com("display_power_mode")
    return PowerMode(vcp.get_vcp_feature(code)[0])


def set_power_mode(vcp: VCP, value: Union[int, str, PowerMode]):
    if isinstance(value, str):
        mode_value = getattr(PowerMode, value).value
    elif isinstance(value, int):
        mode_value = PowerMode(value).value
    elif isinstance(value, PowerMode):
        mode_value = value.value
    else:
        raise TypeError("unsupported mode type: " + repr(type(value)))

    code = get_vcp_com("display_power_mode")
    vcp.set_vcp_feature(code, mode_value)


def get_input_source(vcp: VCP) -> InputSource:
    code = get_vcp_com("input_select")
    value = vcp.get_vcp_feature(code)[0] & 0xFF
    try:
        return InputSource(value)
    except ValueError:
        raise InputSourceValueError(f"{value} is not a valid InputSource", value)


def set_input_source(vcp: VCP, value: Union[int, str, InputSource]):
    if isinstance(value, str):
        mode_value = getattr(InputSource, value.upper()).value
    elif isinstance(value, int):
        mode_value = value
    elif isinstance(value, InputSource):
        mode_value = value.value
    else:
        raise TypeError("unsupported input type: " + repr(type(value)))

    code = get_vcp_com("input_select")
    vcp.set_vcp_feature(code, mode_value)


def get_capabilities(vcp: VCP) -> dict:
    return vcp.get_vcp_capabilities()


def get_vcps() -> List[VCP]:
    return VCP.get_vcps()
