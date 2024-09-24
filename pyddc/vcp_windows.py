from __future__ import annotations

from .vcp_codes import VCPCommand
from .vcp_abc import VCP, VCPError, VCPFeatureReturn
from types import TracebackType
from typing import List, Optional, Type
import ctypes
import sys

assert sys.platform == "win32", "This file must be imported only for Windows"

dxva2 = ctypes.windll.dxva2
from ctypes.wintypes import (
    DWORD,
    RECT,
    BOOL,
    HMONITOR,
    HDC,
    LPARAM,
    HANDLE,
    BYTE,
    WCHAR,
)


class PhysicalMonitor(ctypes.Structure):
    _fields_ = [("handle", HANDLE), ("description", WCHAR * 128)]


# references:
# https://stackoverflow.com/questions/16588133/
class WindowsVCP(VCP):
    def __init__(self, hmonitor: HMONITOR):
        super().__init__()
        self.hmonitor = hmonitor

    def __enter__(self):
        super().__enter__()
        num_physical = DWORD()
        self.logger.debug("GetNumberOfPhysicalMonitorsFromHMONITOR")
        try:
            if not dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(self.hmonitor, ctypes.byref(num_physical)):
                raise VCPError(f"Call to GetNumberOfPhysicalMonitorsFromHMONITOR failed: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("Call to GetNumberOfPhysicalMonitorsFromHMONITOR failed") from err
        if num_physical.value == 0:
            raise VCPError("no physical monitor found")
        elif num_physical.value > 1:
            # TODO: Figure out a clever way around the Windows API since
            # it does not allow opening and closing of individual physical
            # monitors without their hmonitors.
            raise VCPError("more than one physical monitor per hmonitor")
        physical_monitors = (PhysicalMonitor * num_physical.value)()
        self.logger.debug("GetPhysicalMonitorsFromHMONITOR")
        try:
            if not dxva2.GetPhysicalMonitorsFromHMONITOR(self.hmonitor, num_physical.value, physical_monitors):
                raise VCPError(f"Call to GetPhysicalMonitorsFromHMONITOR failed: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to open physical monitor handle") from err
        self.handle = physical_monitors[0].handle
        self.description = physical_monitors[0].description
        return self

    def __exit__(
            self,
            exception_type: Optional[Type[BaseException]],
            exception_value: Optional[BaseException],
            exception_traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self.logger.debug("DestroyPhysicalMonitor")
        try:
            if not dxva2.DestroyPhysicalMonitor(self.handle):
                raise VCPError(f"Call to DestroyPhysicalMonitor failed: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to close handle") from err
        return super().__exit__(exception_type, exception_value, exception_traceback)

    def _set_vcp_feature(self, code: VCPCommand, value: int, timeout: float):
        del timeout # unused
        try:
            if not dxva2.SetVCPFeature(HANDLE(self.handle), BYTE(code.code), DWORD(value)):
                raise VCPError(f"failed to set VCP feature: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to close handle") from err

    def _get_vcp_feature(self, code: VCPCommand, timeout: float) -> VCPFeatureReturn:
        del timeout # unused
        feature_current = DWORD()
        feature_max = DWORD()
        try:
            if not dxva2.GetVCPFeatureAndVCPFeatureReply(
                HANDLE(self.handle),
                BYTE(code.code),
                None,
                ctypes.byref(feature_current),
                ctypes.byref(feature_max),
            ):
                raise VCPError(f"failed to get VCP feature: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to get VCP feature") from err
        self.logger.debug(f"GetVCPFeatureAndVCPFeatureReply -> (code: {code.code}) | (feature current/max: {feature_current.value} / {feature_max.value})")
        return VCPFeatureReturn(feature_current.value, feature_max.value)

    def _get_vcp_capabilities_str(self, timeout: float) -> str:
        del timeout # unused
        cap_length = DWORD()
        self.logger.debug("GetCapabilitiesStringLength")
        try:
            if not dxva2.GetCapabilitiesStringLength(HANDLE(self.handle), ctypes.byref(cap_length)):
                raise VCPError(f"failed to get VCP capabilities: {ctypes.FormatError()}")
            caps_str = (ctypes.c_char * cap_length.value)()
            self.logger.debug("CapabilitiesRequestAndCapabilitiesReply")
            if not dxva2.CapabilitiesRequestAndCapabilitiesReply(HANDLE(self.handle), caps_str, cap_length):
                raise VCPError(f"failed to get VCP capabilities: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to get VCP capabilities") from err
        return caps_str.code.decode("ascii")

    @staticmethod
    def get_vcps() -> List[WindowsVCP]:
        hmonitors = []
        try:
            def _callback(hmonitor, hdc, lprect, lparam):
                hmonitors.append(HMONITOR(hmonitor))
                del hmonitor, hdc, lprect, lparam
                return True  # continue enumeration

            MONITORENUMPROC = ctypes.WINFUNCTYPE(BOOL, HMONITOR, HDC, ctypes.POINTER(RECT), LPARAM)
            callback = MONITORENUMPROC(_callback)
            if not ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback, 0):
                raise VCPError("Call to EnumDisplayMonitors failed")
        except OSError as err:
            raise VCPError("failed to enumerate VCPs") from err
        return [WindowsVCP(logical) for logical in hmonitors]
