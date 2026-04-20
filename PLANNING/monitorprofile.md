# Implementation Plan: `monitorboss/profile.py`

## Overview

`profile.py` introduces per-monitor TOML profile files to MonitorBoss. Each profile stores monitor identity (EDID-derived), a cached capabilities string, per-feature max values, value redirects (for silently aliased inputs), and per-feature timing overrides.

All five top-level tables are **required** and must be present in the TOML file. However, `[max_values]`, `[value_redirects]`, and `[settings]` may have entirely empty contents. The `[identity]` and `[capabilities]` tables always have required fields.

The module follows the two-stage Pydantic validation pattern established in `config.py`: raw TOML structure is validated by `_RawToml*` models, then transformed into frozen runtime models (`MonitorIdentity` and `MonitorProfile`) via a `from_raw()` class method.

The example profile at `conf/profiles/example_profile.toml` demonstrates the expected TOML structure and can be referenced when writing new profiles.

Logging follows the standard pattern per AGENTS.md: `_log = getLogger(__name__)`.

---

## Constants

- `DEFAULT_PROFILE_DIR: str = "./conf/profiles"` — mirrors `DEFAULT_CONF_FILE_LOC` in `config.py`. Individual profile files within this directory are addressed by their full path; the directory constant is a convenience reference for callers (e.g., CLI lookup or file listing).

---

## TOML Section Enums

Two enums, mirroring `TomlCategories` and `TomlSettingsKeys` in `config.py`:

- **`ProfileTomlCategories`** — one member per top-level TOML section: `identity`, `capabilities`, `max_values`, `value_redirects`, `settings`. Each member has a string value matching the TOML section name.

- **`ProfileTomlSettingsKeys`** — same three members as `TomlSettingsKeys`: `wait_get`, `wait_set`, `wait_internal`. Mirrors `TomlSettingsKeys` for consistency. Note: these enum values are **not** used during TOML parsing — Pydantic maps TOML keys to model fields by matching field names directly. As with `TomlSettingsKeys`, they exist solely for TOML construction/generation (e.g. a future `default_profile_toml()` equivalent). They have no callers in the current implementation scope.

---

## Pydantic Model Design

All **raw** models (`_RawTomlIdentity`, `_RawTomlCapabilities`, `_RawTomlProfileSettings`, `_RawTomlProfile`) are configured with `extra='forbid'` — unknown keys at any level of the TOML input are a validation error. Runtime models (`MonitorIdentity`, `MonitorProfile`) carry only `frozen=True`; they are constructed by trusted application code and do not need input-boundary validation.

### `_RawTomlIdentity`

Fixed-schema sub-model for the `[identity]` table. All six fields are required.

| Field             | Type  | Notes                                                                              |
|-------------------|-------|------------------------------------------------------------------------------------|
| `pnpid`           | `str` | 3-letter PnP manufacturer ID from EDID (e.g., `"DEL"` for Dell)                    |
| `model`           | `str` | Human-readable model name from the EDID monitor name descriptor                    |
| `serial`          | `str` | Serial number string from the EDID serial number descriptor                        |
| `year`            | `int` | Manufacturing year from EDID                                                       |
| `week`            | `int` | Manufacturing week from EDID                                                       |
| `edid_128_base64` | `str` | Base64-encoded first 128 bytes of EDID — the definitive unique monitor fingerprint |

A `@field_validator` on `edid_128_base64` decodes the value via `base64.b64decode(v, validate=True)` and asserts `len(decoded) == 128`, rejecting any malformed or wrong-length fingerprint. Using `validate=True` ensures that strings containing non-base64 characters raise `binascii.Error` (a `ValueError` subclass) rather than being silently stripped before the length check.

---

### `_RawTomlCapabilities`

Fixed-schema sub-model for the `[capabilities]` table. Contains a single required field:

- `raw: str` — the raw DDC/CI capabilities string as reported by the monitor

---

### `_RawTomlProfileSettings`

Sub-model for the `[settings]` table in a profile. The `[settings]` table is required, but all three fields are `Optional[float]` — an absent field means "use the global config value". An entirely empty `[settings]` table is valid (all three fields will be `None`):

- `wait_get: Optional[float] = None`
- `wait_set: Optional[float] = None`
- `wait_internal: Optional[float] = None`

A `@field_validator` on all three fields enforces non-negativity when a value is present (same logic as `_RawTomlSettings.validate_wait_times` in `config.py`).

---

### `_RawTomlProfile`

Top-level raw model. All five tables are required, though `[max_values]`, `[value_redirects]`, and `[settings]` may have empty contents. Mirrors the full TOML profile document:

