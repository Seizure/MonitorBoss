# pragma: exclude file

from __future__ import annotations

from pyddc.vcp_codes import VCPCommand
from pyddc.vcp_abc import VCP, VCPError, VCPFeatureReturn
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
import winreg


class PhysicalMonitor(ctypes.Structure):
    _fields_ = [("handle", HANDLE), ("description", WCHAR * 128)]

CCHDEVICENAME = 32

class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", DWORD),
        ("szDevice", WCHAR * CCHDEVICENAME),
    ]

class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", DWORD),
        ("DeviceName", WCHAR * 32),
        ("DeviceString", WCHAR * 128),
        ("StateFlags", DWORD),
        ("DeviceID", WCHAR * 128),
        ("DeviceKey", WCHAR * 128),
    ]


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
            #   it does not allow opening and closing of individual physical
            #   monitors without their hmonitors.
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
        del timeout  # unused
        try:
            if not dxva2.SetVCPFeature(HANDLE(self.handle), BYTE(code.code), DWORD(value)):
                raise VCPError(f"failed to set VCP feature: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to close handle") from err

    def _get_vcp_feature(self, com: VCPCommand, timeout: float) -> VCPFeatureReturn:
        del timeout  # unused
        feature_current = DWORD()
        feature_max = DWORD()
        try:
            if not dxva2.GetVCPFeatureAndVCPFeatureReply(
                HANDLE(self.handle),
                BYTE(com.code),
                None,
                ctypes.byref(feature_current),
                ctypes.byref(feature_max),
            ):
                raise VCPError(f"failed to get VCP feature: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to get VCP feature") from err
        self.logger.debug(f"GetVCPFeatureAndVCPFeatureReply -> (cme: {com.code}) | (feature current/max: {feature_current.value} / {feature_max.value})")
        return VCPFeatureReturn(feature_current.value, feature_max.value)

    def _get_vcp_capabilities_str(self, timeout: float) -> str:
        del timeout  # unused
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
        return caps_str.value.decode("ascii")


    def get_edid_from_logical_handle(self) -> bytes:
        """
        Retrieves the raw EDID bytes for a given HMONITOR handle.
        """
        # 1. Get the Logical Device Name (e.g., \\.\DISPLAY1)
        mon_info = MONITORINFOEXW()
        mon_info.cbSize = ctypes.sizeof(MONITORINFOEXW)
        if not ctypes.windll.user32.GetMonitorInfoW(self.hmonitor, ctypes.byref(mon_info)):
            raise VCPError(
                f"HMONITOR handle is invalid. "
                f"HMONITOR: {self.hmonitor} | "
                f"Win32 error: {ctypes.FormatError()}"
            )

        # 2. Get the Hardware Device ID
        # Note: We query the device attached to the monitor name
        display_device = DISPLAY_DEVICEW()
        display_device.cb = ctypes.sizeof(DISPLAY_DEVICEW)

        # We call EnumDisplayDevices for the specific monitor name
        if not ctypes.windll.user32.EnumDisplayDevicesW(mon_info.szDevice, 0, ctypes.byref(display_device), 1):
            raise VCPError(
                f"No physical display device attached to logical display. "
                f"HMONITOR: {self.hmonitor}) | "
                f"logical display: {mon_info.szDevice} | "
                f"Win32 error: {ctypes.FormatError()}"
            )

        # 3. Parse DeviceID into Registry Path
        # DeviceID looks like: MONITOR\GSM5B55\{4d36e96e-e325-11ce-bfc1-08002be10318}\0001
        # We need: DISPLAY\GSM5B55\{4d36e96e-e325-11ce-bfc1-08002be10318}\0001
        device_id = display_device.DeviceID
        if not device_id:
            raise VCPError(
                f"DeviceID is empty. "
                f"HMONITOR: {self.hmonitor}) | "
                f"logical display: {mon_info.szDevice} | "
                f"device: {display_device.DeviceString}"
            )

        # Standardize the path: replace MONITOR\ with DISPLAY\
        # and swap the first two '#' with '\' if the format uses them.
        path_parts = device_id.split('#')
        if len(path_parts) >= 3:
            # Format: MONITOR\PNP000\123456...
            reg_path = f"SYSTEM\\CurrentControlSet\\Enum\\DISPLAY\\{path_parts[1]}\\{path_parts[2]}\\Device Parameters"
        else:
            # Fallback for older drivers or virtual displays
            reg_path = device_id.replace("MONITOR\\", "DISPLAY\\") + "\\Device Parameters"

        # 4. Extract from Registry
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                edid_blob, _ = winreg.QueryValueEx(key, "EDID")
                return bytes(edid_blob)
        except (FileNotFoundError, OSError) as err:
            raise VCPError(f"Could not open registry location for VCP: {err}") from err

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


if __name__ == "__main__":
    vcps = WindowsVCP.get_vcps()
    edids = {}
    for vcp in vcps:
        edids[str(vcp.hmonitor)] = vcp.get_edid_from_logical_handle()

    for hmonitor, edid in edids.items():
        print(f"EDID for {hmonitor}:\n{edid}")