from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

_logger: Optional[logging.Logger] = None


def _get_logger() -> logging.Logger:
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("agent_requests")
    logger.setLevel(logging.INFO)

    # Log to repo root: <repo>/agent.log
    log_path = Path(__file__).resolve().parents[2] / "agent.log"
    handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
    handler.setLevel(logging.INFO)
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.propagate = False

    _logger = logger
    return logger


def log_input(system: str, user: str) -> None:
    logger = _get_logger()
    logger.info("INPUT")
    logger.info("SYSTEM: %s", system)
    logger.info("USER: %s", user)


def log_output(assistant: str) -> None:
    logger = _get_logger()
    logger.info("OUTPUT")
    logger.info("ASSISTANT: %s", assistant)
    logger.info("-"*50)


def log_error(message: str) -> None:
    logger = _get_logger()
    logger.info("OUTPUT")
    logger.info("ASSISTANT: %s", message)
    logger.info("-"*50)
