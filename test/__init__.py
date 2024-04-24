import sys
sys.platform = "test"
# this is part of a demonic hack to load in a dummy VCP in the test framework
# otherwise, Python loads unnecessary OS-specific files,
# which can potentially cause errors if running on an otherwise unsupported OS
# there is probably a better way to do this.

from pyddc import VCPError, VCPIOError, VCPPermissionError, parse_capabilities, get_vcp_com, create_vcp_com, VCPCommand, VCPFeatureReturn
# from .vcp_dummy import DummyVCP as VCP