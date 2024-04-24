import pytest
from test import get_vcp_com, parse_capabilities
from .vcp_dummy import DummyVCP as VCP

vcps = VCP.get_vcps()
input_command = get_vcp_com(96)
lum_command = get_vcp_com(16)
reset_command = get_vcp_com(4)
active_control = get_vcp_com(82)


class TestGetFeature:

    vcp = vcps[0]

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


class TestSetFeature:

    vcp = vcps[0]

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


class TestCapabilitiesFunctions:

    vcp = vcps[0]

    def test_cm_assertion(self):
        with pytest.raises(AssertionError):
            self.vcp.get_vcp_capabilities()

    def test_caps_parsing(self):
        with vcps[0] as vcp:
            caps = parse_capabilities(vcp.get_vcp_capabilities())
            # TODO: caps parsing is changing soon, this will break as soon as it does
            assert caps.__str__() == "{'prot': 'monitor', 'type': 'LCD', 'model': 'DUMM13', 'cmds': [<4>], 'vcp': [<16>, <18>, <96 (<27>, <15>, <17>)>, <170 (<1>, <2>, <4>)>], 'mccs_ver': '2.1'}"
