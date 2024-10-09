from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import List, Optional, Type
from copy import deepcopy

from pyddc import VCPCommand, VCPFeatureReturn, ABCVCP, VCPError
from pyddc.vcp_codes import VCPCodes, get_vcp_com


@dataclass
class SupportedCodeTemplate:
    code: int
    supported_params: list[int] | None
    initial_value: int | None
    max_value: int | None

    def __post_init__(self):
        com = get_vcp_com(self.code)
        if com:
            if com.discrete and self.supported_params is None:
                raise ValueError(f"Feature {self.code}/{com} is known to be discrete, supported_params can not be 'None'")
            elif not com.discrete and self.supported_params is not None:
                raise ValueError(f"Feature {self.code}/{com} is known to be continuous, supported_params must be 'None'")
            if not com.readable and self.initial_value is not None:
                raise ValueError(f"Feature {self.code}/{com} is known to be write-only, initial_value must be 'None'")
            elif com.readable and self.initial_value is None:
                raise ValueError(f"Feature {self.code}/{com} is known to be readable, initial_value can not be 'None'")

        if self.max_value is None:
            if self.supported_params is None:
                raise ValueError(f"Feature {self.code}: supported_params is 'None', implying a continuous feature, but max_value was 'None'")
            if self.initial_value and self.initial_value not in self.supported_params:
                raise ValueError(f"Feature {self.code}: initial_value ({self.initial_value}) not in params ({self.supported_params})")
        else:
            if self.supported_params is not None:
                raise ValueError(f"Feature {self.code}: supported_params is not 'None', implying a discrete feature, but max_value was not 'None'")
            if isinstance(self.initial_value, int) and self.initial_value > self.max_value:
                raise ValueError(f"Feature {self.code}: initial_value is greater than max_value on a continuous, readable feature")


class VCPTemplate:
    supported_codes: dict[int, list[int] | None] = {}
    current_values: dict[int, int] = {}
    unknown_max_values: dict[int, int] = {}
    caps_str: str
    faulty: bool  # for tests where you want the VCP operations to fail with a VCPError

    def __init__(self, supported_codes: list[SupportedCodeTemplate], caps_str: str, faulty: bool):
        for code in supported_codes:
            self.supported_codes[code.code] = code.supported_params
            self.current_values[code.code] = code.initial_value
            if code.max_value:
                self.unknown_max_values[code.code] = code.max_value
        self.caps_str = caps_str
        self.faulty = faulty


DEFAULT_VCP_TEMPLATE = VCPTemplate(
    [
        SupportedCodeTemplate(VCPCodes.restore_factory_default.value, [], None, None),
        SupportedCodeTemplate(VCPCodes.image_luminance.value, None, 75, 80),
        SupportedCodeTemplate(VCPCodes.image_contrast.value, None, 75, 100),
        SupportedCodeTemplate(VCPCodes.input_source, [27, 15, 17, 257], 257, None),
        SupportedCodeTemplate(VCPCodes.image_orientation.value, [1, 2, 4], 2, None),
    ],
    "(prot(monitor)type(LCD)model(DUMM13)cmds(04)vcp(10 12 60(1B 0F 11 ) AA(01 02 04 ) )mccs_ver(2.1))",
    False
)


vcp_template_list: list[VCPTemplate] = [DEFAULT_VCP_TEMPLATE, DEFAULT_VCP_TEMPLATE, DEFAULT_VCP_TEMPLATE]


class DummyVCP(ABCVCP):
    def __init__(self, template: VCPTemplate):
        super().__init__()
        self.supported_codes = deepcopy(template.supported_codes)
        self.current_values = template.current_values.copy()
        self.unknown_max_values = template.unknown_max_values.copy()
        self.caps_str = template.caps_str
        self.faulty = template.faulty

    def __enter__(self):
        super().__enter__()

        return self

    def __exit__(
            self,
            exception_type: Optional[Type[BaseException]],
            exception_value: Optional[BaseException],
            exception_traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        return super().__exit__(exception_type, exception_value, exception_traceback)

    def _set_vcp_feature(self, com: VCPCommand, value: int, timeout: float):
        del timeout  # unused
        if self.faulty:
            raise VCPError("I am a broken monitor, beep boop")
        code = com.code
        if code not in self.supported_codes:  # pragma: no cover - not testable in practice
            # This is not defined behavior in practice, some monitors don't complain.
            # Therefor it is probably not worth testing against this result.
            # Also note you would not actually receive an explicit explanation in the wild.
            raise VCPError("The monitor does not support the specified VCP code.")
        if not com.discrete:
            # VCPABC already checks for max values, we don't need to here
            self.current_values[code] = value
        else:  # pragma: no cover - tautological code / not testable in practice
            if value in self.supported_codes[code]:
                # this is just for the sake of proper implementation, but no point testing it
                self.current_values[code] = value
            else:
                # This is not defined behavior in practice, some monitors don't complain.
                # Therefor it is probably not worth testing against this result.
                # Also note you would not actually receive an explicit explanation in the wild.
                raise VCPError("The monitor does not support the specified VCP code.")

    def _get_vcp_feature(self, com: VCPCommand, timeout: float) -> (int, int):
        del timeout  # unused
        if self.faulty:
            raise VCPError("I am a broken monitor, beep boop")
        code = com.code
        if code not in self.supported_codes:  # pragma: no cover
            # This is not defined behavior in practice, some monitors don't complain and just return garbage.
            # Therefor it is probably not worth testing against this result.
            # Also note you would not actually receive an explicit explanation in the wild.
            raise VCPError("The monitor does not support the specified VCP code.")
        if not com.discrete:
            maxv = self.unknown_max_values[code]
        else:
            # The max value on discrete features is the number of options, but
            # there's nothing meaningful to test in that regard
            maxv = len(self.supported_codes[code])
        return VCPFeatureReturn(self.current_values[code], maxv)

    def _get_vcp_capabilities_str(self, timeout: float) -> str:
        del timeout  # unused
        if self.faulty:
            raise VCPError("I am a broken monitor, beep boop")
        return self.caps_str

    @staticmethod
    def get_vcps() -> List[DummyVCP]:
        return[DummyVCP(template) for template in vcp_template_list]
