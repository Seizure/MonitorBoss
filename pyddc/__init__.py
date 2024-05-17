import sys
import os

from .vcp_abc import VCPError, VCPIOError, VCPPermissionError, parse_capabilities, VCPFeatureReturn
from .vcp_codes import get_vcp_com, VCPCommand

if os.environ.get("PYDDC_SKIP_DRIVER") is not None and os.environ.get("PYDDC_SKIP_DRIVER").casefold() == "true":
    from .vcp_abc import VCP as ABCVCP
else:
    if sys.platform == "win32":
        from .vcp_windows import WindowsVCP as VCP
    elif sys.platform.startswith("linux"):
        from .vcp_linux import LinuxVCP as VCP
    else:
        raise NotImplementedError(
            f"Your OS is not supported. Supported OSs are: Windows, Linux. Detected system: {sys.platform}")