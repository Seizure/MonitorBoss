import os

import pytest

os.environ["PYDDC_SKIP_DRIVER"] = "true"
from pyddc import get_vcp_com, parse_capabilities
from pyddc.vcp_codes import VCPCodes
from .vcp_dummy import DummyVCP as VCP

input_command = get_vcp_com(VCPCodes.input_source)
lum_command = get_vcp_com(VCPCodes.image_luminance)
reset_command = get_vcp_com(VCPCodes.restore_factory_default)
active_control = get_vcp_com(VCPCodes.active_control)


class TestGetFeature:

    vcp = VCP.get_vcps()[0]

    def test_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_feature(input_command)

    def test_unreadable_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.get_vcp_feature(reset_command)

    def test_unsupported_code(self):
        # TODO: need to sort out expected/proper behavior for this
        pass

    def test_supported_discreet_code(self):
        # TODO: need to figure out what the "max" return is for discreet codes
        pass

    def test_supported_continuous_code(self):
        with self.vcp as vcp:
            assert vcp.get_vcp_feature(lum_command) == (75, 80)


class TestGetMax:

    vcp = VCP.get_vcps()[0]

    def test_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_feature_max(input_command)

    def test_unreadable_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.get_vcp_feature_max(reset_command)

    def test_discreet_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.get_vcp_feature_max(input_command)

    def test_unsupported_code(self):
        # TODO: need to sort out expected/proper behavior for this
        pass

    def test_supported_code(self):
        with self.vcp as vcp:
            assert vcp.get_vcp_feature_max(lum_command) == 80
        assert self.vcp.code_maximum[lum_command.value] == 80


class TestSetFeature:

    vcp = VCP.get_vcps()[0]

    def test_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.set_vcp_feature(input_command, 27)

    def test_unwriteable_code(self):
        with self.vcp as vcp:
            with pytest.raises(TypeError):
                vcp.set_vcp_feature(active_control, 0)

    def test_set_above_max(self):
        with self.vcp as vcp:
            with pytest.raises(ValueError):
                vcp.set_vcp_feature(lum_command, 85)

    def test_unsupported_code(self):
        # TODO: need to sort out expected/proper behavior for this
        pass

    def test_supported_code(self):
        with self.vcp as vcp:
            vcp.set_vcp_feature(lum_command, 30)
            assert vcp.get_vcp_feature(lum_command).value == 30


class TestCapabilitiesFunctions:

    vcp = VCP.get_vcps()[0]

    def test_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_capabilities()

    # TODO: test different string formats/edge cases

    def test_caps_parsing(self):
        with self.vcp as vcp:
            caps = parse_capabilities(vcp.get_vcp_capabilities())
            # TODO: caps parsing is changing soon, this will break as soon as it does
            assert caps.__str__() == "{'prot': 'monitor', 'type': 'LCD', 'model': 'DUMM13', 'cmds': [<4>], 'vcp': [<16>, <18>, <96 (27, 15, 17)>, <170 (1, 2, 4)>], 'mccs_ver': '2.1'}"


class TestGetVCPCom:

    def test_get_with_bad_type(self):
        with pytest.raises(TypeError):
            get_vcp_com(1.3)

    def test_get_none_by_int(self):
        assert get_vcp_com(1048) is None

    def test_get_none_by_str(self):
        assert get_vcp_com("rawr") is None

    def test_get_com_by_int(self):
        assert get_vcp_com(16).name == "image_luminance"

    def test_get_com_by_str(self):
        assert get_vcp_com("image_luminance").value == 16
