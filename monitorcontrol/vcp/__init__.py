import sys

from .vcp_codes import VCPCommand
from .vcp_abc import VCPError, VCPIOError, VCPPermissionError

from vcp_codes import get_vcp_com, create_vcp_com, VCPCommand

if sys.platform == "win32":
    from .vcp_windows import WindowsVCP as VCP
elif sys.platform.startswith("linux"):
    from .vcp_linux import LinuxVCP as VCP
else:
    raise NotImplementedError(
        f"Your OS is not supported. Supported OSs are: Windows, Linux. Detected system: {sys.platform}")
