from pathlib import Path

import pytest

from monitorboss import config
from monitorboss.config import Config
from monitorboss.profile import MonitorProfile, get_profile
from test.testdata import TEST_TOML_CONTENTS, TEST_PROFILE_TOML_CONTENTS

pytest_plugins = "pytester"  # used by the functions in test_config_units.py


def _write_file_fixture(tmp_path_factory, subdir: str, filename: str, contents: str) -> Path:
    """Write contents to a temporary TOML file and return its Path."""
    file = tmp_path_factory.mktemp(subdir) / filename
    file.write_text(contents)
    return file


@pytest.fixture(scope='module')
def test_conf_file(tmp_path_factory) -> Path:
    return _write_file_fixture(tmp_path_factory, "conf", "mb_conf.toml", TEST_TOML_CONTENTS)


@pytest.fixture(scope='module')
def test_conf(test_conf_file) -> Config:
    return config.get_config(test_conf_file.as_posix())


@pytest.fixture(scope='module')
def test_profile_file(tmp_path_factory) -> Path:
    return _write_file_fixture(tmp_path_factory, "profile", "mb_profile.toml", TEST_PROFILE_TOML_CONTENTS)


@pytest.fixture(scope='module')
def test_profile(test_profile_file) -> MonitorProfile:
    return get_profile(test_profile_file.as_posix())


