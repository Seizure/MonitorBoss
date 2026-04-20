import pytest
from pydantic import BaseModel, ValidationError
from tomlkit import document, table

from monitorboss import MonitorBossError
from monitorboss.util import validate_non_negative_wait, read_toml_file, write_toml_file, toml_load_errors

VALID_TOML = "[section]\nkey = \"value\""


class TestValidateNonNegativeWait:
    """Tests for validate_non_negative_wait."""

    @pytest.mark.parametrize("v", [0.0, 0.05, 1.0, 100.0])
    def test_non_negative_value_passes_through(self, v: float):
        """Non-negative floats must be returned unchanged."""
        assert validate_non_negative_wait(v) == v

    def test_none_passes_through(self):
        """None must be returned unchanged (profile settings use Optional[float])."""
        assert validate_non_negative_wait(None) is None

    @pytest.mark.parametrize("v", [-0.001, -1.0, -100.0])
    def test_negative_value_raises(self, v: float):
        """Negative values must raise ValueError with a descriptive message."""
        with pytest.raises(ValueError, match="Wait times must be non-negative"):
            validate_non_negative_wait(v)


class TestReadTomlFile:
    """Tests for read_toml_file."""

    def test_valid_file_returns_document(self, tmp_path):
        """A valid TOML file must be read and parsed into a TOMLDocument."""
        f = tmp_path / "test.toml"
        f.write_text(VALID_TOML)
        doc = read_toml_file(f.as_posix(), "test")
        assert doc["section"]["key"] == "value"

    def test_missing_file_no_on_missing_raises(self, tmp_path):
        """A missing file with no on_missing must raise MonitorBossError."""
        with pytest.raises(MonitorBossError, match="could not read"):
            read_toml_file((tmp_path / "nonexistent.toml").as_posix(), "test")

    def test_missing_file_on_missing_creates_and_reads(self, tmp_path):
        """When on_missing is provided and file is absent, the content must be written then read."""
        f = tmp_path / "auto.toml"
        assert not f.exists()
        doc = read_toml_file(f.as_posix(), "test", on_missing=VALID_TOML)
        assert f.exists()
        assert doc["section"]["key"] == "value"

    def test_missing_file_on_missing_creates_parent_dirs(self, tmp_path):
        """When on_missing is provided, missing parent directories must be created."""
        f = tmp_path / "subdir" / "nested" / "auto.toml"
        assert not f.parent.exists()
        read_toml_file(f.as_posix(), "test", on_missing=VALID_TOML)
        assert f.exists()

    def test_existing_file_on_missing_not_overwritten(self, tmp_path):
        """When on_missing is provided but the file already exists, it must not be overwritten."""
        f = tmp_path / "existing.toml"
        f.write_text(VALID_TOML)
        original_mtime = f.stat().st_mtime
        read_toml_file(f.as_posix(), "test", on_missing="[other]\nkey = \"different\"")
        assert f.stat().st_mtime == original_mtime
        assert f.read_text() == VALID_TOML

    def test_invalid_toml_raises(self, tmp_path):
        """A file with invalid TOML content must raise MonitorBossError."""
        f = tmp_path / "bad.toml"
        f.write_text("[[[ not valid toml")
        with pytest.raises(MonitorBossError, match="could not parse"):
            read_toml_file(f.as_posix(), "test")

    def test_extra_parse_hint_included_in_error(self, tmp_path):
        """The extra_parse_hint must be appended to the parse-failure error message."""
        f = tmp_path / "bad.toml"
        f.write_text("[[[ not valid toml")
        with pytest.raises(MonitorBossError, match="my recovery hint"):
            read_toml_file(f.as_posix(), "test", extra_parse_hint="my recovery hint")

    def test_label_used_in_read_error_message(self, tmp_path):
        """The label must appear in the read-failure error message."""
        with pytest.raises(MonitorBossError, match="mytype"):
            read_toml_file((tmp_path / "nonexistent.toml").as_posix(), "mytype")

    def test_label_used_in_parse_error_message(self, tmp_path):
        """The label must appear in the parse-failure error message."""
        f = tmp_path / "bad.toml"
        f.write_text("[[[ not valid toml")
        with pytest.raises(MonitorBossError, match="mytype"):
            read_toml_file(f.as_posix(), "mytype")


class TestWriteTomlFile:
    """Tests for write_toml_file."""

    def _make_doc(self) -> object:
        doc = document()
        t = table()
        t.add("key", "value")
        doc.add("section", t)
        return doc

    def test_writes_file_content(self, tmp_path):
        """The TOMLDocument must be serialised and written to the specified path."""
        f = tmp_path / "out.toml"
        write_toml_file(f.as_posix(), "test", self._make_doc())
        assert f.exists()
        assert 'key = "value"' in f.read_text()

    def test_creates_parent_dirs(self, tmp_path):
        """Missing parent directories must be created before writing."""
        f = tmp_path / "subdir" / "nested" / "out.toml"
        assert not f.parent.exists()
        write_toml_file(f.as_posix(), "test", self._make_doc())
        assert f.exists()

    def test_overwrites_existing_file(self, tmp_path):
        """An existing file at the path must be overwritten."""
        f = tmp_path / "out.toml"
        f.write_text("old content")
        write_toml_file(f.as_posix(), "test", self._make_doc())
        assert 'key = "value"' in f.read_text()

    def test_label_used_in_error_message(self, tmp_path):
        """The label must appear in the MonitorBossError message on write failure."""
        # Write to a path where the parent is a file (not a dir), forcing an OS error
        blocker = tmp_path / "blocker"
        blocker.write_text("I am a file")
        bad_path = blocker / "out.toml"
        with pytest.raises(MonitorBossError, match="mytype"):
            write_toml_file(bad_path.as_posix(), "mytype", self._make_doc())


class TestTomlLoadErrors:
    """Tests for the toml_load_errors context manager."""

    def test_no_exception_passes_through(self):
        """No exception inside the block must result in normal execution."""
        result = []
        with toml_load_errors("/fake/path", "test"):
            result.append("ok")
        assert result == ["ok"]

    def test_validation_error_becomes_monitor_boss_error(self):
        """A ValidationError raised inside the block must be wrapped in MonitorBossError."""
        class _Model(BaseModel):
            x: int

        with pytest.raises(MonitorBossError, match="Invalid test"):
            with toml_load_errors("/fake/path", "test"):
                _Model(x="not_an_int")

    def test_monitor_boss_error_reraised_unchanged(self):
        """A MonitorBossError raised inside the block must be re-raised as-is."""
        original = MonitorBossError("original message")
        with pytest.raises(MonitorBossError, match="original message") as exc_info:
            with toml_load_errors("/fake/path", "test"):
                raise original
        assert exc_info.value is original

    def test_other_exception_becomes_monitor_boss_error(self):
        """Any other exception raised inside the block must be wrapped in MonitorBossError."""
        with pytest.raises(MonitorBossError, match="Could not load test"):
            with toml_load_errors("/fake/path", "test"):
                raise RuntimeError("something unexpected")

    def test_label_used_in_validation_error_message(self):
        """The label must appear in the ValidationError-derived MonitorBossError message."""
        class _Model(BaseModel):
            x: int

        with pytest.raises(MonitorBossError, match="mylabel"):
            with toml_load_errors("/fake/path", "mylabel"):
                _Model(x="bad")

    def test_label_used_in_other_error_message(self):
        """The label must appear in the generic-exception-derived MonitorBossError message."""
        with pytest.raises(MonitorBossError, match="mylabel"):
            with toml_load_errors("/fake/path", "mylabel"):
                raise ValueError("boom")

