from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType
from typing import List, Optional, Type
from copy import deepcopy

from pyddc import VCPCommand, VCPFeatureReturn, ABCVCP, VCPError
from pyddc.vcp_codes import VCPCodes


@dataclass
class VCPTemplate:
    supported_codes: dict[int, list[int] | None]
    current_values: dict[int, int]
    unknown_max_values: dict[int, int]
    caps_str: str
    faulty: bool  # for tests where you want the VCP operations to fail with a VCPError

    def __post_init__(self):
        pass


DEFAULT_VCP_TEMPLATE = VCPTemplate({
            VCPCodes.restore_factory_default.value: [],  # factory reset code (WO) TODO: should find a better WO command (with actual values)
            VCPCodes.image_luminance.value: None,  # luminance (RW/continuous)
            VCPCodes.image_contrast.value: None,  # contrast (RW/continuous)
            VCPCodes.input_source.value: [27, 15, 17, 257],  # input source code (RW/discreet); with params for USBC, dp1, and hdm1
            VCPCodes.image_orientation.value: [1, 2, 4]  # image orientation (RO/discreet); with params for who knows what
        },
        {VCPCodes.image_luminance.value: 75, VCPCodes.image_contrast.value: 75, VCPCodes.input_source.value: 257, VCPCodes.image_orientation.value: 2},  # input is 1 (analog) with high byte set)
        {VCPCodes.image_luminance.value: 80, VCPCodes.image_contrast.value: 100},
        "(prot(monitor)type(LCD)model(DUMM13)cmds(04)vcp(10 12 60(1B 0F 11 ) AA(01 02 04 ) )mccs_ver(2.1))",
        False)


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
