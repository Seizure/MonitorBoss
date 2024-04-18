import enum
from pathlib import Path
from dataclasses import dataclass, field

from tomlkit import parse, dump, comment, document, table, TOMLDocument

from monitorboss import MonitorBossError

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.toml"


class TomlKeys(enum.Enum):
    monitors = "monitor_names"
    inputs = "input_names"
    settings = "settings"
    wait = "wait"


@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)
    wait_time: float = field(default_factory=float)


def default_toml() -> TOMLDocument:
    mon_names = table()
    mon_names.add(comment("Seizure's configuration"))
    mon_names.add("right", 2)
    mon_names.add("middle", 0)
    mon_names.add("left", 1)

    input_names = table()
    input_names.add("USBC", 27)
    input_names["USBC"].comment("27 seems to be the \"standard non-standard\" ID for USB-C among manufacturers")

    settings = table()
    settings.add(TomlKeys.wait, 2.0)

    doc = document()
    doc.add(TomlKeys.monitors, mon_names)
    doc.add(TomlKeys.inputs, input_names)
    doc.add(TomlKeys.settings, settings)

    return doc


def __get_toml(path: str | None = None) -> TOMLDocument:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    try:
        with open(path, "r", encoding="utf8") as file:
            content = file.read()
    except Exception as err:
        print(err)
        raise MonitorBossError(f'could not open config file for reading: "{path}"')
    return parse(content)


def get_config(path: str | None = None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC

    if not Path(path).parent.exists():
        Path(path).parent.mkdir(parents=True)
    if not Path(path).exists():
        reset_config()

    doc = __get_toml(path)
    cfg = Config()
    try:
        for key, value in doc[TomlKeys.monitors.value].items():
            cfg.monitor_names[key] = value
        for key, value in doc[TomlKeys.inputs.value].items():
            cfg.input_source_names[key] = value
        cfg.wait_time = doc[TomlKeys.settings.value][TomlKeys.wait.value]
    except Exception as err:
        print(err)
        raise MonitorBossError(f'could not parse config file: "{path}"')
    # As far as I can tell, negative numbers in python's sleep has undefined behavior, so we want to catch that
    if cfg.wait_time < 0:
        raise MonitorBossError(f'invalid wait time in config file: "{path}"')
    return cfg


def __write_toml(config: TOMLDocument, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    try:
        with open(path, "w", encoding="utf8") as file:
            dump(config, file)
    except Exception as err:
        print(err)
        raise MonitorBossError(f'could not open config file for writing: "{path}"')


def set_monitor_alias(alias: str, mon_id: int, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    doc = __get_toml(path)
    doc[TomlKeys.monitors.value][alias] = mon_id
    __write_toml(doc, path)


def remove_monitor_alias(alias: str, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    doc = __get_toml(path)
    doc.remove(doc[TomlKeys.monitors.value][alias])
    __write_toml(doc, path)


def set_input_alias(alias: str, input_id: int, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    doc = __get_toml(path)
    doc[TomlKeys.inputs.value][alias] = input_id
    __write_toml(doc, path)


def remove_input_alias(alias: str, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    doc = __get_toml(path)
    doc.remove(doc[TomlKeys.inputs.value][alias])
    __write_toml(doc, path)


def set_wait_time(wait: float, path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    if wait < 0:
        raise MonitorBossError(f'invalid wait time: {wait}')
    doc = __get_toml(path)
    doc[TomlKeys.settings.value][TomlKeys.wait.value] = wait
    __write_toml(doc, path)


def reset_config(path: str | None = None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    __write_toml(default_toml(), path)
