from enum import Enum  # cannot use StrEnum, it's not in Python 3.10
from logging import getLogger
from pathlib import Path

from tomlkit import parse, dump, document, table, TOMLDocument
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from monitorboss import MonitorBossError
from pyddc import get_vcp_com
from pyddc.vcp_codes import VCPCodes

_log = getLogger(__name__)

DEFAULT_CONF_FILE_LOC = "./conf/MonitorBoss.toml"


class TomlCategories(Enum):
    monitors = "monitor_names"
    features = "feature_aliases"
    settings = "settings"
    values = "value_aliases"


class TomlSettingsKeys(Enum):
    wait_get = "wait_get"
    wait_set = "wait_set"
    wait_internal = "wait_internal"


class _RawTomlSettings(BaseModel):
    """
    Pydantic model for the [settings] section of the TOML file.
    Fixed-schema sub-model: all keys are known and required.
    """
    wait_get: float
    wait_set: float
    wait_internal: float

    @field_validator("wait_get", "wait_set", "wait_internal")
    @classmethod
    def validate_wait_times(cls, v: float) -> float:
        """Wait times must be non-negative."""
        if v < 0:
            raise ValueError(f"Wait times must be non-negative, got {v}")
        return v


class _RawTomlConfig(BaseModel):
    """
    Pydantic model mirroring the exact TOML structure before inversion.
    This model handles shape validation: ensuring monitor_names, feature_aliases,
    value_aliases exist with the right type structure (dict with string/list values),
    and that settings is properly typed and valid.

    Monitor IDs in TOML are keys (strings): {id_str: alias_or_list}
    Feature codes in TOML are keys (strings): {code_str: alias_or_list}
    Value aliases in TOML are nested: {feature_name: {value_str: alias_or_list}}

    All keys are user-defined (variable schema), so they remain as dicts, not sub-models.

    Validation rules enforced by field validators:
    - monitor_names keys: must be non-negative integer strings
    - feature_aliases keys: must be non-negative integers corresponding to valid VCP commands
    - value_aliases inner keys (per feature sub-table): must be non-negative integer strings
    - value_aliases outer keys (feature names): must correspond to valid VCP command names
    - All alias strings (TOML values): must not be numeric (would be indistinguishable from bare IDs at runtime)
    - Aliases must not be duplicated within the same table (monitor_names, feature_aliases),
      or within the same feature sub-table (value_aliases); cross-sub-table duplicates are allowed
    """
    monitor_names: dict[str, str | list[str]]
    feature_aliases: dict[str, str | list[str]]
    value_aliases: dict[str, dict[str, str | list[str]]] = {}
    settings: _RawTomlSettings

    @field_validator("monitor_names")
    @classmethod
    def validate_monitor_names(cls, v: dict[str, str | list[str]]) -> dict[str, str | list[str]]:
        """Monitor IDs (keys) must be non-negative integers; aliases (values) must not be numeric or duplicated."""
        errors: list[str] = []
        seen_aliases: set[str] = set()
        for mon_id_str, aliases in v.items():
            if not mon_id_str.isdecimal():
                errors.append(f"Monitor IDs must be non-negative integers, got: {mon_id_str!r}")
                continue  # key is invalid; alias checks for this entry are meaningless
            alias_list = aliases if isinstance(aliases, list) else [aliases]
            for alias in alias_list:
                if alias.isdecimal():
                    errors.append(f"Monitor aliases can not be numeric: {alias}")
                elif alias in seen_aliases:
                    errors.append(f"Monitor alias is used multiple times: {alias!r}")
                else:
                    seen_aliases.add(alias)
        if errors:
            raise ValueError("\n".join(errors))
        return v

    @field_validator("feature_aliases")
    @classmethod
    def validate_feature_aliases(cls, v: dict[str, str | list[str]]) -> dict[str, str | list[str]]:
        """Feature codes (keys) must be non-negative integers corresponding to valid VCP commands;
        aliases (values) must not be numeric or duplicated."""
        errors: list[str] = []
        seen_aliases: set[str] = set()
        for code_str, aliases in v.items():
            if not code_str.isdecimal():
                errors.append(f"Feature codes must be non-negative integers, got: {code_str!r}")
                continue  # key is invalid; alias checks for this entry are meaningless
            code = int(code_str)
            if get_vcp_com(code) is None:
                errors.append(f"Feature code {code} does not correspond to a valid command, can not be aliased")
                continue  # code is invalid; alias checks for this entry are meaningless
            alias_list = aliases if isinstance(aliases, list) else [aliases]
            for alias in alias_list:
                if alias.isdecimal():
                    errors.append(f"Feature aliases can not be numeric: {alias}")
                elif alias in seen_aliases:
                    errors.append(f"Feature alias is used multiple times: {alias!r}")
                else:
                    seen_aliases.add(alias)
        if errors:
            raise ValueError("\n".join(errors))
        return v

    @field_validator("value_aliases")
    @classmethod
    def validate_value_aliases(cls, v: dict[str, dict[str, str | list[str]]]) -> dict[str, dict[str, str | list[str]]]:
        """Feature names (outer keys) must be valid VCP commands. Inner value keys must be non-negative integers;
        aliases must not be numeric or duplicated within a sub-table."""
        errors: list[str] = []
        for feature_name, value_map in v.items():
            # Validate that feature_name corresponds to a valid VCP command
            if get_vcp_com(feature_name) is None:
                errors.append(f"Value aliases feature name {feature_name!r} does not correspond to a valid command")
                continue  # Skip further validation for this invalid feature
            
            seen_aliases: set[str] = set()
            for val_str, aliases in value_map.items():
                if not val_str.isdecimal():
                    errors.append(
                        f"Value IDs must be non-negative integers in feature {feature_name!r}, got: {val_str!r}")
                    continue  # key is invalid; alias checks for this entry are meaningless
                alias_list = aliases if isinstance(aliases, list) else [aliases]
                for alias in alias_list:
                    if alias.isdecimal():
                        errors.append(f"Value aliases can not be numeric: {alias}")
                    elif alias in seen_aliases:
                        errors.append(
                            f"Value alias is used multiple times in feature {feature_name!r}: {alias!r}")
                    else:
                        seen_aliases.add(alias)
        if errors:
            raise ValueError("\n".join(errors))
        return v


