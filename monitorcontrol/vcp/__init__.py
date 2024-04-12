import sys

from .vcp_codes import VCPCommand
from .vcp_abc import VCPError, VCPIOError, VCPPermissionError


if sys.platform == "win32":
    from .vcp_windows import WindowsVCP as VCP
elif sys.platform.startswith("linux"):
    from .vcp_linux import LinuxVCP as VCP
elif sys.platform == "darwin":
    # TODO: need to check for intel vs arm platform and import appropriately
    from .vcp_macos_intel import MacOSIntelVCP as VCP
else:
    raise NotImplementedError(
        f"Detected unsupported OS. Supported OSs are: Windows, Linux, and macOS. Detected system: {sys.platform}")
