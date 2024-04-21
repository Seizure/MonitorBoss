from __future__ import annotations

from collections import namedtuple

from pyddc.vcp_codes import VCPCommand
from pyddc.vcp_abc import VCP, VCPError
from types import TracebackType
from typing import List, Optional, Type


supported_codes = {}
supported_codes[4] = [] # factory reset code (WO) TODO: should find a better WO command (with actual values)
supported_codes[16] = None # luminance (RW/continuous)
supported_codes[18] = None # contrast (RW/continuous)
supported_codes[96] = [27, 15, 17] # input source code (RW/discreet); with params for USBC, dp1, and hdm1
supported_codes[170] = [1, 2, 4] # image orientation (RO/discreet); with params for who knows what


internal_values = {16: 75, 96: 27, 170: 2} # lum is 75, input is USBC(27), image orientation is 2 (whatever that means)
internal_max = {16: 80, 18: 100}

class DummyVCP(VCP):
    def __init__(self):
        super().__init__()

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

    def _set_vcp_feature(self, code: VCPCommand, value: int):
        code = VCPCommand.value
        if code in supported_codes:
            if value is not None and value in supported_codes[code]:
                pass
            else:
                # TODO: What happens if an unsupported value is sent? Presumably nothing but should check
                pass
        else:
            # TODO: what should happen when an unsupported VCP command is sent?
            pass

    def _get_vcp_feature(self, code: VCPCommand) -> (int, int):
        code = VCPCommand.value
        if code in supported_codes:
                internal[code] = value
            else:
                # TODO: What happens if an unsupported value is sent? Presumably nothing but should check
                pass
        else:
            # TODO: what should happen when an unsupported VCP command is sent?
            pass

def _get_vcp_capabilities_str(self) -> str:
        # TODO: modify this capability string to mock that of a monitor with very limited MCCS support
        return "(prot(monitor)type(LCD)model(U2422HE)cmds(01 02 03 07 0C E3 F3)vcp(02 04 05 08 10 12 14(01 04 05 06 08 09 0B 0C) 16 18 1A 52 60(1B 0F 11 ) AA(01 02 04 ) AC AE B2 B6 C6 C8 C9 CA CC(02 0A 03 04 08 09 0D 06 ) D6(01 04 05) DC(00 03 05 ) DF E0 E1 E2(00 02 04 0C 0D 0F 10 11 13 0B 1A 14 ) E7(02 03) EA F0(09 ) F1 F2 FD)mswhql(1)asset_eep(40)mccs_ver(2.1))"

    @staticmethod
    def get_vcps() -> List[DummyVCP]:
        return [DummyVCP() for i in range(3)]
