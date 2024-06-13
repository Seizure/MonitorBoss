import pytest

import tomlkit

from .vcp_dummy import DummyVCP as VCP
import pyddc

pyddc.VCP = VCP

from .test_utils import rm_toml, set_toml, TEST_CONFIG_LOCATION, TEST_TOML_CONTENTS
from monitorboss import config


class TestConfig:

    def test_auto_create_config(self):
        rm_toml()
        assert not TEST_CONFIG_LOCATION.exists()
        config.get_config(TEST_CONFIG_LOCATION)
        assert TEST_CONFIG_LOCATION.exists()

    def test_config_reset(self):
        set_toml()
        contents: str
        new_contents: str

        with open(TEST_CONFIG_LOCATION, "r", encoding="utf8") as file:
            contents = file.read().strip()
        assert contents == TEST_TOML_CONTENTS

        config.reset_config(TEST_CONFIG_LOCATION)
        with open(TEST_CONFIG_LOCATION, "r", encoding="utf8") as file:
            contents = open(TEST_CONFIG_LOCATION, "r", encoding="utf8").read().strip()
        assert contents == tomlkit.dumps(config.default_toml()).strip()

    # TODO: should probably eventually test more of the config functions,
    #   but we're currently not even using them and they might change, so not bothering yet


class TestCLIGet:

    def test_get_discreet