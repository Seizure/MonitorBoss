from configparser import ConfigParser
from dataclasses import dataclass, field

from impl import MonitorBossError

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.conf"


DEFAULT_CONF_CONTENT = """
[MONITOR_NAMES]
DEFAULT = 0

[INPUT_NAMES]
USBC = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[SETTINGS]
WAIT = 2.0 # time to wait between commands, to avoid DDC/CI latency conflicts 
""".lstrip()


@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)
    wait_time: float = field(default_factory=float)


def read_config(path: str | None = None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    cfg_parser = ConfigParser(inline_comment_prefixes="#")
    cfg_parser.optionxform = str # case-sensitive keys

    try:
        with open(path, "r", encoding="utf8") as file:
            cfg_parser.read_file(file, path)
    except:
        raise MonitorBossError(f'could not read config file "{path}"')

    cfg = Config()

    try:
        for key, value in cfg_parser["MONITOR_NAMES"].items():
            cfg.monitor_names[key] = int(value)
        for key, value in cfg_parser["INPUT_NAMES"].items():
            cfg.input_source_names[key] = int(value)
        cfg.wait_time = float(cfg_parser["SETTINGS"]["WAIT"])
    except:
        raise MonitorBossError(f'could not parse config file "{path}"')

    # as far as I can tell, negative numbers in Python's sleep command creates undefined behavior depending on OS
    # and other things, so we probably want to catch this in some manner
    if cfg.wait_time < 0:
        raise MonitorBossError(f'WAIT time is set to a negative value in config file "{path}"')

    return cfg


def reset_config(path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "w", encoding="utf8") as file:
            file.write(DEFAULT_CONF_CONTENT)
    except:
        raise MonitorBossError(f'could not reset config file "{path}"')