```
identity:         _RawTomlIdentity
capabilities:     _RawTomlCapabilities
max_values:       dict[str, int]
value_redirects:  dict[str, dict[str, int]]
settings:         _RawTomlProfileSettings
```

**Field validator: `validate_max_values`**

Applied to `max_values: dict[str, int]`. Checks:
- Each key is a decimal string (non-negative integer VCP feature code)
- Each key corresponds to a valid VCP command code (via `get_vcp_com(int(key))`)
- Each value is non-negative (represents the maximum value the monitor reports for that feature)

**Field validator: `validate_value_redirects`**

Applied to `value_redirects: dict[str, dict[str, int]]`. Checks:
- Each outer key is a valid VCP command name (via `get_vcp_com(outer_key)`)
- Each inner key is a decimal string (the original/standard value the caller sends)
- Each inner value is non-negative (the value the monitor actually expects; used when a monitor silently remaps a standard value to a non-standard one, e.g. treating DP2 as USB-C)

Both validators accumulate all errors before raising, following the pattern in `_RawTomlConfig.validate_feature_aliases` and `validate_value_aliases`.

---

### `MonitorIdentity`

Frozen runtime model for identity data (`model_config = ConfigDict(frozen=True)`). Fields are a direct pass-through from `_RawTomlIdentity` (no inversion or key transformation needed — identity fields are a simple 1-to-1 mapping):

```
pnpid:             str
model:             str
serial:            str
year:              int
week:              int
edid_128_base64:   str
```

---

### `MonitorProfile`

Frozen runtime model (`model_config = ConfigDict(frozen=True)`). Produced by `MonitorProfile.from_raw()`. `settings` fields are aligned with `Config`:

```
identity:            MonitorIdentity
capabilities:        str
max_values:          dict[int, int]
value_redirects:     dict[str, dict[int, int]]
wait_get_time:       float | None
wait_set_time:       float | None
wait_internal_time:  float | None
```

Settings fields are flattened out of the sub-model (as `Config` flattens `_RawTomlSettings` into `wait_get_time`, etc.) and use the same field names. `None` means "no profile override for this setting".

---

## Data Transformations in `MonitorProfile.from_raw()`

`from_raw(raw: _RawTomlProfile) -> "MonitorProfile"` performs the following transformations:

1. **`identity`** — construct `MonitorIdentity` directly from `raw.identity` fields (no transformation).

2. **`capabilities`** — extract `raw.capabilities.raw` directly.

3. **`max_values`** — convert string keys to `int`: `{str: int}` → `{int: int}` using `int(k)` for each key.

4. **`value_redirects`** — convert inner string keys to `int`: `{str: {str: int}}` → `{str: {int: int}}` using `int(k)` for each inner key. Outer keys (VCP command names) are passed through unchanged.

5. **`wait_get_time / wait_set_time / wait_internal_time`** — mapped from `raw.settings.wait_get / wait_set / wait_internal` respectively, aligning raw TOML key names to runtime field names in the same manner as `Config.from_raw()`.

---

## Public API

### `_read_toml_profile(path: str) -> TOMLDocument`

Reads and parses the TOML file at `path`, returning a raw `TOMLDocument`. This mirrors `_read_toml()` in `config.py`. Raises `MonitorBossError` on read or parse failure. Unlike `_read_toml()`, this function does **not** auto-create a missing file — profiles are created externally.

### `get_profile(path: str) -> MonitorProfile`

Unlike `get_config()`, this function does not accept `None` as a path (profiles do not have a single well-known default path). The function:

1. Calls `_read_toml_profile(path)` to read and parse the TOML file (first stage: reading/parsing).
2. Unwraps `tomlkit` types to plain Python via `.unwrap()`.
3. Validates with `_RawTomlProfile.model_validate()`, wrapping `ValidationError` in `MonitorBossError`.
4. Returns `MonitorProfile.from_raw(raw)`.

Error handling follows the same `try/except` layering as `get_config()`:
- `ValidationError` → `MonitorBossError`
- `MonitorBossError` → re-raise
- Any other `Exception` → `MonitorBossError`

Two-stage error handling: first stage (reading/parsing TOML) handled by `_read_toml_profile`, second stage (validation and transformation) handled by `get_profile`. Consider code deduplication with `config.py` in future refactoring, but keep the current implementation as specified.

**Note:** `get_profile()` does **not** auto-create a missing profile. Profiles are created externally (e.g., by a future `profile save` CLI command or manual authoring).

---

## Tests

The test suite for `profile.py` mirrors the structure in `test/monitorboss/test_config_units.py`. New additions are needed across three files.

### `test/testdata.py`

