import enum
from logging import getLogger
from pathlib import Path
from dataclasses import dataclass, field

from tomlkit import parse, dump, comment, document, table, TOMLDocument

from monitorboss import MonitorBossError

_log = getLogger(__name__)

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

    def read(self, doc: TOMLDocument):
        _log.debug(f"read Config from TOML doc: {doc}")
        for key, value in doc[TomlKeys.monitors.value].items():
            self.monitor_names[key] = value
        for key, value in doc[TomlKeys.inputs.value].items():
            self.input_source_names[key] = value
        self.wait_time = doc[TomlKeys.settings.value][TomlKeys.wait.value]

    def validate(self):
        _log.debug(f"validate Config")
        if self.wait_time < 0:
            raise MonitorBossError(f"invalid wait time: {self.wait_time}")


def default_toml() -> TOMLDocument:
    _log.debug("define default TOML config")
    mon_names = table()
    mon_names.add("main", 0)

    input_names = table()
    input_names.add("usbc", 27)
    input_names["usbc"].comment('27 seems to be the "standard non-standard" ID for USB-C among manufacturers')

    settings = table()
    settings.add(TomlKeys.wait.value, 0.05)

    doc = document()
    doc.add(TomlKeys.monitors.value, mon_names)
    doc.add(TomlKeys.inputs.value, input_names)
    doc.add(TomlKeys.settings.value, settings)

    return doc


def __read_toml(path: str | None) -> TOMLDocument:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"read TOML config from: {path}")
    if not Path(path).parent.exists():
        Path(path).parent.mkdir(parents=True)
    if not Path(path).exists():
        reset_config(path)
    try:
        with open(path, "r", encoding="utf8") as file:
            content = file.read()
    except Exception as err:
        raise MonitorBossError(f"could not read config file: {path}") from err
    return parse(content)


def __write_toml(doc: TOMLDocument, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"write TOML config to: {path}")
    if not Path(path).parent.exists():
        Path(path).parent.mkdir(parents=True)
    try:
        with open(path, "w", encoding="utf8") as file:
            dump(doc, file)
    except Exception as err:
        raise MonitorBossError(f"could not write config file: {path}") from err


def get_config(path: str | None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"get Config dataclass from: {path}")
    doc = __read_toml(path)
    cfg = Config()
    try:
        cfg.read(doc)
    except Exception as err:
        raise MonitorBossError(f"could not parse config file: {path}: {err}") from err
    cfg.validate()
    return cfg


def set_monitor_alias(alias: str, mon_id: int, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set monitor alias: {alias} = {mon_id} (in {path})")
    doc = __read_toml(path)
    doc[TomlKeys.monitors.value][alias] = mon_id
    __write_toml(doc, path)


def remove_monitor_alias(alias: str, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"remove monitor alias: {alias} (in {path})")
    doc = __read_toml(path)
    doc.remove(doc[TomlKeys.monitors.value][alias])
    __write_toml(doc, path)


def set_input_alias(alias: str, input_id: int, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set input alias: {alias} = {input_id} (in {path})")
    doc = __read_toml(path)
    doc[TomlKeys.inputs.value][alias] = input_id
    __write_toml(doc, path)


def remove_input_alias(alias: str, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"remove input alias: {alias} (in {path})")
    doc = __read_toml(path)
    doc.remove(doc[TomlKeys.inputs.value][alias])
    __write_toml(doc, path)


def set_wait_time(wait_time: float, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set wait time: {wait_time} (in {path})")
    if wait_time < 0:
        raise MonitorBossError(f"invalid wait time: {wait_time}")
    doc = __read_toml(path)
    doc[TomlKeys.settings.value][TomlKeys.wait.value] = wait_time
    __write_toml(doc, path)


def reset_config(path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"reset config to default: {path}")
    __write_toml(default_toml(), path)
