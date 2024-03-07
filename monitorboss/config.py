from configparser import ConfigParser
from dataclasses import dataclass, field
from pathlib import Path

import monitorboss as mb

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.conf"

#  TODO: when we fully support comments in config (see issue: https://github.com/Seizure/MonitorBoss/issues/7) this should just be a prebuilt cfg_parser
DEFAULT_CONF_CONTENT = """
[MONITOR_NAMES]
DEFAULT = 0

[INPUT_NAMES]
USBC = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers

[SETTINGS]
WAIT = 2.0 # time in seconds to wait between commands, to avoid DDC/CI latency conflicts 
""".lstrip()

@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)
    wait_time: float = field(default_factory=float)


cfg_parser = ConfigParser(inline_comment_prefixes="#")
cfg_parser.optionxform = str  # case-sensitive keys TODO: get rid of this, after making MB internals case-insensitive


def read_config(path: str | None = None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "r", encoding="utf8") as file:
            cfg_parser.read_file(file, path)
    except:
        raise mb.MonitorBossError(f'could not read config file "{path}"')

    cfg = Config()

    try:
        for key, value in cfg_parser["MONITOR_NAMES"].items():
            cfg.monitor_names[key] = int(value)
        for key, value in cfg_parser["INPUT_NAMES"].items():
            cfg.input_source_names[key] = int(value)
        cfg.wait_time = float(cfg_parser["SETTINGS"]["WAIT"])
    except:
        raise mb.MonitorBossError(f'could not parse config file "{path}"')

    # As far as I can tell, negative numbers in python's sleep has undefined behavior, so we want to catch that
    if cfg.wait_time < 0:
        raise mb.MonitorBossError(f'WAIT time is set to a negative value in config file "{path}"')

    return cfg


def __write_config(path: str | None = None):
    """It's expected that read_config was called at some point prior to using this.
    Otherwise, you'll just blank the config/file"""

    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "w", encoding="utf8") as file:
            cfg_parser.write(file)
    except:
        raise mb.MonitorBossError(f'could not write to config file "{path}"')


def add_monitor_alias(alias: str, monid: int, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    read_config(path)

    cfg_parser.set("MONITOR_NAMES", alias, str(monid))

    __write_config(path)


def remove_monitor_alias(alias: str, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    read_config(path)

    cfg_parser.remove_option("MONITOR_NAMES", alias)

    __write_config(path)


def reset_config(path: str | None = None):
    #  TODO: when we fully support comments in config (see issue: https://github.com/Seizure/MonitorBoss/issues/7) this should call __write_config
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "w", encoding="utf8") as file:
            file.write(DEFAULT_CONF_CONTENT)
    except:
        raise mb.MonitorBossError(f'could not reset config file "{path}"')