- **`TEST_PROFILE_TOML_CONTENTS`** — a valid profile TOML string exercising all five required tables, including non-empty `max_values`, `value_redirects`, and `settings`. Uses the existing `edid_blob` (128 bytes, base64-encoded) and the `caps_str` from `vcp_template`. This string is self-contained test data and must not reference or depend on any on-disk profile file (e.g. `conf/profiles/example_profile.toml`), following the same pattern as `TEST_TOML_CONTENTS`.

### `test/conftest.py`

Two new module-scoped fixtures analogous to `test_conf_file` / `test_cfg`:

- **`test_profile_file`** — writes `TEST_PROFILE_TOML_CONTENTS` to a temporary file; returns the `Path`.
- **`test_profile`** — loads and returns `MonitorProfile` via `get_profile(test_profile_file.as_posix())`.

### `test/monitorboss/test_profile_units.py`

At the module level, analogous to `CONFIG_DICT_TEMPLATE` in `test/monitorboss/test_config_units.py`:

- **`PROFILE_IDENTITY_TEMPLATE`** — a dict of all six valid identity fields (including the base64-encoded `edid_blob` from `testdata`), used as a base for constructing `_RawTomlProfile` instances in parametrized tests.

- **`PROFILE_DICT_TEMPLATE`** — top-level base dict for constructing `_RawTomlProfile` instances in parametrized tests, analogous to `CONFIG_DICT_TEMPLATE`. Fields and their values:
  - `identity`: `PROFILE_IDENTITY_TEMPLATE`
  - `capabilities`: `_RawTomlCapabilities(raw="")`
  - `max_values`: `{}`
  - `value_redirects`: `{}`
  - `settings`: `_RawTomlProfileSettings()` (all fields default to `None`)

  Using model instances for `capabilities` and `settings` is consistent with how `CONFIG_DICT_TEMPLATE` uses a `_RawTomlSettings(...)` instance for its `settings` key.

**`TestProfileValidation`** class:

| Test                                                          | Case(s)                                                                                                                                                   | Expected                                                                                                                                                                                                                                                                                         |
|---------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `test_profile_valid_round_trip` (uses `test_profile` fixture) | Full parse of `TEST_PROFILE_TOML_CONTENTS`                                                                                                                | All fields match expected values: `identity` fields match `PROFILE_IDENTITY_TEMPLATE`, `capabilities` matches `caps_str`, `max_values` is `{16: 100, 18: 100}`, `value_redirects` is `{"input_source": {16: 27}}`, `wait_get_time` is 0.05, `wait_set_time` is 0.1, `wait_internal_time` is 0.04 |
| `test_identity_invalid_rejected` (parametrized)               | Extra field in `[identity]`; `edid_128_base64` wrong decoded length; invalid base64 string; missing required field (e.g., missing `pnpid`, `model`, etc.) | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_capabilities_invalid_rejected` (parametrized)           | Extra field in `[capabilities]`; missing required `raw` field                                                                                             | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_settings_invalid_rejected` (parametrized)               | `wait_get < 0`; `wait_set < 0`; `wait_internal < 0`; extra field in settings                                                                              | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_raw_profile_missing_required_table` (parametrized)      | Each of the 5 required top-level tables omitted individually                                                                                              | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_raw_profile_extra_field_rejected`                       | Extra key at top level                                                                                                                                    | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_max_values_invalid_rejected` (parametrized)             | Non-numeric key; invalid VCP code; negative value                                                                                                         | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_value_redirects_invalid_rejected` (parametrized)        | Invalid feature name; non-numeric inner key; negative inner value                                                                                         | `ValidationError`                                                                                                                                                                                                                                                                                |
| `test_empty_optional_tables_valid`                            | All three optional-content tables empty                                                                                                                   | No error raised; `max_values == {}`, `value_redirects == {}`, all `wait_*_time` fields are `None`                                                                                                                                                                                                |

**Standalone tests:**

| Test                                    | Purpose                                                                                                                                                        |
|-----------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `test_profile_from_raw_transformations` | `max_values` str keys → int; `value_redirects` inner str keys → int; `wait_*` raw fields → `wait_*_time` runtime fields                                        |
| `test_profile_is_frozen`                | Mutating a top-level `MonitorProfile` field raises `ValidationError`; mutating a field on the nested `MonitorIdentity` sub-model also raises `ValidationError` |
| `test_get_profile_missing_file`         | Non-existent path raises `MonitorBossError`                                                                                                                    |
| `test_get_profile_invalid_toml`         | Malformed TOML content raises `MonitorBossError`                                                                                                               |
| `test_get_profile_invalid_profile`      | Valid TOML that fails Pydantic validation raises `MonitorBossError`                                                                                            |
