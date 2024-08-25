import enum
from logging import getLogger
from pathlib import Path
from dataclasses import dataclass, field

from tomlkit import parse, dump, comment, document, table, TOMLDocument
from tomlkit.items import Array, String, Trivia

from monitorboss import MonitorBossError

_log = getLogger(__name__)

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.toml"


class TomlCategories(enum.Enum):
    monitors = "monitor_names"
    inputs = "input_names"
    settings = "settings"


class TomlSettingsKeys(enum.Enum):
    wait_get = "wait_get"
    wait_set = "wait_set"


@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)
    wait_get_time: float = field(default_factory=float)
    wait_set_time: float = field(default_factory=float)

    def read(self, doc: TOMLDocument):
        _log.debug(f"read Config from TOML doc: {doc}")
        for val, aliases in doc[TomlCategories.monitors.value].items():
            if isinstance(aliases, String):
                aliases = Array([aliases], Trivia())
            for alias in aliases:
                self.monitor_names[alias] = int(val) if val.isdigit() else val
        for val, aliases in doc[TomlCategories.inputs.value].items():
            if isinstance(aliases, String):
                aliases = Array([aliases], Trivia())
            for alias in aliases:
                self.input_source_names[alias] = int(val) if val.isdigit() else val
        self.wait_get_time = doc[TomlCategories.settings.value][TomlSettingsKeys.wait_get.value]
        self.wait_set_time = doc[TomlCategories.settings.value][TomlSettingsKeys.wait_set.value]

    def validate(self):
        _log.debug(f"validate config")
        if self.wait_get_time < 0:
            raise MonitorBossError(f"invalid wait get time: {self.wait_get_time}")
        if self.wait_set_time < 0:
            raise MonitorBossError(f"invalid wait set time: {self.wait_set_time}")


def default_toml() -> TOMLDocument:
    _log.debug("define default TOML config")
    mon_names = table()
    mon_names.add("0", "main")

    input_names = table()
    input_names.add("27", ["usbc", "usb_c", "usbc"])
    input_names["27"].comment('27 seems to be the "standard non-standard" ID for USB-C among manufacturers')

    settings = table()
    settings.add(TomlSettingsKeys.wait_get.value, 0.05)
    settings.add(TomlSettingsKeys.wait_set.value, 0.1)

    doc = document()
    doc.add(TomlCategories.monitors.value, mon_names)
    doc.add(TomlCategories.inputs.value, input_names)
    doc.add(TomlCategories.settings.value, settings)

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
    doc[TomlCategories.monitors.value][alias] = mon_id
    __write_toml(doc, path)


def remove_monitor_alias(alias: str, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"remove monitor alias: {alias} (in {path})")
    doc = __read_toml(path)
    doc.remove(doc[TomlCategories.monitors.value][alias])
    __write_toml(doc, path)


def set_input_alias(alias: str, input_id: int, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set input alias: {alias} = {input_id} (in {path})")
    doc = __read_toml(path)
    doc[TomlCategories.inputs.value][alias] = input_id
    __write_toml(doc, path)


def remove_input_alias(alias: str, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"remove input alias: {alias} (in {path})")
    doc = __read_toml(path)
    doc.remove(doc[TomlCategories.inputs.value][alias])
    __write_toml(doc, path)


def set_wait_get_time(wait_get_time: float, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set wait get time: {wait_get_time} (in {path})")
    if wait_get_time < 0:
        raise MonitorBossError(f"invalid wait get time: {wait_get_time}")
    doc = __read_toml(path)
    doc[TomlCategories.settings.value][TomlSettingsKeys.wait_get.value] = wait_get_time
    __write_toml(doc, path)


def set_wait_set_time(wait_set_time: float, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set wait set time: {wait_set_time} (in {path})")
    if wait_set_time < 0:
        raise MonitorBossError(f"invalid wait set time: {wait_set_time}")
    doc = __read_toml(path)
    doc[TomlCategories.settings.value][TomlSettingsKeys.wait_set.value] = wait_set_time
    __write_toml(doc, path)


def reset_config(path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"reset config to default: {path}")
    __write_toml(default_toml(), path)
