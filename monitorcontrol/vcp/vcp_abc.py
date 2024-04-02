from __future__ import annotations
import abc
import logging
from types import TracebackType
from typing import Optional, Tuple, Type, List

from .vcp_codes import VPCCommand


class VCPError(Exception):
    """Base class for all VCP related errors."""

    pass


class VCPIOError(VCPError):
    """Raised on VCP IO errors."""

    pass


class VCPPermissionError(VCPError):
    """Raised on VCP permission errors."""

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

    @abc.abstractmethod
    def set_vcp_feature(self, code: VPCCommand, value: int):
        """
        Sets the value of a feature on the virtual control panel.

        Args:
            code: Feature code.
            value: Feature value.

        Raises:
            VCPError: Failed to set VCP feature.
        """
        pass

    @abc.abstractmethod
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
        pass

    @abc.abstractmethod
    def get_vcp_capabilities(self) -> dict:
        pass

    def _get_code_maximum(self, code: VPCCommand) -> int:
        """
        Gets the maximum values for a given code, and caches in the
        class dictionary if not already found.

        Args:
            code: Feature code definition class.

        Returns:
            Maximum value for the given code.

        Raises:
            TypeError: Code is write only.
        """
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
