# see https://github.com/MonitorControl/ for reference/ObjC implementation of ddc/ci on macOS

from __future__ import annotations
from types import TracebackType
from typing import List, Optional, Type, Tuple

from monitorcontrol.vcp import VCPCommand
from monitorcontrol.vcp.vcp_abc import VCP


class MacOSARMVCP(VCP):
    def __init__(self, display_id: int):
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
        self.logger.debug("DestroyPhysicalMonitor")

        return super().__exit__(exception_type, exception_value, exception_traceback)

    def _set_vcp_feature(self, code: VCPCommand, value: int):
        pass

    def _get_vcp_feature(self, code: VCPCommand) -> Tuple[int, int]:
        pass

    def _get_vcp_capabilities_str(self) -> str:
        pass

    @staticmethod
    def get_vcps() -> List[MacOSARMVCP]:
        pass

