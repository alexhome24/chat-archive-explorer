"""Application configuration loading and validation."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from chat_archive_explorer.errors import ConfigurationError

APP_DIR_NAME = "ChatArchiveExplorer"
ENV_DATA_DIR = "CHAT_ARCHIVE_EXPLORER_DATA_DIR"
ENV_LOG_LEVEL = "CHAT_ARCHIVE_EXPLORER_LOG_LEVEL"
ENV_LOG_FORMAT = "CHAT_ARCHIVE_EXPLORER_LOG_FORMAT"
_ALLOWED_LOG_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_ALLOWED_LOG_FORMATS = frozenset({"human", "json"})


def default_data_dir(*, platform: str | None = None, home: Path | None = None) -> Path:
    """Return a platform-appropriate application data directory without creating it."""

    active_platform = platform or sys.platform
    active_home = home or Path.home()
    if active_platform == "darwin":
        return active_home / "Library" / "Application Support" / APP_DIR_NAME
    if active_platform.startswith("win"):
        appdata = os.environ.get("LOCALAPPDATA")
        if appdata:
            return Path(appdata) / APP_DIR_NAME
        return active_home / "AppData" / "Local" / APP_DIR_NAME
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    if xdg_data_home:
        return Path(xdg_data_home) / "chat-archive-explorer"
    return active_home / ".local" / "share" / "chat-archive-explorer"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Validated runtime configuration."""

    data_dir: Path
    log_level: str = "INFO"
    log_format: str = "human"

    @property
    def logs_dir(self) -> Path:
        """Directory reserved for application logs."""

        return self.data_dir / "logs"

    @property
    def temp_dir(self) -> Path:
        """Directory reserved for application-owned temporary files."""

        return self.data_dir / "tmp"

    @property
    def config_dir(self) -> Path:
        """Directory reserved for future persisted settings."""

        return self.data_dir / "config"

    @classmethod
    def from_environment(cls, environ: Mapping[str, str] | None = None) -> AppConfig:
        """Load and validate configuration from environment variables."""

        source = os.environ if environ is None else environ
        raw_data_dir = source.get(ENV_DATA_DIR)
        data_dir = Path(raw_data_dir).expanduser() if raw_data_dir else default_data_dir()
        log_level = source.get(ENV_LOG_LEVEL, "INFO").upper()
        log_format = source.get(ENV_LOG_FORMAT, "human").lower()

        if not str(data_dir).strip():
            raise ConfigurationError(f"{ENV_DATA_DIR} must not be empty")
        if log_level not in _ALLOWED_LOG_LEVELS:
            allowed = ", ".join(sorted(_ALLOWED_LOG_LEVELS))
            raise ConfigurationError(f"{ENV_LOG_LEVEL} must be one of: {allowed}")
        if log_format not in _ALLOWED_LOG_FORMATS:
            allowed = ", ".join(sorted(_ALLOWED_LOG_FORMATS))
            raise ConfigurationError(f"{ENV_LOG_FORMAT} must be one of: {allowed}")

        return cls(data_dir=data_dir, log_level=log_level, log_format=log_format)
