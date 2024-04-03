import sys

from .vcp_codes import VPCCommand
from .vcp_abc import VCPError, VCPIOError, VCPPermissionError

if sys.platform == "win32":
    from .vcp_windows import WindowsVCP as VCP
elif sys.platform.startswith("linux"):
    from .vcp_linux import LinuxVCP as VCP
else:
    raise NotImplementedError(
        f"Your OS is not supported. Supported OSs are: Windows, Linux. Detected system: {sys.platform}")
