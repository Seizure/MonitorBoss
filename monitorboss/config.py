
# from configparser import ConfigParser
from dataclasses import dataclass, field

from tomlkit import parse, dumps, dump, comment, document, table, TOMLDocument

from monitorboss import MonitorBossError

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.toml"

#  TODO: when we fully support comments in config (see issue: https://github.com/Seizure/MonitorBoss/issues/7) this should just be a prebuilt cfg_parser
# DEFAULT_CONF_CONTENT = """
# [MONITOR_NAMES]
# DEFAULT = 0
#
# [INPUT_NAMES]
# USBC = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers
#
# [SETTINGS]
# WAIT = 2.0 # time in seconds to wait between commands, to avoid DDC/CI latency conflicts
# """.lstrip()

@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)
    wait_time: float = field(default_factory=float)


# cfg_parser = ConfigParser(inline_comment_prefixes="#")
# cfg_parser.optionxform = str  # case-sensitive keys TODO: get rid of this, after making MB internals case-insensitive


def default_toml() -> TOMLDocument:
    mon_names = table()
    mon_names.add(comment("Seizure's configuration"))
    mon_names.add("RIGHT", 0)
    mon_names.add("MIDDLE", 1)
    mon_names.add("LEFT", 2)

    input_names = table()
    input_names.add("USBC", 27)
    input_names["USBC"].comment("27 seems to be the \"standard non-standard\" ID for USB-C among manufacturers")

    settings = table()
    settings.add("WAIT", 2.0)

    doc = document()
    doc.add("MONITOR_NAMES", mon_names)
    doc.add("INPUT_NAMES", input_names)
    doc.add("SETTINGS", settings)

    return doc


def __get_toml_doc(path: str | None = None) -> TOMLDocument:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "r", encoding="utf8") as file:
            content = file.read()
    except:
        raise MonitorBossError(f'could not open config file for reading: "{path}"')

    return parse(content)


def get_config(path: str | None = None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    doc = __get_toml_doc(path)

    cfg = Config()
    try:
        for key, value in doc["MONITOR_NAMES"].items():
            cfg.monitor_names[key] = value
        for key, value in doc["INPUT_NAMES"].items():
            cfg.input_source_names[key] = value
        cfg.wait_time = doc["SETTINGS"]["WAIT"]
    except:
        raise MonitorBossError(f'could not parse config file: "{path}"')

    # As far as I can tell, negative numbers in python's sleep has undefined behavior, so we want to catch that
    if cfg.wait_time < 0:
        raise MonitorBossError(f'WAIT time is set to a negative value in config file: "{path}"')

    return cfg


def __write_config(config: TOMLDocument, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "w", encoding="utf8") as file:
            dump(config, file)
    except:
        raise MonitorBossError(f'could not open config file for writing: "{path}"')


def set_monitor_alias(alias: str, monid: int, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    doc = __get_toml_doc(path)

    doc["MONITOR_NAMES"][alias] = monid

    __write_config(doc, path)


def remove_monitor_alias(alias: str, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    doc = __get_toml_doc(path)

    doc.remove(["MONITOR_NAMES"][alias])

    doc["MONITOR_NAMES"][alias]

    __write_config(path)


def set_input_alias(alias: str, inputid: int, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    read_config(path)

    cfg_parser.set("INPUT_NAMES", alias, str(inputid))

    __write_config(path)


def remove_input_alias(alias: str, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    read_config(path)

    cfg_parser.remove_option("INPUT_NAMES", alias)

    __write_config(path)


def set_wait_time(wait: float, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    read_config(path)

    if wait < 0:
        raise MonitorBossError(f'WAIT time can not be set to a negative value: {wait}')

    cfg_parser.set("SETTINGS", "WAIT", str(wait))

    __write_config(path)


def reset_config(path: str | None = None):
    #  TODO: when we fully support comments in config (see issue: https://github.com/Seizure/MonitorBoss/issues/7) this should call __write_config
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "w", encoding="utf8") as file:
            file.write(DEFAULT_CONF_CONTENT)
    except:
        raise MonitorBossError(f'could not reset config file "{path}"')
