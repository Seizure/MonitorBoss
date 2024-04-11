# see https://github.com/kfix/ddcctl for reference/ObjC implementation of ddc/ci on macOS

from __future__ import annotations
from types import TracebackType
from typing import List, Optional, Type, Tuple

import AppKit
import Quartz

from monitorcontrol.vcp import VCPCommand
from monitorcontrol.vcp.vcp_abc import VCP


class macOSVCP(VCP):
    def __init__(self, display_id: int):
        super().__init__()
        self.display_id = display_id

    def __enter__(self):
        super().__enter__()

        return self

    def __exit__(
            self,
            exception_type: Optional[Type[BaseException]],
            exception_value: Optional[BaseException],
            exception_traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self.logger.debug("DestroyPhysicalMonitor")

        return super().__exit__(exception_type, exception_value, exception_traceback)

    def _set_vcp_feature(self, code: VCPCommand, value: int):
        pass

    def _get_vcp_feature(self, code: VCPCommand) -> Tuple[int, int]:
        pass

    def _get_vcp_capabilities_str(self) -> str:
        pass

    @staticmethod
    def get_vcps() -> List[macOSVCP]:
        NSScreen = AppKit.NSScreen

        screens = NSScreen.screens()
        vcps = []
        for s in screens:
            screen_desc = s._.deviceDescription
            is_screen = screen_desc.objectForKey_('NSDeviceIsScreen')
            if is_screen == "YES":
                screen_id = screen_desc.objectForKey_("NSScreenNumber").integerValue()
                if not Quartz.CGDisplayIsBuiltin(screen_id):
                    vcps.append(macOSVCP(screen_id))

        return vcps

