from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from core.config.path import _BUNDLE_DIR, _DEFAULT_CONFIG_PATH

logger = logging.getLogger("whisperwriter.utils")

def _load_config_schema(schema_path: Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = _BUNDLE_DIR / "config_schema.yaml"
    with Path(schema_path).open("r", encoding="utf-8") as fh:
        schema: dict[str, Any] = yaml.safe_load(fh)
    return schema

def deep_update(source: dict[str, Any], overrides: dict[str, Any]) -> None:
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(source.get(key), dict):
            deep_update(source[key], value)
        else:
            source[key] = value

def extract_defaults(schema: dict[str, Any]) -> dict[str, Any]:
    def extract_value(item: Any) -> Any:
        if isinstance(item, dict):
            return item["value"] if "value" in item else {k: extract_value(v) for k, v in item.items()}
        return item
    return {category: extract_value(settings) for category, settings in schema.items()}

def load_user_config(config_path: Path | None = None) -> dict[str, Any]:
    if config_path is None:
        config_path = _DEFAULT_CONFIG_PATH
    config_path = Path(config_path)
    if not config_path.is_file():
        return {}
    try:
        with config_path.open("r", encoding="utf-8") as fh:
            user_config: dict[str, Any] = yaml.safe_load(fh) or {}
        return user_config
    except yaml.YAMLError:
        logger.exception("Error parsing configuration file %s; using defaults.", config_path)
        return {}

__all__ = ["_load_config_schema", "deep_update", "extract_defaults", "load_user_config"]
