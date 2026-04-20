"""Shared utility helpers for TOML loading and common validation logic."""

from contextlib import contextmanager
from logging import getLogger
from pathlib import Path
from typing import Generator

from pydantic import ValidationError
from tomlkit import dump, parse, TOMLDocument

from monitorboss import MonitorBossError

_log = getLogger(__name__)


def validate_non_negative_wait(v: float | None) -> float | None:
    """Raise ValueError if v is a negative number. Pass-through for None.

    Intended for use inside Pydantic field validators on wait-time fields.
    """
    if v is not None and v < 0:
        raise ValueError(f"Wait times must be non-negative, got {v}")
    return v


def read_toml_file(
    path: str,
    label: str,
    extra_parse_hint: str = "",
    on_missing: str | None = None,
) -> TOMLDocument:
    """Read and parse a TOML file, wrapping OS and parse errors in MonitorBossError.

    Args:
        path: Absolute or relative path to the TOML file.
        label: Short noun used in error messages (e.g. ``"config"``, ``"profile"``).
        extra_parse_hint: Optional text appended to the parse-failure message
            (e.g. a hint about how to recover from a corrupt file).
        on_missing: Optional string content to write to the file when it does not
            exist. When provided, the parent directory is also created if absent.
            Intended for callers that want to auto-create a default file (e.g. the
            serialised default config TOML). Profile files are never auto-created,
            so callers that do not need this behaviour omit the argument.

    Returns:
        The parsed ``TOMLDocument``.

    Raises:
        MonitorBossError: If the file cannot be read or the content cannot be parsed.
    """
    _log.debug(f"read {label} TOML file from: {Path(path).absolute()}")
    if on_missing is not None:
        if not Path(path).parent.exists():
            Path(path).parent.mkdir(parents=True)
        if not Path(path).exists():
            try:
                with open(path, "w", encoding="utf8") as file:
                    file.write(on_missing)
            except Exception as err:
                raise MonitorBossError(f"could not create {label} file: {Path(path).absolute()}") from err
    try:
        with open(path, "r", encoding="utf8") as file:
            content = file.read()
    except Exception as err:
        raise MonitorBossError(f"could not read {label} file: {Path(path).absolute()}") from err
    try:
        return parse(content)
    except Exception as err:
        raise MonitorBossError(
            f"could not parse {label} file: {path}: {err}{extra_parse_hint}"
        ) from err


def write_toml_file(path: str, label: str, doc: TOMLDocument) -> None:
    """Write a TOMLDocument to a file, wrapping OS errors in MonitorBossError.

    Args:
        path: Absolute or relative path to the destination file.
        label: Short noun used in error messages (e.g. ``"config"``, ``"profile"``).
        doc: The ``TOMLDocument`` to serialize and write.

    Raises:
        MonitorBossError: If the parent directory cannot be created or the file
            cannot be written.
    """
    _log.debug(f"write {label} TOML file to: {Path(path).absolute()}")
    if not Path(path).parent.exists():
        Path(path).parent.mkdir(parents=True)
    try:
        with open(path, "w", encoding="utf8") as file:
            dump(doc, file)
    except Exception as err:
        raise MonitorBossError(f"could not write {label} file: {Path(path).absolute()}") from err


@contextmanager
def toml_load_errors(path: str, label: str) -> Generator[None, None, None]:
    """Context manager that normalises ``ValidationError`` and unexpected exceptions
    into ``MonitorBossError``, re-raising ``MonitorBossError`` unchanged.

    Args:
        path: Path to the TOML file being loaded (used in error messages).
        label: Short noun used in error messages (e.g. ``"config"``, ``"profile"``).

    Example::

        with toml_load_errors(path, "config"):
            raw = _RawTomlConfig.model_validate(doc.unwrap())
            return Config.from_raw(raw)
    """
    try:
        yield
    except ValidationError as err:
        raise MonitorBossError(f"Invalid {label} at {Path(path).absolute()}: {err}") from err
    except MonitorBossError:
        raise
    except Exception as err:
        raise MonitorBossError(f"Could not load {label} from {Path(path).absolute()}: {err}") from err





