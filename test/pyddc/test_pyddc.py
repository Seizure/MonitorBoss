import pytest

from pyddc import get_vcp_com, parse_capabilities, vcp_codes
from pyddc.vcp_codes import VCPCodes
from .vcp_dummy import DummyVCP as VCP

input_command = get_vcp_com(VCPCodes.input_source)
lum_command = get_vcp_com(VCPCodes.image_luminance)
reset_command = get_vcp_com(VCPCodes.restore_factory_default)
active_control = get_vcp_com(VCPCodes.active_control)


class TestGetFeature:

    vcp = VCP.get_vcps()[0]

    def test_get_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_feature(input_command)

    def test_get_unreadable_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.get_vcp_feature(reset_command)

    # def test_unsupported_code(self):
    #   # behavior for unsupported codes is undefined in practice, so not worth testing
    #   pass

    # def test_supported_discreet_code(self):
    #   # according to VESA specs, the MAX value for discrete codes should be number of options,
    #   # but there is nothing meaningful to test in that regard with a dummy driver, so not bothering
    #   pass

    def test_get_supported_continuous_code(self):
        with self.vcp as vcp:
            result = vcp.get_vcp_feature(lum_command)
            assert (result.value, result.max) == (75, 80)

    def test_get_masked_high_byte(self):
        with self.vcp as vcp:
            result = vcp.get_vcp_feature(input_command)
            assert (result.value, result.max) == (1, 4)


class TestGetMax:

    vcp = VCP.get_vcps()[0]

    def test_getmax_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_feature_max(input_command)

    def test_getmax_unreadable_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.get_vcp_feature_max(reset_command)

    # def test_supported_discreet_code(self):
    #   # according to VESA specs, the MAX value for discrete codes should be number of options,
    #   # but there is nothing meaningful to test in that regard with a dummy driver, so not bothering
    #   pass

    # def test_unsupported_code(self):
    #   # behavior for unsupported codes is undefined in practice, so not worth testing
    #   pass

    def test_getmax_supported_continuous_code(self):
        with self.vcp as vcp:
            assert vcp.get_vcp_feature_max(lum_command) == 80
        assert self.vcp.code_maximum[lum_command.code] == 80


class TestSetFeature:

    vcp = VCP.get_vcps()[0]

    def test_set_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.set_vcp_feature(input_command, 27)

    def test_set_unwriteable_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.set_vcp_feature(active_control, 0)

    def test_set_continuous_above_max(self):
        with self.vcp as vcp:
            with pytest.raises(ValueError):
                vcp.set_vcp_feature(lum_command, 85)

    # def test_unsupported_code(self):
    #   # behavior for unsupported codes is undefined in practice, so not worth testing
    #   pass

    # def test_abovemax_code(self):
    #   # behavior for unsupported codes is undefined in practice, so not worth testing
    #   pass

    def test_set_supported_code(self):
        with self.vcp as vcp:
            vcp.set_vcp_feature(lum_command, 30)
            assert vcp.get_vcp_feature(lum_command).value == 30


class TestCapabilitiesFunctions:

    vcp = VCP.get_vcps()[0]

    def test_caps_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_capabilities()

    # def test_caps_str(self):
    #     # doesn't seem worth testing in a dummy driver, since I'm hard-coding the caps string
    #     pass

    # TODO: test different string formats/edge cases
    def test_caps_parsing(self):
        with self.vcp as vcp:
            caps = parse_capabilities(vcp.get_vcp_capabilities())
            assert str(caps) == "{'prot': 'monitor', 'type': 'LCD', 'model': 'DUMM13', 'cmds': [Capability(cap=4, values=None)], 'vcp': [Capability(cap=16, values=None), Capability(cap=18, values=None), Capability(cap=96, values=[27, 15, 17]), Capability(cap=170, values=[1, 2, 4])], 'mccs_ver': '2.1'}"


class TestVCPCommands:

    # The number of items in VCPCodes(IntEnum) and _VCP_COMMANDS should always match
    def test_codes_commandlist_parity(self):
        assert len(vcp_codes._VCP_COMMANDS) == len(VCPCodes)

    def test_get_com_with_bad_type(self):
        with pytest.raises(TypeError):
            get_vcp_com(1.3)

    def test_get_com_none_by_int(self):
        assert get_vcp_com(1048) is None

    def test_get_com_none_by_str(self):
        assert get_vcp_com("rawr") is None

    def test_get_com_by_int(self):
        assert get_vcp_com(16).code == 16

    def test_get_com_by_str(self):
        assert get_vcp_com("image_luminance").code == 16
