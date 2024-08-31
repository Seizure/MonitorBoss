from dataclasses import dataclass
from enum import IntEnum, unique


@unique
class VCPCodes(IntEnum):
    restore_factory_default = 4  # 0x04
    image_luminance = 16  # 0x10
    image_contrast = 18  # 0x12
    image_color_preset = 20  # 0x14
    active_control = 82  # 0x52
    input_source = 96  # 0x60
    image_orientation = 170  # 0xAA
    display_power_mode = 214  # 0xD6


@unique
class InputSourceNames(IntEnum):
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


@unique
class PowerModeNames(IntEnum):
    on = 0x01
    standby = 0x02
    suspend = 0x03
    off_soft = 0x04
    off_hard = 0x05


@unique
class ColorPresetNames(IntEnum):
    ct4000k = 0x03
    ct5000k = 0x04
    ct6500k = 0x05
    ct7500k = 0x06
    ct8200k = 0x07
    ct9300k = 0x08
    ct10000k = 0x09
    ct11500k = 0x0a
    ctuser1 = 0x0b
    ctuser2 = 0x0c
    ctuser3 = 0x0d


@dataclass(frozen=True)
class VCPCommand:
    name: str
    desc: str
    value: int
    readable: bool
    writeable: bool
    discrete: bool
    param_names: dict

    def __str__(self):
        return f"VCPCommand: {self.name} ({self.value})"


_VCP_COMMANDS = [
    VCPCommand(
        name="restore_factory_default",
        desc="restore factory default image",
        value=VCPCodes.restore_factory_default,
        readable=False,
        writeable=True,
        discrete=True,
        param_names={}),
    VCPCommand(
        name="image_luminance",
        desc="image luminance",
        value=VCPCodes.image_luminance,
        readable=True,
        writeable=True,
        discrete=False,
        param_names={}),
    VCPCommand(
        name="image_contrast",
        desc="image contrast",
        value=VCPCodes.image_contrast,
        readable=True,
        writeable=True,
        discrete=False,
        param_names={}),
    VCPCommand(
        name="image_color_preset",
        desc="image color preset",
        value=VCPCodes.image_color_preset,
        readable=True,
        writeable=True,
        discrete=False,
        param_names=dict(ColorPresetNames.__members__)),
    VCPCommand(
        name="active_control",
        desc="active control",
        value=VCPCodes.active_control,
        readable=True,
        writeable=False,
        discrete=True,
        param_names={}),
    VCPCommand(
        name="input_source",
        desc="input source",
        value=VCPCodes.input_source,
        readable=True,
        writeable=True,
        discrete=True,
        param_names=dict(InputSourceNames.__members__)),
    VCPCommand(
        name="image_orientation",
        desc="image orientation",
        value=VCPCodes.image_orientation,
        readable=True,
        writeable=False,
        discrete=True,
        param_names={}),
    VCPCommand(
        name="display_power_mode",
        desc="display power mode",
        value=VCPCodes.display_power_mode,
        readable=True,
        writeable=False,
        discrete=True,
        param_names=dict(PowerModeNames.__members__)),
]


# TODO: should this just take a VCPCode, now that we're doing it that way? There are some places this
#   would make more awkward (see cli._check_feature) but maybe there's a clever way?
def get_vcp_com(key: str | int) -> VCPCommand | None:
    if not isinstance(key, (int, str)):
        raise TypeError(f"key must be string or int. Got {type(key)}.")
    for com in _VCP_COMMANDS:
        if isinstance(key, str) and com.name == key:
            return com
        elif com.value == key:
            return com
    return None
