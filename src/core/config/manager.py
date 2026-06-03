from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from core.config.loader import _load_config_schema, deep_update, extract_defaults, load_user_config

logger = logging.getLogger("whisperwriter.utils")

class ConfigManager:
    _instance: ConfigManager | None = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        self.config: dict[str, Any] = {}
        self.schema: dict[str, Any] = {}

    @classmethod
    def initialize(cls, schema_path: Path | None = None) -> None:
        with cls._lock:
            if cls._instance is None:
                instance = cls()
                instance.schema = _load_config_schema(schema_path)
                instance.config = extract_defaults(instance.schema)
                user_config = load_user_config()
                deep_update(instance.config, user_config)
                cls._instance = instance

    @classmethod
    def _get_instance(cls) -> ConfigManager:
        if cls._instance is None:
            raise RuntimeError("ConfigManager not initialized. Call ConfigManager.initialize() first.")
        return cls._instance

    @classmethod
    def get_schema(cls) -> dict[str, Any]:
        return cls._get_instance().schema

    @classmethod
    def get_config_section(cls, *keys: str) -> dict[str, Any]:
        section: Any = cls._get_instance().config
        for key in keys:
            if isinstance(section, dict) and key in section:
                section = section[key]
            else:
                return {}
        return section if isinstance(section, dict) else {}

    @classmethod
    def get_config_value(cls, *keys: str) -> Any:
        value: Any = cls._get_instance().config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    @classmethod
    def set_config_value(cls, value: Any, *keys: str) -> None:
        config = cls._get_instance().config
        for key in keys[:-1]:
            config = config.setdefault(key, {})
            if not isinstance(config, dict):
                config = {}
        config[keys[-1]] = value

    @classmethod
    def config_file_exists(cls) -> bool:
        from core.config.path import _DEFAULT_CONFIG_PATH
        return _DEFAULT_CONFIG_PATH.is_file()

    @classmethod
    def save_config(cls, config_path: Path | None = None) -> None:
        from core.config.path import _DEFAULT_CONFIG_PATH
        if config_path is None:
            config_path = _DEFAULT_CONFIG_PATH
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as fh:
            import yaml
            yaml.dump(cls._get_instance().config, fh, default_flow_style=False)
        logger.info("Configuration saved to %s", config_path)

    @classmethod
    def reload_config(cls) -> None:
        instance = cls._get_instance()
        instance.config = extract_defaults(instance.schema)
        user_config = load_user_config()
        deep_update(instance.config, user_config)

    @classmethod
    def console_print(cls, message: str) -> None:
        logger.info(message)

    @classmethod
    def get_config_path(cls) -> Path:
        from core.config.path import _DEFAULT_CONFIG_PATH
        return _DEFAULT_CONFIG_PATH

__all__ = ["ConfigManager"]