class Config(BaseModel):
    """
    Runtime-ready configuration model after TOML inversion.
    Aliases are now keys: {alias_str: id_int}, feature codes are inverted similarly.
    This model is frozen (immutable) since the tool runs stateless: config is loaded once,
    used for an operation, then the tool exits. frozen=True prevents any mutation.
    Note: We don't leverage hashing (frozen enables it, but Config is never used as a dict key).
    All validation is performed upstream in _RawTomlSettings and _RawTomlConfig.
    """
    model_config = ConfigDict(frozen=True)

    monitor_names: dict[str, int]
    feature_aliases: dict[str, int]
    value_aliases: dict[str, dict[str, int]]
    wait_get_time: float
    wait_set_time: float
    wait_internal_time: float

    @classmethod
    def from_raw(cls, raw: _RawTomlConfig) -> "Config":
        """
        Convert from raw TOML structure to runtime-ready Config.
        Performs the alias inversion: {id: [aliases]} -> {alias: id}
        Also maps raw settings field names to Config field names.
        All validation is handled upstream by field validators on _RawTomlSettings and _RawTomlConfig.
        """
        _log.debug("Converting raw TOML config to runtime Config via inversion")

        # Invert monitor aliases: TOML {mon_id_str: alias_or_list} -> Config {alias_str: mon_id_int}
        monitor_names: dict[str, int] = {}
        for mon_id_str, aliases in raw.monitor_names.items():
            mon_id = int(mon_id_str)
            alias_list = aliases if isinstance(aliases, list) else [aliases]
            for alias in alias_list:
                monitor_names[alias] = mon_id

        # Invert feature aliases: TOML {code_str: alias_or_list} -> Config {alias_str: code_int}
        feature_aliases: dict[str, int] = {}
        for code_str, aliases in raw.feature_aliases.items():
            code = int(code_str)
            alias_list = aliases if isinstance(aliases, list) else [aliases]
            for alias in alias_list:
                feature_aliases[alias] = code

        # Invert value aliases: TOML {feature: {val_str: alias_or_list}} -> Config {feature: {alias: val_int}}
        value_aliases: dict[str, dict[str, int]] = {}
        for feature_name, value_map in raw.value_aliases.items():
            value_aliases[feature_name] = {}
            for val_str, aliases in value_map.items():
                val_int = int(val_str)
                alias_list = aliases if isinstance(aliases, list) else [aliases]
                for alias in alias_list:
                    value_aliases[feature_name][alias] = val_int

        return cls(
            monitor_names=monitor_names,
            feature_aliases=feature_aliases,
            value_aliases=value_aliases,
            wait_get_time=raw.settings.wait_get,
            wait_set_time=raw.settings.wait_set,
            wait_internal_time=raw.settings.wait_internal,
        )


