from __future__ import annotations
import abc
import logging
from types import TracebackType
from typing import Optional, Tuple, Type, List

from .vcp_codes import VCPCommand, get_vcp_com


class VCPError(Exception):
    pass


class VCPIOError(VCPError):
    pass


class VCPPermissionError(VCPError):
    pass


class VCP(abc.ABC):

    @abc.abstractmethod
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.code_maximum = {}
        self._in_ctx = False

    @abc.abstractmethod
    def __enter__(self):
        self._in_ctx = True
        return self

    @abc.abstractmethod
    def __exit__(
            self,
            exception_type: Optional[Type[BaseException]],
            exception_value: Optional[BaseException],
            exception_traceback: Optional[TracebackType],
    ) -> Optional[bool]:
        self._in_ctx = False
        return False

    def set_vcp_feature(self, code: VCPCommand, value: int):
        assert self._in_ctx, "This function must be run within the context manager"
        if not code.writeable:
            raise TypeError(f"cannot write read-only code: {code.name}")
        elif code.readable and code.discreet is False:
            maximum = self._get_code_maximum(code)
            if value > maximum:
                raise ValueError(f"value of {value} exceeds code maximum of {maximum} for {code.name}")
        self.logger.debug(f"SetVCPFeature(_, {code.name=}, {value=})")
        self._set_vcp_feature(code, value)

    @abc.abstractmethod
    def _set_vcp_feature(self, code: VCPCommand, value: int):
        pass

    def get_vcp_feature(self, code: VCPCommand) -> Tuple[int, int]:
        assert self._in_ctx, "This function must be run within the context manager"
        if not code.readable:
            raise TypeError(f"cannot read write-only code: {code.name}")
        self.logger.debug(f"GetVCPFeatureAndVCPFeatureReply(_, {code.name=}, None, _, _)")
        return self._get_vcp_feature(code)

    @abc.abstractmethod
    def _get_vcp_feature(self, code: VCPCommand) -> Tuple[int, int]:
        pass

    def get_vcp_capabilities(self) -> dict:
        assert self._in_ctx, "This function must be run within the context manager"
        caps_str = self._get_vcp_capabilities_str()
        return _parse_capabilities(caps_str)

    @abc.abstractmethod
    def _get_vcp_capabilities_str(self) -> str:
        pass

    def _get_code_maximum(self, code: VCPCommand) -> int:
        assert self._in_ctx, "This function must be run within the context manager"
        if not code.readable:
            raise TypeError(f"code is not readable: {code.name}")
        if code.value in self.code_maximum:
            return self.code_maximum[code.value]
        else:
            _, maximum = self.get_vcp_feature(code)
            self.code_maximum[code.value] = maximum
            return maximum

    @staticmethod
    @abc.abstractmethod
    def get_vcps() -> List[VCP]:
        pass


def _extract_a_cap(caps_str: str, key: str) -> str:
    """
    Splits the capabilities string into individual sets.

    Returns:
        Dict of all values for the capability
    """
    start_of_filter = caps_str.upper().find(key.upper())
    if start_of_filter == -1:
        # Not all keys are returned by monitor.
        # Also, sometimes the string has errors.
        return ""
    start_of_filter += len(key)
    filtered_caps_str = caps_str[start_of_filter:]
    end_of_filter = 0
    for i in range(len(filtered_caps_str)):
        if filtered_caps_str[i] == "(":
            end_of_filter += 1
        elif filtered_caps_str[i] == ")":
            end_of_filter -= 1
        if end_of_filter == 0:
            # 1:i to remove the first character "(" and the closing ")"
            return filtered_caps_str[1:i]
    return filtered_caps_str


def _convert_to_dict(caps_str: str) -> dict:
    """
    Example:
    >>> _convert_to_dict("04 14(05 06) 16")
    {4: {}, 20: {5: {}, 6: {}}, 22: {}}
    """
    caps_dict = {}
    group = []
    prev_val = None
    for chunk in caps_str.replace("(", " ( ").replace(")", " ) ").split():
        if chunk == "":
            continue
        elif chunk == "(":
            group.append(prev_val)
        elif chunk == ")":
            group.pop(-1)
        else:
            val = int(chunk, 16)
            if len(group) == 0:
                caps_dict[val] = {}
            else:
                d = caps_dict
                for g in group:
                    d = d[g]
                d[val] = {}
            prev_val = val
    return caps_dict

# TODO: this should probably return the raw dict, and not help/add extra info; that's for MonitorBoss to do
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
        cap = _extract_a_cap(caps_str, key)
        if key in {"cmds", "vcp"}:
            cap = _convert_to_dict(cap)
        caps_dict[key] = cap

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
