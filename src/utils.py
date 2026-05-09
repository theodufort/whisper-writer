from __future__ import annotations

import logging
import logging.config
import sys
import threading
from pathlib import Path
from typing import Any

import yaml

_SRC_DIR = Path(__file__).parent

# When frozen by PyInstaller, __file__ resolves inside sys._MEIPASS at the
# root level (no src/ prefix), so bundled data files live at sys._MEIPASS too.
# User-writable files (config.yaml) must live next to the exe so they persist.
if hasattr(sys, "_MEIPASS"):
    _BUNDLE_DIR = Path(sys._MEIPASS)  # read-only bundled resources
    _DATA_DIR = Path(sys.executable).parent  # writable directory beside exe
else:
    _BUNDLE_DIR = _SRC_DIR  # project's src/ in dev mode
    _DATA_DIR = _SRC_DIR

_LOGGING_CONF = _BUNDLE_DIR / "logging.conf"
_DEFAULT_CONFIG_PATH = _DATA_DIR / "config.yaml"

if _LOGGING_CONF.exists():
    logging.config.fileConfig(_LOGGING_CONF, disable_existing_loggers=False)

logger = logging.getLogger("whisperwriter.utils")


def resource_path(relative_path: str) -> str:
    """Return an absolute path to a bundled resource.

    Works both when running from source and when frozen by PyInstaller.
    Assets should be addressed relative to the project root, e.g.
    ``resource_path('assets/beep.wav')``.
    """
    if hasattr(sys, "_MEIPASS"):
        return str(Path(sys._MEIPASS) / relative_path)
    # In development the project root is one level above src/
    return str(_SRC_DIR.parent / relative_path)


class ConfigManager:
    _instance: ConfigManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the ConfigManager instance."""
        self.config: dict[str, Any] = {}
        self.schema: dict[str, Any] = {}

    @classmethod
    def initialize(cls, schema_path: Path | None = None) -> None:
        """Initialize the ConfigManager with the given schema path."""
        with cls._lock:
            if cls._instance is None:
                instance = cls()
                instance.schema = instance._load_config_schema(schema_path)
                instance.config = instance._load_default_config()
                instance._load_user_config()
                cls._instance = instance

    @classmethod
    def _get_instance(cls) -> ConfigManager:
        if cls._instance is None:
            raise RuntimeError(
                "ConfigManager not initialized. Call ConfigManager.initialize() first."
            )
        return cls._instance

    @classmethod
    def get_schema(cls) -> dict[str, Any]:
        """Get the configuration schema."""
        return cls._get_instance().schema

    @classmethod
    def get_config_section(cls, *keys: str) -> dict[str, Any]:
        """Get a specific section of the configuration."""
        section: Any = cls._get_instance().config
        for key in keys:
            if isinstance(section, dict) and key in section:
                section = section[key]
            else:
                return {}
        return section if isinstance(section, dict) else {}

    @classmethod
    def get_config_value(cls, *keys: str) -> Any:
        """Get a specific configuration value using nested keys."""
        value: Any = cls._get_instance().config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    @classmethod
    def set_config_value(cls, value: Any, *keys: str) -> None:
        """Set a specific configuration value using nested keys."""
        config = cls._get_instance().config
        for key in keys[:-1]:
            config = config.setdefault(key, {})
            if not isinstance(config, dict):
                config = {}
        config[keys[-1]] = value

    @classmethod
    def config_file_exists(cls) -> bool:
        """Return True if the user config file exists on disk."""
        return _DEFAULT_CONFIG_PATH.is_file()

    @classmethod
    def save_config(cls, config_path: Path = _DEFAULT_CONFIG_PATH) -> None:
        """Save the current configuration to a YAML file."""
        instance = cls._get_instance()
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as fh:
            yaml.dump(instance.config, fh, default_flow_style=False)
        logger.info("Configuration saved to %s", config_path)

    @classmethod
    def reload_config(cls) -> None:
        """Reload the configuration from the file."""
        instance = cls._get_instance()
        instance.config = instance._load_default_config()
        instance._load_user_config()

    @classmethod
    def console_print(cls, message: str) -> None:
        """Log an informational message (backwards-compat shim)."""
        logger.info(message)

    # ------------------------------------------------------------------
    # Instance helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_config_schema(schema_path: Path | None = None) -> dict[str, Any]:
        """Load the configuration schema from a YAML file."""
        if schema_path is None:
            schema_path = _BUNDLE_DIR / "config_schema.yaml"
        with Path(schema_path).open("r", encoding="utf-8") as fh:
            schema: dict[str, Any] = yaml.safe_load(fh)
        return schema

    def _load_default_config(self) -> dict[str, Any]:
        """Build default configuration values from the schema."""

        def extract_value(item: Any) -> Any:
            if isinstance(item, dict):
                return (
                    item["value"]
                    if "value" in item
                    else {k: extract_value(v) for k, v in item.items()}
                )
            return item

        return {category: extract_value(settings) for category, settings in self.schema.items()}

    def _load_user_config(self, config_path: Path = _DEFAULT_CONFIG_PATH) -> None:
        """Load user configuration and deep-merge into the default config."""

        def deep_update(source: dict[str, Any], overrides: dict[str, Any]) -> None:
            for key, value in overrides.items():
                if isinstance(value, dict) and isinstance(source.get(key), dict):
                    deep_update(source[key], value)
                else:
                    source[key] = value

        config_path = Path(config_path)
        if not config_path.is_file():
            return
        try:
            with config_path.open("r", encoding="utf-8") as fh:
                user_config: dict[str, Any] = yaml.safe_load(fh) or {}
            deep_update(self.config, user_config)
            logger.debug("User config loaded from %s", config_path)
        except yaml.YAMLError:
            logger.exception("Error parsing configuration file %s; using defaults.", config_path)
