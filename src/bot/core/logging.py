"""
src/bot/core/logging.py
-----------------------
Kairo Logging System

Provides a consistent, structured logging setup across the entire Kairo
project. All modules obtain their logger through get_logger() rather than
calling logging.getLogger() directly — this ensures uniform formatting,
level filtering, and future handler changes (e.g. file rotation, structured
JSON output) can be applied from one place.

Design decisions:
    - A single call to setup_logging() configures the root Kairo logger.
      It should be called once, at the very start of src/run.py.
    - discord.py's own logger is also configured here so its verbosity can
      be controlled without touching library internals.
    - Log records include timestamp, level, logger name, and message. In
      debug mode, the source file and line number are added.

Usage:
    # In run.py or bot.py (once):
    from src.bot.core.logging import setup_logging
    setup_logging(level="INFO", debug=False)

    # In any other module:
    from src.bot.core.logging import get_logger
    log = get_logger(__name__)
    log.info("Cog loaded: %s", cog_name)

Log levels:
    DEBUG    — Granular diagnostic information (verbose).
    INFO     — Normal operational events (startup, cog loads, commands).
    WARNING  — Unexpected but recoverable situations.
    ERROR    — Errors that prevent a specific operation from completing.
    CRITICAL — Errors that prevent the bot from running at all.
"""

import logging
import sys
from typing import Optional


# ------------------------------------------------------------------ #
# Formatting                                                          #
# ------------------------------------------------------------------ #

_STANDARD_FORMAT = "[%(asctime)s] [%(levelname)-8s] %(name)s: %(message)s"
_DEBUG_FORMAT = "[%(asctime)s] [%(levelname)-8s] %(name)s (%(filename)s:%(lineno)d): %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Level name → ANSI colour codes for terminal output
_LEVEL_COLOURS = {
    "DEBUG":    "\033[36m",    # Cyan
    "INFO":     "\033[32m",    # Green
    "WARNING":  "\033[33m",    # Yellow
    "ERROR":    "\033[31m",    # Red
    "CRITICAL": "\033[35m",    # Magenta
}
_RESET = "\033[0m"


class _ColouredFormatter(logging.Formatter):
    """
    A log formatter that adds ANSI colour codes to the level name when
    writing to a terminal. Falls back to plain text when stdout is not
    a TTY (e.g. when piped to a file or a process manager).
    """

    def __init__(self, fmt: str, datefmt: str, use_colour: bool) -> None:
        super().__init__(fmt, datefmt=datefmt)
        self._use_colour = use_colour

    def format(self, record: logging.LogRecord) -> str:
        if self._use_colour and record.levelname in _LEVEL_COLOURS:
            colour = _LEVEL_COLOURS[record.levelname]
            record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


# ------------------------------------------------------------------ #
# Public API                                                          #
# ------------------------------------------------------------------ #

def setup_logging(
    level: str = "INFO",
    debug: bool = False,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure the Kairo logging hierarchy.

    This must be called once before any loggers are used. Calling it more
    than once is safe — duplicate handlers are not added.

    Args:
        level:    Minimum log level for the Kairo logger (e.g. "INFO").
                  Overridden to "DEBUG" when debug=True.
        debug:    When True, forces DEBUG level and includes source location
                  in each log record.
        log_file: Optional path to write log output to in addition to stdout.
                  The file is opened in append mode with UTF-8 encoding.
    """
    effective_level = logging.DEBUG if debug else getattr(logging, level.upper(), logging.INFO)
    fmt = _DEBUG_FORMAT if debug else _STANDARD_FORMAT

    # --- stdout handler ----------------------------------------------- #
    use_colour = sys.stdout.isatty()
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(_ColouredFormatter(fmt, _DATE_FORMAT, use_colour))
    stream_handler.setLevel(effective_level)

    handlers: list[logging.Handler] = [stream_handler]

    # --- optional file handler ---------------------------------------- #
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(fmt, datefmt=_DATE_FORMAT))
        file_handler.setLevel(effective_level)
        handlers.append(file_handler)

    # --- configure the root kairo logger ------------------------------ #
    kairo_logger = logging.getLogger("kairo")
    if kairo_logger.handlers:
        return  # already configured; avoid duplicate handlers on re-import
    kairo_logger.setLevel(effective_level)
    for handler in handlers:
        kairo_logger.addHandler(handler)

    # Prevent log records from propagating to the root Python logger,
    # which may have its own (unformatted) StreamHandler.
    kairo_logger.propagate = False

    # --- discord.py logger -------------------------------------------- #
    # discord.py is chatty at DEBUG. In non-debug mode we cap it at WARNING
    # so routine gateway messages don't flood the console.
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.DEBUG if debug else logging.WARNING)
    for handler in handlers:
        discord_logger.addHandler(handler)
    discord_logger.propagate = False

    # --- aiohttp logger (used internally by discord.py) --------------- #
    aiohttp_logger = logging.getLogger("aiohttp")
    aiohttp_logger.setLevel(logging.WARNING)
    aiohttp_logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """
    Return a logger scoped under the 'kairo' namespace.

    Args:
        name: Typically __name__ of the calling module. If the name already
              starts with 'kairo.' it is used as-is; otherwise it is
              prefixed with 'kairo.' to keep the hierarchy consistent.

    Returns:
        A logging.Logger instance.

    Example:
        log = get_logger(__name__)
        log.info("Feature loaded.")
    """
    if name.startswith("kairo."):
        return logging.getLogger(name)
    # Strip the leading 'src.bot.' or 'src.' path component so logger names
    # are readable (e.g. 'kairo.core.config' instead of 'kairo.src.bot.core.config').
    clean = name.removeprefix("src.bot.").removeprefix("src.")
    return logging.getLogger(f"kairo.{clean}")
