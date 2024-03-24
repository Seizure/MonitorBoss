from enum import unique, Enum
from dataclasses import dataclass
from typing import Union, Callable, Any

from monitorcontrol import Monitor


@dataclass
class AttributeData:
    shortdesc: str
    getter: Union[Callable[[Monitor], ...], Any]
    setter: Union[Callable[[Monitor, ...], Any], Any]
    description: str
    notes: str


@unique
class ColorPreset(Enum):
    """Monitor color presets."""

    ct4000 = 0x03
    ct5000 = 0x04
    ct6500 = 0x05
    ct7500 = 0x06
    ct8200 = 0x07
    ct9300 = 0x08
    ct10000 = 0x09
    ct11500 = 0x0A
    ctuser1 = 0x0B
    ctuser2 = 0x0C
    ctuser3 = 0x0D


@unique
class PowerMode(Enum):
    on = 0x01
    standby = 0x02
    suspend = 0x03
    off_soft = 0x04
    off_hard = 0x05


@unique
class InputSource(Enum):
    off = 0x00
    analog1 = 0x01
    analog2 = 0x02
    dvi1 = 0x03
    dvi2 = 0x04
    cmpst1 = 0x05
    cmpst2 = 0x06
    svideo1 = 0x07
    svideo2 = 0x08
    tuner1 = 0x09
    tuner2 = 0x0A
    tuner3 = 0x0B
    cmpnt1 = 0x0C
    cmpnt2 = 0x0D
    cmpnt3 = 0x0E
    dp1 = 0x0F
    dp2 = 0x10
    hdmi1 = 0x11
    hdmi2 = 0x12


class MonitorBossError(Exception):
    def __init__(self, message: str):
        super().__init__(message)