def default_toml() -> TOMLDocument:
    _log.debug("define default TOML config")
    mon_names = table()
    mon_names.add("0", "main")

    feature_aliases = table()
    feature_aliases.add("16", ['lum', 'luminance', 'brightness'])
    feature_aliases.add("18", ['cnt', 'contrast'])
    feature_aliases.add("20", ['clr', 'color', 'clrpreset'])
    feature_aliases.add("96", ['src', 'source', 'input'])
    feature_aliases.add("214", ['pwr', 'power', 'powermode'])

    input_names = table()
    input_names.add("27", ["usbc", "usb_c", "usb-c"])
    input_names["27"].comment('27 seems to be the "standard non-standard" ID for USB-C among manufacturers')
    display_power_names = table()
    display_power_names.add("3", "sleep")
    value_aliases = table()
    value_aliases.add(get_vcp_com(VCPCodes.input_source).name, input_names)
    value_aliases.add(get_vcp_com(VCPCodes.display_power_mode).name, display_power_names)

    settings = table()
    settings.add(TomlSettingsKeys.wait_get.value, 0.05)
    settings.add(TomlSettingsKeys.wait_set.value, 0.1)
    settings.add(TomlSettingsKeys.wait_internal.value, 0.04)

    doc = document()
    doc.add(TomlCategories.monitors.value, mon_names)
    doc.add(TomlCategories.features.value, feature_aliases)
    doc.add(TomlCategories.values.value, value_aliases)
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
    _log.debug(f"get Config from: {Path(path).absolute()}")
    try:
        doc = _read_toml(path)
        # Unwrap tomlkit types to plain Python dict/list/etc for Pydantic
        unwrapped = doc.unwrap()
        # Validate against raw TOML structure (including alias validation)
        raw_cfg = _RawTomlConfig.model_validate(unwrapped)
        # Convert to runtime-ready Config (performs alias inversion and field mapping)
        cfg = Config.from_raw(raw_cfg)
        _log.debug(f"Successfully loaded Config from {Path(path).absolute()}")
        return cfg
    except ValidationError as err:
        raise MonitorBossError(f"Invalid config at {Path(path).absolute()}: {err}") from err
    except MonitorBossError:
        raise
    except Exception as err:
        raise MonitorBossError(f"Could not load config from {Path(path).absolute()}: {err}") from err


def reset_config(path: str | None):
    path = path if path is not None else DEFAULT_CONF_FILE_LOC
    _log.debug(f"reset config to default: {Path(path).absolute()}")
    _write_toml(default_toml(), path)
