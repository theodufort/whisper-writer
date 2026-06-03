from __future__ import annotations

import logging
import logging.config

from core.config.path import _LOGGING_CONF

if _LOGGING_CONF.exists():
    logging.config.fileConfig(_LOGGING_CONF, disable_existing_loggers=False)

# Initialize logger
logger = logging.getLogger("whisperwriter.utils")

__all__ = ["logger"]
