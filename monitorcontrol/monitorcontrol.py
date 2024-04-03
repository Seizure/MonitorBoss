from typing import List, Union
import enum

from .vcp import VCP
from .vcp.vcp_codes import get_vcp_com


@enum.unique
class ColorPreset(enum.Enum):
    color_temp_4000k = 0x03
    color_temp_5000k = 0x04
    color_temp_6500k = 0x05
    color_temp_7500k = 0x06
    color_temp_8200k = 0x07
    color_temp_9300k = 0x08
    color_temp_10000k = 0x09
    color_temp_11500k = 0x0a
    color_temp_user1 = 0x0b
    color_temp_user2 = 0x0c
    color_temp_user3 = 0x0d


@enum.unique
class PowerMode(enum.Enum):
    on = 0x01
    standby = 0x02
    suspend = 0x03
    off_soft = 0x04
    off_hard = 0x05


@enum.unique
class InputSource(enum.Enum):
    off = 0x00
    analog1 = 0x01
    analog2 = 0x02
    dvi1 = 0x03
    dvi2 = 0x04
    composite1 = 0x05
    composite2 = 0x06
    svideo1 = 0x07
    svideo2 = 0x08
    tuner1 = 0x09
    tuner2 = 0x0a
    tuner3 = 0x0b
    cmponent1 = 0x0c
    cmponent2 = 0x0d
    cmponent3 = 0x0e
    dp1 = 0x0f
    dp2 = 0x10
    hdmi1 = 0x11
    hdmi2 = 0x12


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
        mode_value = getattr(InputSource, value).value
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
