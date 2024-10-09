from pathlib import Path

import pytest

from monitorboss import config
from monitorboss.config import Config
from test.pyddc import TEST_TOML_CONTENTS

pytest_plugins = "pytester"  # used by the functions in test_config_units.py


@pytest.fixture(scope='module')
def test_conf_file(tmp_path_factory) -> Path:
    file = tmp_path_factory.mktemp("conf") / "mb_conf.toml"
    file.write_text(TEST_TOML_CONTENTS)
    return file


@pytest.fixture(scope='module')
def test_cfg(test_conf_file) -> Config:
    return config.get_config(test_conf_file.as_posix())
