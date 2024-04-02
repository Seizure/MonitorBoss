import sys
from .vcp_codes import VPCCommand  # noqa: F401
from .vcp_abc import (  # noqa: F401
    VCPError,
    VCPIOError,
    VCPPermissionError,
)

if sys.platform == "win32":
    from .vcp_windows import WindowsVCP as VCP  # noqa: F401
elif sys.platform.startswith("linux"):
    from .vcp_linux import LinuxVCP as VCP  # noqa: F401
else:
    raise NotImplementedError(f"Your OS is not supported. Supported OSs are: Windows, Linux. Detected system: {sys.platform}")
