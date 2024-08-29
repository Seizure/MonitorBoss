from enum import Enum # cannot use StrEnum, it's not in Python 3.10
from logging import getLogger
from pathlib import Path
from dataclasses import dataclass, field

from tomlkit import parse, dump, comment, document, table, TOMLDocument
from tomlkit.items import Array, String, Trivia

from monitorboss import MonitorBossError

_log = getLogger(__name__)

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.toml"


class TomlCategories(Enum):
    monitors = "monitor_names"
    features = "feature_aliases"
    inputs = "input_names"
    settings = "settings"


class TomlSettingsKeys(Enum):
    wait_get = "wait_get"
    wait_set = "wait_set"
    wait_internal = "wait_internal"


@dataclass
class Config:
    monitor_names: dict[str, int] = field(default_factory=dict)
    feature_aliases: dict[str, int] = field(default_factory=dict)
    input_source_names: dict[str, int] = field(default_factory=dict)
    wait_get_time: float = field(default_factory=float)
    wait_set_time: float = field(default_factory=float)
    wait_internal_time: float = field(default_factory=float)

    # TODO: why are we allowing for non-numeric keys?
    def read(self, doc: TOMLDocument):
        _log.debug(f"read Config from TOML doc: {doc}")
        for val, aliases in doc[TomlCategories.monitors.value].items():
            if isinstance(aliases, String):
                aliases = Array([aliases], Trivia())
            for alias in aliases:
                self.monitor_names[alias] = int(val) if val.isdigit() else val
        for val, aliases in doc[TomlCategories.features.value].items():
            if isinstance(aliases, String):
                aliases = Array([aliases], Trivia())
            for alias in aliases:
                self.feature_aliases[alias] = int(val) if val.isdigit else val
        for val, aliases in doc[TomlCategories.inputs.value].items():
            if isinstance(aliases, String):
                aliases = Array([aliases], Trivia())
            for alias in aliases:
                self.input_source_names[alias] = int(val) if val.isdigit() else val
        self.wait_get_time = doc[TomlCategories.settings.value][TomlSettingsKeys.wait_get.value]
        self.wait_set_time = doc[TomlCategories.settings.value][TomlSettingsKeys.wait_set.value]
        self.wait_internal_time = doc[TomlCategories.settings.value][TomlSettingsKeys.wait_internal.value]

    def validate(self):
        _log.debug(f"validate config")
        if self.wait_get_time < 0:
            raise MonitorBossError(f"invalid wait get time: {self.wait_get_time}")
        if self.wait_set_time < 0:
            raise MonitorBossError(f"invalid wait set time: {self.wait_set_time}")
        if self.wait_internal_time < 0:
            raise MonitorBossError(f"invalid wait internal time: {self.wait_internal_time}")


def default_toml() -> TOMLDocument:
    _log.debug("define default TOML config")
    mon_names = table()
    mon_names.add("0", "main")

    input_names = table()
    input_names.add("27", ["usbc", "usb_c", "usb-c"])
    input_names["27"].comment('27 seems to be the "standard non-standard" ID for USB-C among manufacturers')

    settings = table()
    settings.add(TomlSettingsKeys.wait_get.value, 0.05)
    settings.add(TomlSettingsKeys.wait_set.value, 0.1)
    settings.add(TomlSettingsKeys.wait_internal.value, 0.04)

    doc = document()
    doc.add(TomlCategories.monitors.value, mon_names)
    doc.add(TomlCategories.inputs.value, input_names)
    doc.add(TomlCategories.settings.value, settings)

    return doc


def _read_toml(path: str | None) -> TOMLDocument:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"read TOML config from: {Path(path).absolute()}")
    if not Path(path).parent.exists():
        Path(path).parent.mkdir(parents=True)
    if not Path(path).exists():
        reset_config(path)
    try:
        with open(path, "r", encoding="utf8") as file:
            content = file.read()
    except Exception as err:
        raise MonitorBossError(f"could not read config file: {Path(path).absolute()}") from err
    try:
        return parse(content)
    except Exception as err:
        # TODO: add CLI options to manage the config
        raise MonitorBossError(
            f"could not parse config file: {path}: {err}\n"
            "To reset the config file to its default content, delete the file."
        ) from err


def _write_toml(doc: TOMLDocument, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"write TOML config to: {Path(path).absolute()}")
    if not Path(path).parent.exists():
        Path(path).parent.mkdir(parents=True)
    try:
        with open(path, "w", encoding="utf8") as file:
            dump(doc, file)
    except Exception as err:
        raise MonitorBossError(f"could not write config file: {Path(path).absolute()}") from err


def get_config(path: str | None) -> Config:
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"get Config dataclass from: {Path(path).absolute()}")
    doc = _read_toml(path)
    cfg = Config()
    try:
        cfg.read(doc)
    except Exception as err:
        raise MonitorBossError(f"could not parse config file: {Path(path).absolute()}: {err}") from err
    cfg.validate()
    return cfg


def set_monitor_alias(alias: str, mon_id: int, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set monitor alias: {alias} = {mon_id} (in {Path(path).absolute()})")
    doc = _read_toml(path)
    doc[TomlCategories.monitors.value][alias] = mon_id
    _write_toml(doc, path)


def remove_monitor_alias(alias: str, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"remove monitor alias: {alias} (in {Path(path).absolute()})")
    doc = _read_toml(path)
    doc.remove(doc[TomlCategories.monitors.value][alias])
    _write_toml(doc, path)


def set_input_alias(alias: str, input_id: int, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set input alias: {alias} = {input_id} (in {Path(path).absolute()})")
    doc = _read_toml(path)
    doc[TomlCategories.inputs.value][alias] = input_id
    _write_toml(doc, path)


def remove_input_alias(alias: str, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"remove input alias: {alias} (in {Path(path).absolute()})")
    doc = _read_toml(path)
    doc.remove(doc[TomlCategories.inputs.value][alias])
    _write_toml(doc, path)


def set_wait_get_time(wait_get_time: float, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set wait get time: {wait_get_time} (in {Path(path).absolute()})")
    if wait_get_time < 0:
        raise MonitorBossError(f"invalid wait get time: {wait_get_time}")
    doc = _read_toml(path)
    doc[TomlCategories.settings.value][TomlSettingsKeys.wait_get.value] = wait_get_time
    _write_toml(doc, path)


def set_wait_set_time(wait_set_time: float, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set wait set time: {wait_set_time} (in {Path(path).absolute()})")
    if wait_set_time < 0:
        raise MonitorBossError(f"invalid wait set time: {wait_set_time}")
    doc = _read_toml(path)
    doc[TomlCategories.settings.value][TomlSettingsKeys.wait_set.value] = wait_set_time
    _write_toml(doc, path)


def set_wait_internal_time(wait_internal_time: float, path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"set wait internal time: {wait_internal_time} (in {Path(path).absolute()})")
    if wait_internal_time < 0:
        raise MonitorBossError(f"invalid wait internal time: {wait_internal_time}")
    doc = _read_toml(path)
    doc[TomlCategories.settings.value][TomlSettingsKeys.wait_internal.value] = wait_internal_time
    _write_toml(doc, path)


def reset_config(path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"reset config to default: {Path(path).absolute()}")
    _write_toml(default_toml(), path)
