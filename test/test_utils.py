from pathlib import Path
import os
import sys
from io import StringIO

TEST_CONFIG_LOCATION = Path("./test/test_config.toml")

TEST_TOML_CONTENTS = """
[monitor_names]
main = 0
foo = 1
bar = 2

[input_names]
usbc = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[settings]
wait = 0.0""".strip()


def rm_toml():
    if TEST_CONFIG_LOCATION.exists():
        os.remove(TEST_CONFIG_LOCATION)


def set_toml():
    if TEST_CONFIG_LOCATION.exists():
        rm_toml()
    with open(TEST_CONFIG_LOCATION, "w", encoding="utf8") as file:
        file.write(TEST_TOML_CONTENTS)


# https://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
class CaptureSTDOUT(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout
