import base64
import binascii
from enum import Enum
from logging import getLogger
from pathlib import Path
from typing import Optional

import pyedid
from pydantic import BaseModel, ConfigDict, field_validator
from tomlkit import TOMLDocument, document, table

from monitorboss import MonitorBossError
from monitorboss.util import validate_non_negative_wait, read_toml_file, write_toml_file, toml_load_errors
from pyddc import get_vcp_com

_log = getLogger(__name__)

DEFAULT_PROFILE_DIR: str = str(Path(__file__).parent.parent / "conf" / "profiles")


class ProfileTomlCategories(Enum):
    identity = "identity"
    capabilities = "capabilities"
    max_values = "max_values"
    value_redirects = "value_redirects"
    settings = "settings"


class ProfileTomlSettingsKeys(Enum):
    wait_get = "wait_get"
    wait_set = "wait_set"
    wait_internal = "wait_internal"


class _RawTomlIdentity(BaseModel):
    """Fixed-schema sub-model for the [identity] table. All six fields are required."""
    model_config = ConfigDict(extra='forbid')

    pnpid: str
    model: str
    serial: str
    year: int
    week: int
    edid_128_base64: str

    @field_validator("edid_128_base64")
    @classmethod
    def validate_edid_base64(cls, v: str) -> str:
        """Validate that edid_128_base64 is valid base64 encoding of exactly 128 bytes."""
        try:
            decoded = base64.b64decode(v, validate=True)
        except (binascii.Error, ValueError) as err:
            raise ValueError(f"edid_128_base64 is not valid base64: {err}") from err
        if len(decoded) != 128:
            raise ValueError(f"edid_128_base64 must decode to exactly 128 bytes, got {len(decoded)}")
        return v


class _RawTomlCapabilities(BaseModel):
    """Fixed-schema sub-model for the [capabilities] table."""
    model_config = ConfigDict(extra='forbid')

    raw: str


class _RawTomlProfileSettings(BaseModel):
    """Sub-model for the [settings] table in a profile. All fields optional (None = use global config)."""
    model_config = ConfigDict(extra='forbid')

    wait_get: Optional[float] = None
    wait_set: Optional[float] = None
    wait_internal: Optional[float] = None

    @field_validator("wait_get", "wait_set", "wait_internal")
    @classmethod
    def validate_wait_times(cls, v: Optional[float]) -> Optional[float]:
        """Wait times must be non-negative when present."""
        return validate_non_negative_wait(v)


class _RawTomlProfile(BaseModel):
    """Top-level raw model mirroring the full TOML profile document."""
    model_config = ConfigDict(extra='forbid')

    identity: _RawTomlIdentity
    capabilities: _RawTomlCapabilities
    max_values: dict[str, int]
    value_redirects: dict[str, dict[str, int]]
    settings: _RawTomlProfileSettings

    @field_validator("max_values")
    @classmethod
    def validate_max_values(cls, v: dict[str, int]) -> dict[str, int]:
        """Keys must be decimal VCP code strings; values must be non-negative."""
        errors: list[str] = []
        for key, val in v.items():
            if not key.isdecimal():
                errors.append(f"max_values keys must be non-negative integer VCP codes, got: {key!r}")
                continue
            if get_vcp_com(int(key)) is None:
                errors.append(f"max_values key {key} does not correspond to a valid VCP command")
                continue
            if val < 0:
                errors.append(f"max_values values must be non-negative, got {val} for key {key!r}")
        if errors:
            raise ValueError("\n".join(errors))
        return v

    @field_validator("value_redirects")
    @classmethod
    def validate_value_redirects(cls, v: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
        """Outer keys must be valid VCP command names; inner keys must be decimal strings; inner values non-negative."""
        errors: list[str] = []
        for feature_name, redirect_map in v.items():
            if get_vcp_com(feature_name) is None:
                errors.append(f"value_redirects feature name {feature_name!r} does not correspond to a valid command")
                continue
            for inner_key, inner_val in redirect_map.items():
                if not inner_key.isdecimal():
                    errors.append(
                        f"value_redirects inner keys must be non-negative integer strings in feature "
                        f"{feature_name!r}, got: {inner_key!r}"
                    )
                    continue
                if inner_val < 0:
                    errors.append(
                        f"value_redirects inner values must be non-negative, got {inner_val} "
                        f"for feature {feature_name!r}, key {inner_key!r}"
                    )
        if errors:
            raise ValueError("\n".join(errors))
        return v


class MonitorIdentity(BaseModel):
    """Frozen runtime model for monitor identity data."""
    model_config = ConfigDict(frozen=True)

    pnpid: str
    model: str
    serial: str
    year: int
    week: int
    edid_128_base64: str


class MonitorProfile(BaseModel):
    """Frozen runtime model for a monitor profile."""
    model_config = ConfigDict(frozen=True)

    identity: MonitorIdentity
    capabilities: str
    max_values: dict[int, int]
    value_redirects: dict[str, dict[int, int]]
    wait_get_time: Optional[float]
    wait_set_time: Optional[float]
    wait_internal_time: Optional[float]

    @classmethod
    def from_raw(cls, raw: _RawTomlProfile) -> "MonitorProfile":
        """Convert from raw TOML structure to runtime-ready MonitorProfile."""
        _log.debug("Converting raw TOML profile to runtime MonitorProfile")

        identity = MonitorIdentity(
            pnpid=raw.identity.pnpid,
            model=raw.identity.model,
            serial=raw.identity.serial,
            year=raw.identity.year,
            week=raw.identity.week,
            edid_128_base64=raw.identity.edid_128_base64,
        )

        max_values: dict[int, int] = {int(k): v for k, v in raw.max_values.items()}

        value_redirects: dict[str, dict[int, int]] = {
            feature: {int(k): v for k, v in redirect_map.items()}
            for feature, redirect_map in raw.value_redirects.items()
        }

        return cls(
            identity=identity,
            capabilities=raw.capabilities.raw,
            max_values=max_values,
            value_redirects=value_redirects,
            wait_get_time=raw.settings.wait_get,
            wait_set_time=raw.settings.wait_set,
            wait_internal_time=raw.settings.wait_internal,
        )


def new_profile_toml(edid_blob: bytes, caps_str: str) -> TOMLDocument:
    """Build a foundational profile TOMLDocument from a raw EDID blob and a capabilities string.

    The returned document contains all five required top-level tables.  The
    ``[identity]`` and ``[capabilities]`` tables are populated from the supplied
    data; ``[max_values]``, ``[value_redirects]``, and ``[settings]`` are present
    but intentionally empty, ready for the user to fill in.

    Args:
        edid_blob: Raw EDID bytes.  Only the first 128 bytes are used for the profile
        caps_str: The raw DDC/CI capabilities string as reported by the monitor.

    Returns:
        A ``TOMLDocument`` matching the structure of ``conf/profiles/example_profile.toml``.

    Raises:
        MonitorBossError: If the EDID blob cannot be parsed.
    """
    _log.debug("building new profile TOML from EDID blob and capabilities string")
    try:
        edid = pyedid.parse_edid(edid_blob)
    except Exception as err:
        raise MonitorBossError(f"could not parse EDID blob: {err}") from err

    edid_128_base64 = base64.b64encode(edid_blob[:128]).decode("utf-8")

    identity = table()
    identity.add("pnpid", edid.manufacturer_pnp_id)
    identity.add("model", edid.name)
    identity.add("serial", edid.serial)
    identity.add("year", edid.year)
    identity.add("week", edid.week)
    identity.add("edid_128_base64", edid_128_base64)

    caps = table()
    caps.comment(
        "The capabilities string of the monitor, cached for parsing purposes."
        " THIS SHOULD NOT BE MANUALLY EDITED."
    )
    caps.add("raw", caps_str)

    doc = document()
    doc.add(ProfileTomlCategories.identity.value, identity)
    doc.add(ProfileTomlCategories.capabilities.value, caps)
    doc.add(ProfileTomlCategories.max_values.value, table())
    doc.add(ProfileTomlCategories.value_redirects.value, table())
    doc.add(ProfileTomlCategories.settings.value, table())

    return doc


def get_profile(path: str) -> MonitorProfile:
    """Load and return a MonitorProfile from the TOML file at path."""
    _log.debug(f"get MonitorProfile from: {Path(path).absolute()}")
    with toml_load_errors(path, "profile"):
        doc = read_toml_file(path, "profile")
        unwrapped = doc.unwrap()
        raw_profile = _RawTomlProfile.model_validate(unwrapped)
        profile = MonitorProfile.from_raw(raw_profile)
        _log.debug(f"Successfully loaded MonitorProfile from {Path(path).absolute()}")
        return profile


def write_profile(doc: TOMLDocument, dir_path: str | None, filename: str) -> None:
    """Write a profile TOMLDocument to a file within the profile's directory.

    Args:
        doc: The ``TOMLDocument`` to write.
        dir_path: Directory in which to write the file. Defaults to
            ``DEFAULT_PROFILE_DIR`` when ``None``.
        filename: Name of the profile file (e.g. ``"my_monitor.toml"``).
    """
    dir_path = dir_path if dir_path is not None else DEFAULT_PROFILE_DIR
    path = str(Path(dir_path) / filename)
    _log.debug(f"write profile to: {Path(path).absolute()}")
    write_toml_file(path, "profile", doc)


