import abc
import ctypes
import dataclasses
import sys
from logging import getLogger
from typing import Any, List, Union, Callable

from pyddc import VCPCommand, VCPError, VCPFeatureReturn


class Handle(abc.ABC):
    @abc.abstractmethod
    def open(self):
        pass

    @abc.abstractmethod
    def close(self):
        pass


@dataclasses.dataclass
class Driver:
    iscompatible: Callable[[], bool]
    get_vcp_capabilities: Callable[[Handle], str]
    get_vcp_feature: Callable[[Handle, VCPCommand], (int, int)]
    set_vcp_feature: Callable[[Handle, VCPCommand, int], None]
    get_vcp_handles: Callable[[], List[Handle]]


##########################
# Code for Windows Driver
##########################


class HandleWindows(Handle):
    from ctypes.wintypes import HMONITOR, HANDLE, WCHAR, DWORD
    dxva2 = ctypes.windll.dxva2

    def __init__(self, hmonitor: HMONITOR):
        self.hmonitor: self.HMONITOR = hmonitor
        self.handle: Union[self.HANDLE, None] = None
        self.description: Union[self.WCHAR * 128, None] = None
        self.logger = getLogger(f"HandleWindows: {hmonitor}")

    def open(self):
        class PhysicalMonitor(ctypes.Structure):
            _fields_ = [("handle", self.HANDLE), ("description", self.WCHAR * 128)]

        num_physical = self.DWORD()
        self.logger.debug("GetNumberOfPhysicalMonitorsFromHMONITOR")
        try:
            if not self.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(self.hmonitor, ctypes.byref(num_physical)):
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
            if not self.dxva2.GetPhysicalMonitorsFromHMONITOR(self.hmonitor, num_physical.value,
                                                              physical_monitors):
                raise VCPError(f"Call to GetPhysicalMonitorsFromHMONITOR failed: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to open physical monitor handle") from err
        self.handle = physical_monitors[0].handle
        self.description = physical_monitors[0].description

    def close(self):
        self.logger.debug("DestroyPhysicalMonitor")
        try:
            if not self.dxva2.DestroyPhysicalMonitor(self.handle):
                raise VCPError(f"Call to DestroyPhysicalMonitor failed: {ctypes.FormatError()}")
        except OSError as err:
            raise VCPError("failed to close handle") from err
        self.handle = None
        self.description = None


logger = getLogger("DriverWindows")


def __windows_iscompatible() -> bool:
    return sys.platform == "win32"


def __windows_get_vcp_capabilities(handle: HandleWindows) -> str:
    dxva2 = ctypes.windll.dxva2
    from ctypes.wintypes import DWORD, HANDLE

    cap_length = DWORD()
    logger.debug("GetCapabilitiesStringLength")
    try:
        if not dxva2.GetCapabilitiesStringLength(HANDLE(handle.handle), ctypes.byref(cap_length)):
            raise VCPError(f"failed to get VCP capabilities: {ctypes.FormatError()}")
        caps_str = (ctypes.c_char * cap_length.value)()
        logger.debug("CapabilitiesRequestAndCapabilitiesReply")
        if not dxva2.CapabilitiesRequestAndCapabilitiesReply(HANDLE(handle.handle), caps_str, cap_length):
            raise VCPError(f"failed to get VCP capabilities: {ctypes.FormatError()}")
    except OSError as err:
        raise VCPError("failed to get VCP capabilities") from err
    return caps_str.value.decode("ascii")


def __windows_get_vcp_feature(handle: HandleWindows, com: VCPCommand) -> (int, int):
    dxva2 = ctypes.windll.dxva2
    from ctypes.wintypes import DWORD, HANDLE, BYTE

    feature_current = DWORD()
    feature_max = DWORD()
    try:
        if not dxva2.GetVCPFeatureAndVCPFeatureReply(
                HANDLE(handle.handle),
                BYTE(com.value),
                None,
                ctypes.byref(feature_current),
                ctypes.byref(feature_max),
        ):
            raise VCPError(f"failed to get VCP feature: {ctypes.FormatError()}")
    except OSError as err:
        raise VCPError("failed to get VCP feature") from err
    logger.debug(f"GetVCPFeatureAndVCPFeatureReply -> ({feature_current.value}, {feature_max.value})")
    return VCPFeatureReturn(feature_current.value, feature_max.value)


def __windows_set_vcp_feature(handle: HandleWindows, com: VCPCommand, value: int):
    dxva2 = ctypes.windll.dxva2
    from ctypes.wintypes import DWORD, HANDLE, BYTE

    try:
        if not dxva2.SetVCPFeature(HANDLE(handle.handle), BYTE(com.value), DWORD(value)):
            raise VCPError(f"failed to set VCP feature: {ctypes.FormatError()}")
    except OSError as err:
        raise VCPError("failed to close handle") from err


def __windows_get_vcp_handles() -> List[HandleWindows]:
    from ctypes.wintypes import BOOL, HMONITOR, HDC

    hmonitors = []
    try:
        def _callback(hmonitor, hdc, lprect, lparam):
            hmonitors.append(HMONITOR(hmonitor))
            del hmonitor, hdc, lprect, lparam
            return True  # continue enumeration

        MONITORENUMPROC = ctypes.WINFUNCTYPE(BOOL, HMONITOR, HDC, ctypes.POINTER(cls.RECT), cls.LPARAM)
        callback = MONITORENUMPROC(_callback)
        if not ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback, 0):
            raise VCPError("Call to EnumDisplayMonitors failed")
    except OSError as err:
        raise VCPError("failed to enumerate VCPs") from err
    return [HandleWindows(logical) for logical in hmonitors]


__windows_driver = Driver(__windows_iscompatible,
                          __windows_get_vcp_capabilities,
                          __windows_get_vcp_feature,
                          __windows_set_vcp_feature,
                          __windows_get_vcp_handles)

##########################
# Code for Linux Driver
##########################


class DriverLinux(Driver):

    @staticmethod
    def iscompatible() -> bool:
        return sys.platform.startswith("linux")

    @staticmethod
    def open(handle) -> Any:
        pass

    @staticmethod
    def close(handle) -> Any:
        pass

    @staticmethod
    def get_vcp_capabilities(handle) -> str:
        pass

    @staticmethod
    def get_vcp_feature(handle, com: VCPCommand) -> (int, int):
        pass

    @staticmethod
    def set_vcp_feature(handle, com: VCPCommand, value: int):
        pass

    @staticmethod
    def get_vcp_handles() -> List:
        pass


drivers = [__windows_driver]
