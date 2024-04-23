import pytest

import sys
sys.platform = "test"
# this is part of a demonic hack to load in a dummy VCP in the test framework
# otherwise, Python loads unnecessary OS-specific files,
# which can potentially cause errors if running on an otherwise unsupported OS
# there is probably a better way to do this.
from pyddc import VCP

vcps = VCP.get_vcps()

def test_check_for_cm_req():
    v = vcps[0]
    with pytest.raises(AssertionError):
        v.get_vcp_feature(0)
    with pytest.raises(AssertionError):
        v.set_vcp_feature(0, 0)
    with pytest.raises(AssertionError):
        v.get_vcp_capabilities()