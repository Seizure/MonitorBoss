from dataclasses import dataclass
from enum import Enum, unique
from typing import Union


@unique
class ComType(Enum):
    ro = "ro"
    wo = "wo"
    rw = "rw"


@dataclass(frozen=True)
class VPCCommand:
    name: str
    desc: str
    value: int
    type: ComType
    discreet: bool

    def readable(self) -> bool:
        return 'r' in self.type.value

    def writeable(self) -> bool:
        return 'w' in self.type.value


__VCP_COMMANDS = [
    VPCCommand(
        name="image_factory_default",
        desc="restore factory default image",
        value=0x04,
        type=ComType.wo,
        discreet=True),
    VPCCommand(
        name="image_luminance",
        desc="image luminance",
        value=0x10,
        type=ComType.rw,
        discreet=False),
    VPCCommand(
        name="image_contrast",
        desc="image contrast",
        value=0x12,
        type=ComType.rw,
        discreet=False),
    VPCCommand(
        name="image_color_preset",
        desc="image color preset",
        value=0x14,
        type=ComType.rw,
        discreet=False),
    VPCCommand(
        name="active_control",
        desc="active control",
        value=0x52,
        type=ComType.ro,
        discreet=True),
    VPCCommand(
        name="input_select",
        desc="input select",
        value=0x60,
        type=ComType.rw,
        discreet=True),
    VPCCommand(
        name="image_orientation",
        desc="image orientation",
        value=0xAA,
        type=ComType.ro,
        discreet=True),
    VPCCommand(
        name="display_power_mode",
        desc="display power mode",
        value=0xD6,
        type=ComType.rw,
        discreet=True),
]


def get_vcp_com(key: Union[str, int]) -> VPCCommand:
    if not (isinstance(key, str) or isinstance(key, int)):
        raise TypeError(f"key must be string or int. Got {type(key)}.")
    for com in __VCP_COMMANDS:
        if isinstance(key, str) and com.name == key:
            return com
        elif com.value == key:
            return com
    raise LookupError(f"No VCP code matched key: {key}")


def add_vcp_com(newcom: VPCCommand):
    for com in __VCP_COMMANDS:
        if newcom.name == com.name:
            raise ValueError(f"VCP code with name {newcom.name} already exists")
        if newcom.value == com.value:
            raise ValueError(f"VCP code with value {newcom.value} already exists")

    __VCP_COMMANDS.append(newcom)