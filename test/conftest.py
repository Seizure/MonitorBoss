from pathlib import Path

import pytest

from monitorboss import config
from monitorboss.config import Config

pytest_plugins = "pytester" # used by the TestConfig functions in test_monitorboss_units.py

TEST_TOML_CONTENTS = """
[monitor_names]
0 = "foo"
1 = ["bar", "baz"]
# 2 has no alias

[input_names]
27 = ["usbc", "usb-c"] # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers
17 = "hdmi"

[settings]
wait_get = 0
wait_set = 0
wait_internal = 0""".strip()


# TODO: is there a way to not have redundant code between these?
@pytest.fixture(scope='module')
def test_cfg(tmp_path_factory) -> Config:
    file = tmp_path_factory.mktemp("conf") / "mb_conf.toml"
    file.write_text(TEST_TOML_CONTENTS)
    return config.get_config(file.as_posix())

@pytest.fixture(scope='module')
def test_conf_file(tmp_path_factory) -> Path:
    file = tmp_path_factory.mktemp("conf") / "mb_conf.toml"
    file.write_text(TEST_TOML_CONTENTS)
    return file
