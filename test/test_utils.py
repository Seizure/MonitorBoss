from pathlib import Path
import os

TEST_CONFIG_LOCATION = Path("./test/test_config.toml")

TEST_TOML_CONTENTS = """
[monitor_names]
main = 0
foo = 1
bar = 2

[input_names]
USBC = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[settings]
wait = 0.05""".strip()


def rm_toml():
    if TEST_CONFIG_LOCATION.exists():
        os.remove(TEST_CONFIG_LOCATION)


def set_toml():
    if TEST_CONFIG_LOCATION.exists():
        rm_toml()
    with open(TEST_CONFIG_LOCATION, "w", encoding="utf8") as file:
        file.write(TEST_TOML_CONTENTS)
