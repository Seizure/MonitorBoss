import enum
from dataclasses import dataclass
from enum import Enum, unique


@enum.unique
class InputSourceNames(enum.Enum):
    off = 0x00,
    analog1 = 0x01,
    analog2 = 0x02,
    dvi1 = 0x03,
    dvi2 = 0x04,
    composite1 = 0x05,
    composite2 = 0x06,
    svideo1 = 0x07,
    svideo2 = 0x08,
    tuner1 = 0x09,
    tuner2 = 0x0a,
    tuner3 = 0x0b,
    cmponent1 = 0x0c,
    cmponent2 = 0x0d,
    cmponent3 = 0x0e,
    dp1 = 0x0f,
    dp2 = 0x10,
    hdmi1 = 0x11,
    hdmi2 = 0x12


@enum.unique
class PowerModeNames(enum.Enum):
    on = 0x01,
    standby = 0x02,
    suspend = 0x03,
    off_soft = 0x04,
    off_hard = 0x05


@enum.unique
class ColorPresetNames(enum.Enum):
    ct4000k = 0x03,
    ct5000k = 0x04,
    ct6500k = 0x05,
    ct7500k = 0x06,
    ct8200k = 0x07,
    ct9300k = 0x08,
    ct10000k = 0x09,
    ct11500k = 0x0a,
    ctuser1 = 0x0b,
    ctuser2 = 0x0c,
    ctuser3 = 0x0d


@unique
class ComType(Enum):
    ro = "ro"
    wo = "wo"
    rw = "rw"


@dataclass(frozen=True)
class VCPCommand:
    name: str
    desc: str
    value: int
    readable: bool
    writeable: bool
    discreet: bool
    param_names: dict | None



__VCP_COMMANDS = [
    VCPCommand(
        name="restore_factory_default",
        desc="restore factory default image",
        value=0x04,
        readable=False,
        writeable=True,
        discreet=True,
        param_names=None),
    VCPCommand(
        name="image_luminance",
        desc="image luminance",
        value=0x10,
        readable=True,
        writeable=True,
        discreet=False,
        param_names=None),
    VCPCommand(
        name="image_contrast",
        desc="image contrast",
        value=0x12,
        readable=True,
        writeable=True,
        discreet=False,
        param_names=None),
    VCPCommand(
        name="image_color_preset",
        desc="image color preset",
        value=0x14,
        readable=True,
        writeable=True,
        discreet=False,
        param_names=dict(ColorPresetNames.__members__)),
    VCPCommand(
        name="active_control",
        desc="active control",
        value=0x52,
        readable=True,
        writeable=False,
        discreet=True,
        param_names=None),
    VCPCommand(
        name="input_select",
        desc="input select",
        value=0x60,
        readable=True,
        writeable=True,
        discreet=True,
        param_names=dict(InputSourceNames.__members__)),
    VCPCommand(
        name="image_orientation",
        desc="image orientation",
        value=0xAA,
        readable=True,
        writeable=False,
        discreet=True,
        param_names=None),
    VCPCommand(
        name="display_power_mode",
        desc="display power mode",
        value=0xD6,
        readable=True,
        writeable=False,
        discreet=True,
        param_names=dict(PowerModeNames.__members__)),
]


def get_vcp_com(key: str | int) -> VCPCommand:
    if not (isinstance(key, str) or isinstance(key, int)):
        raise TypeError(f"key must be string or int. Got {type(key)}.")
    for com in __VCP_COMMANDS:
        if isinstance(key, str) and com.name == key:
            return com
        elif com.value == key:
            return com
    raise LookupError(f"No VCP code matched key: {key}")


def create_vcp_com(name: str, desc: str, value: int, com_type: ComType, discreet: bool):
    for com in __VCP_COMMANDS:
        if name == com.name:
            raise ValueError(f"VCP code with name {name} already exists")
        if value == com.value:
            raise ValueError(f"VCP code with value {value} already exists")
    return VCPCommand(name, desc, value, com_type, discreet)

