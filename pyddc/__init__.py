import sys

from .vcp_abc import VCPError, VCPIOError, VCPPermissionError, parse_capabilities, VCPFeatureReturn
from .vcp_codes import get_vcp_com, create_vcp_com, VCPCommand

if sys.platform == "win32":
    from .vcp_windows import WindowsVCP as VCP
elif sys.platform.startswith("linux"):
    from .vcp_linux import LinuxVCP as VCP
elif sys.platform.startswith("test"):
    # this is part of a demonic hack to load in a dummy VCP in the test framework
    # otherwise, you get a NotImplementedError and/or Python tries to import non-existant OS-specific modules
    # there is probably a better way to do this.
    pass
else:
    raise NotImplementedError(
        f"Your OS is not supported. Supported OSs are: Windows, Linux. Detected system: {sys.platform}")
