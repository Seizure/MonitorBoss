from configparser import ConfigParser
from dataclasses import dataclass, field


DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.conf"


DEFAULT_CONF_CONTENT = """
[MONITOR_NAMES]
DEFAULT = 0

[INPUT_NAMES]
USBC = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers
""".lstrip()


@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)


def read_config(path: str | None = None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    cfg_parser = ConfigParser(inline_comment_prefixes="#")
    cfg_parser.optionxform = str # case-sensitive keys

    with open(path, "r", encoding="utf8") as file:
        cfg_parser.read_file(file, path)

    cfg = Config()

    for key, value in cfg_parser["MONITOR_NAMES"].items():
        cfg.monitor_names[key] = int(value)
    for key, value in cfg_parser["INPUT_NAMES"].items():
        cfg.input_source_names[key] = int(value)

    return cfg

def reset_config(path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    with open(path, "w", encoding="utf8") as file:
        file.write(DEFAULT_CONF_CONTENT)
