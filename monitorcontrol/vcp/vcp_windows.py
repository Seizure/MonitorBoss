from __future__ import annotations
from .vcp_codes import VPCCommand
from .vcp_abc import VCP, VCPError
from types import TracebackType
from typing import List, Optional, Tuple, Type
import ctypes
import logging
import sys

from .vcp_codes import get_vcp_com

# hide the Windows code from Linux CI coverage
if sys.platform == "win32":
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

    # structure type for a physical monitor
    class PhysicalMonitor(ctypes.Structure):
        _fields_ = [("handle", HANDLE), ("description", WCHAR * 128)]

    class WindowsVCP(VCP):
        """
        Windows API access to a monitor's virtual control panel.

        References:
            https://stackoverflow.com/questions/16588133/
        """

        def __init__(self, hmonitor: HMONITOR):
            """
            Args:
                hmonitor: logical monitor handle
            """
            super().__init__()
            self.hmonitor = hmonitor

        def __enter__(self):
            super().__enter__()
            num_physical = DWORD()
            self.logger.debug("GetNumberOfPhysicalMonitorsFromHMONITOR")
            try:
                if not ctypes.windll.dxva2.GetNumberOfPhysicalMonitorsFromHMONITOR(
                    self.hmonitor, ctypes.byref(num_physical)
                ):
                    raise VCPError(
                        "Call to GetNumberOfPhysicalMonitorsFromHMONITOR failed: "
                        + ctypes.FormatError()
                    )
            except OSError as e:
                raise VCPError(
                    "Call to GetNumberOfPhysicalMonitorsFromHMONITOR failed"
                ) from e

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
                if not ctypes.windll.dxva2.GetPhysicalMonitorsFromHMONITOR(
                    self.hmonitor, num_physical.value, physical_monitors
                ):
                    raise VCPError(
                        "Call to GetPhysicalMonitorsFromHMONITOR failed: "
                        + ctypes.FormatError()
                    )
            except OSError as e:
                raise VCPError("failed to open physical monitor handle") from e
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
                if not ctypes.windll.dxva2.DestroyPhysicalMonitor(self.handle):
                    raise VCPError(
                        "Call to DestroyPhysicalMonitor failed: " + ctypes.FormatError()
                    )
            except OSError as e:
                raise VCPError("failed to close handle") from e

            return super().__exit__(exception_type, exception_value, exception_traceback)

        def set_vcp_feature(self, code: VPCCommand, value: int):
            """
            Sets the value of a feature on the virtual control panel.

            Args:
                code: Feature code.
                value: Feature value.

            Raises:
                VCPError: Failed to set VCP feature.
            """

            assert self._in_ctx, "This function must be run within the context manager"
            if not code.writeable():
                raise TypeError(f"cannot write read-only code: {code.name}")
            elif code.readable() and code.discreet == False:
                maximum = self._get_code_maximum(code)
                if value > maximum:
                    raise ValueError(f"value of {value} exceeds code maximum of {maximum} for {code.name}")

            self.logger.debug(f"SetVCPFeature(_, {code.name=}, {value=})")
            try:
                if not ctypes.windll.dxva2.SetVCPFeature(
                    HANDLE(self.handle), BYTE(code.value), DWORD(value)
                ):
                    raise VCPError("failed to set VCP feature: " + ctypes.FormatError())
            except OSError as e:
                raise VCPError("failed to close handle") from e

        def get_vcp_feature(self, code: VPCCommand) -> Tuple[int, int]:
            """
            Gets the value of a feature from the virtual control panel.

            Args:
                code: Feature code.

            Returns:
                Current feature value, maximum feature value.

            Raises:
                VCPError: Failed to get VCP feature.
            """

            assert self._in_ctx, "This function must be run within the context manager"
            if not code.readable():
                raise TypeError(f"cannot read write-only code: {code.name}")

            feature_current = DWORD()
            feature_max = DWORD()
            self.logger.debug(
                f"GetVCPFeatureAndVCPFeatureReply(_, {code.name=}, None, _, _)"
            )
            try:
                if not ctypes.windll.dxva2.GetVCPFeatureAndVCPFeatureReply(
                    HANDLE(self.handle),
                    BYTE(code.value),
                    None,
                    ctypes.byref(feature_current),
                    ctypes.byref(feature_max),
                ):
                    raise VCPError("failed to get VCP feature: " + ctypes.FormatError())
            except OSError as e:
                raise VCPError("failed to get VCP feature") from e
            self.logger.debug(
                "GetVCPFeatureAndVCPFeatureReply -> "
                f"({feature_current.value}, {feature_max.value})"
            )
            return feature_current.value, feature_max.value

        def get_vcp_capabilities(self) -> dict:
            """
            Gets capabilities string from the virtual control panel

            Returns:
                One long capabilities string in the format:
                "(prot(monitor)type(LCD)model(ACER VG271U)cmds(01 02 03 07 0C)"

                No error checking for the string being valid. String can have
                bit errors or dropped characters.

            Raises:
                VCPError: Failed to get VCP feature.
            """

            assert self._in_ctx, "This function must be run within the context manager"

            cap_length = DWORD()
            self.logger.debug("GetCapabilitiesStringLength")
            try:
                if not ctypes.windll.dxva2.GetCapabilitiesStringLength(
                    HANDLE(self.handle), ctypes.byref(cap_length)
                ):
                    raise VCPError(
                        "failed to get VCP capabilities: " + ctypes.FormatError()
                    )
                cap_string = (ctypes.c_char * cap_length.value)()
                self.logger.debug("CapabilitiesRequestAndCapabilitiesReply")
                if not ctypes.windll.dxva2.CapabilitiesRequestAndCapabilitiesReply(
                    HANDLE(self.handle), cap_string, cap_length
                ):
                    raise VCPError(
                        "failed to get VCP capabilities: " + ctypes.FormatError()
                    )
            except OSError as e:
                raise VCPError("failed to get VCP capabilities") from e
            return _parse_capabilities(cap_string.value.decode("ascii"))

        @staticmethod
        def get_vcps() -> List[WindowsVCP]:
            """
            Opens handles to all physical VCPs.

            Returns:
                List of all VCPs detected.

            Raises:
                VCPError: Failed to enumerate VCPs.
            """
            vcps = []
            hmonitors = []

            try:

                def _callback(hmonitor, hdc, lprect, lparam):
                    hmonitors.append(HMONITOR(hmonitor))
                    del hmonitor, hdc, lprect, lparam
                    return True  # continue enumeration

                MONITORENUMPROC = ctypes.WINFUNCTYPE(  # noqa: N806
                    BOOL, HMONITOR, HDC, ctypes.POINTER(RECT), LPARAM
                )
                callback = MONITORENUMPROC(_callback)
                if not ctypes.windll.user32.EnumDisplayMonitors(0, 0, callback, 0):
                    raise VCPError("Call to EnumDisplayMonitors failed")
            except OSError as e:
                raise VCPError("failed to enumerate VCPs") from e

            for logical in hmonitors:
                vcps.append(WindowsVCP(logical))

            return vcps


    def _extract_a_cap(caps_str: str, key: str) -> str:
        """
        Splits the capabilities string into individual sets.

        Returns:
            Dict of all values for the capability
        """
        start_of_filter = caps_str.upper().find(key.upper())

        if start_of_filter == -1:
            # not all keys are returned by monitor.
            # Also, sometimes the string has errors.
            return ""

        start_of_filter += len(key)
        filtered_caps_str = caps_str[start_of_filter:]
        end_of_filter = 0
        for i in range(len(filtered_caps_str)):
            if filtered_caps_str[i] == "(":
                end_of_filter += 1
            if filtered_caps_str[i] == ")":
                end_of_filter -= 1
            if end_of_filter == 0:
                # don't change end_of_filter to remove the closing ")"
                break

        # 1:i to remove the first character "("
        return filtered_caps_str[1:i]


    def _convert_to_dict(caps_str: str) -> dict:
        """
        Parses the VCP capabilities string to a dictionary.
        Non-continuous capabilities will include an array of
        all supported values.

        Returns:
            Dict with all capabilities in hex

        Example:
            Expected string "04 14(05 06) 16" is converted to::

                {
                    0x04: {},
                    0x14: {0x05: {}, 0x06: {}},
                    0x16: {},
                }
        """

        if len(caps_str) == 0:
            # Sometimes the keys aren't found and the extracting of
            # capabilities returns an empty string.
            return {}

        result_dict = {}
        group = []
        prev_val = None
        for chunk in caps_str.replace("(", " ( ").replace(")", " ) ").split(" "):
            if chunk == "":
                continue
            elif chunk == "(":
                group.append(prev_val)
            elif chunk == ")":
                group.pop(-1)
            else:
                val = int(chunk, 16)
                if len(group) == 0:
                    result_dict[val] = {}
                else:
                    d = result_dict
                    for g in group:
                        d = d[g]
                    d[val] = {}
                prev_val = val

        return result_dict


    def _parse_capabilities(caps_str: str) -> dict:
        """
        Converts the capabilities string into a nice dict
        """
        caps_dict = {
            # Used to specify the protocol class
            "prot": "",
            # Identifies the type of display
            "type": "",
            # The display model number
            "model": "",
            # A list of supported VCP codes. Somehow not the same as "vcp"
            "cmds": "",
            # A list of supported VCP codes with a list of supported values
            # for each nc code
            "vcp": "",
            # undocumented
            "mswhql": "",
            # undocumented
            "asset_eep": "",
            # MCCS version implemented
            "mccs_ver": "",
            # Specifies the window, window type (PIP or Zone) safe area size
            # (bounded safe area) maximum size of the window, minimum size of
            # the window, and window supports VCP codes for control/adjustment.
            "window": "",
            # Alternate name to be used for control
            "vcpname": "",
            # Parsed input sources into text. Not part of capabilities string.
            "inputs": "",
            # Parsed color presets into text. Not part of capabilities string.
            "color_presets": "",
        }

        for key in caps_dict:
            if key in ["cmds", "vcp"]:
                caps_dict[key] = _convert_to_dict(_extract_a_cap(caps_str, key))
            else:
                caps_dict[key] = _extract_a_cap(caps_str, key)

        # Parse the input sources into a text list for readability
        input_source_cap = get_vcp_com("input_select").value
        if input_source_cap in caps_dict["vcp"]:
            caps_dict["inputs"] = []
            input_val_list = list(caps_dict["vcp"][input_source_cap].keys())
            input_val_list.sort()

            for val in input_val_list:
                input_source = val

                caps_dict["inputs"].append(input_source)

        # Parse the color presets into a text list for readability
        color_preset_cap = get_vcp_com("image_color_preset").value
        if color_preset_cap in caps_dict["vcp"]:
            caps_dict["color_presets"] = []
            color_val_list = list(caps_dict["vcp"][color_preset_cap])
            color_val_list.sort()

            for val in color_val_list:
                color_source = val

                caps_dict["color_presets"].append(color_source)

        return caps_dict
