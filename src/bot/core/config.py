"""
src/bot/core/config.py
----------------------
Kairo Configuration System

Loads and validates all configuration from environment variables (typically
provided through a .env file). Every configurable value in Kairo flows
through this module — no other file should read os.environ directly.

Design decisions:
    - Configuration is loaded once at startup and stored as an immutable
      object. This prevents inconsistent runtime state from re-reading env
      variables mid-execution.
    - Required variables raise ConfigError immediately so startup fails fast
      with a clear message rather than failing later with a cryptic KeyError.
    - Optional variables declare explicit defaults here so the expected shape
      of configuration is always visible in one place.

Usage:
    from src.bot.core.config import Config

    config = Config()          # loads from environment
    token  = config.bot_token  # access a value

Adding a new configuration variable:
    1. Add the variable name to .env.example with a comment.
    2. Add a property in Config that reads the value via _require() or _get().
    3. Update docs/configuration.md with the variable's description.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import dotenv_values

# Project root — the directory that holds .env.example. Config() loads the
# .env file from here no matter which folder the process was started in, so
# running the bot, API, or dashboard never silently reads the wrong file.
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class ConfigError(Exception):
    """Raised when a required configuration value is missing or invalid."""


@dataclass
class Config:
    """
    Central configuration container for Kairo.

    Loads values from the process environment (and a .env file) during
    __post_init__. All other parts of Kairo should receive a Config instance
    via dependency injection rather than constructing one themselves.

    Args:
        env_file: Optional path to a .env file. When omitted, the file
            <project root>/.env (next to .env.example) is used if it exists;
            otherwise Kairo falls back to the process environment only.
            Real environment variables always take priority over .env values.

    Attributes:
        bot_token        (str)           Discord bot token. Required.
        client_id        (str)           Discord application client ID. Required.
        client_secret    (str)           Discord OAuth2 client secret. Required.
        guild_id         (int | None)    Development guild for instant slash-command sync.
        prefix           (str)           Legacy text command prefix. Defaults to "!".
        db_path          (str)           Path to the SQLite database file.
        log_level        (str)           Logging level (DEBUG/INFO/WARNING/ERROR).
        api_host         (str)           Host the API server binds to.
        api_port         (int)           Port the API server listens on.
        dashboard_url    (str)           Public URL of the web dashboard (for OAuth2 redirect).
        oauth_redirect   (str)           Full OAuth2 redirect URI registered on Discord.
        debug            (bool)          Enables debug mode (verbose logging, hot-reload, etc.).
    """

    env_file: Optional[str] = None

    # Internal raw env storage — populated in __post_init__
    _env: dict = field(default_factory=dict, init=False, repr=False)
    _dotenv_path: Optional[str] = field(default=None, init=False, repr=False)

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def __post_init__(self) -> None:
        """Load the .env file and validate required variables."""
        dotenv_path = self._resolve_env_file()
        self._dotenv_path = dotenv_path

        # Merge .env values with the process environment WITHOUT mutating
        # os.environ: file values fill gaps, real environment variables take
        # priority. This keeps Config instances isolated and prevents one
        # loaded .env from leaking into unrelated code.
        env: dict = {}
        if dotenv_path is not None:
            env.update(dotenv_values(dotenv_path=dotenv_path))
        env.update(os.environ)
        self._env = env
        self._validate()

    def _resolve_env_file(self) -> Optional[str]:
        """
        Decide which .env file to load, anchored to the project root.

        Resolution order:
          1. An explicit env_file argument. Relative paths are resolved
             against the project root (the directory that contains
             .env.example) so behaviour does not depend on the working
             directory.
          2. <project root>/.env — the directory that contains .env.example.
          3. Nothing (process environment only).
        """
        if self.env_file is not None:
            path = Path(self.env_file).expanduser()
            if not path.is_absolute():
                path = PROJECT_ROOT / path
            resolved = path.resolve()
            # Only report a file as loaded when it actually exists;
            # otherwise the startup banner would claim a path that was
            # never read.
            return os.fspath(resolved) if resolved.is_file() else None
        root_env = PROJECT_ROOT / ".env"
        if root_env.is_file():
            return os.fspath(root_env)
        return None

    def _validate(self) -> None:
        """
        Eagerly validate required variables so the bot fails at startup
        rather than mid-execution when a value is first accessed.
        """
        required = ["BOT_TOKEN", "CLIENT_ID", "CLIENT_SECRET"]
        missing = [k for k in required if not self._env.get(k)]
        if missing:
            raise ConfigError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                "Copy .env.example to .env and fill in the missing values."
            )

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @property
    def env_file_used(self) -> Optional[str]:
        """
        Absolute path of the .env file that was loaded, or None when Kairo
        is running purely from the process environment.
        """
        return self._dotenv_path

    def _require(self, key: str) -> str:
        """Return the value of a required environment variable."""
        value = self._env.get(key)
        if not value:
            raise ConfigError(f"Required environment variable '{key}' is not set.")
        return value

    def _get(self, key: str, default: str = "") -> str:
        """Return the value of an optional environment variable."""
        return self._env.get(key, default)

    def _get_int(self, key: str, default: int) -> int:
        """Return an optional environment variable as an integer."""
        raw = self._env.get(key)
        if raw is None:
            return default
        try:
            return int(raw)
        except ValueError as exc:
            raise ConfigError(
                f"Environment variable '{key}' must be an integer, got: {raw!r}"
            ) from exc

    def _get_bool(self, key: str, default: bool = False) -> bool:
        """Return an optional environment variable as a boolean."""
        raw = self._env.get(key, "").lower()
        if raw in ("1", "true", "yes", "on"):
            return True
        if raw in ("0", "false", "no", "off", ""):
            return default
        raise ConfigError(
            f"Environment variable '{key}' must be a boolean value, got: {raw!r}"
        )

    # ------------------------------------------------------------------ #
    # Discord                                                              #
    # ------------------------------------------------------------------ #

    @property
    def bot_token(self) -> str:
        """Discord bot token. Keep this secret — never log or expose it."""
        return self._require("BOT_TOKEN")

    @property
    def client_id(self) -> str:
        """Discord application client ID (from the Developer Portal)."""
        return self._require("CLIENT_ID")

    @property
    def client_secret(self) -> str:
        """Discord OAuth2 client secret (from the Developer Portal)."""
        return self._require("CLIENT_SECRET")

    @property
    def guild_id(self) -> Optional[int]:
        """
        Development guild ID for instant slash-command synchronisation.

        When set, slash commands are synced to this guild only (instant).
        Leave unset (or empty) in production to sync globally (takes up to 1h).
        """
        raw = self._get("DEV_GUILD_ID")
        return int(raw) if raw else None

    @property
    def prefix(self) -> str:
        """Legacy text command prefix. Defaults to '!'."""
        return self._get("BOT_PREFIX", "!")

    # ------------------------------------------------------------------ #
    # Database                                                             #
    # ------------------------------------------------------------------ #

    @property
    def db_path(self) -> str:
        """
        Path to the SQLite database file.

        Defaults to '<project root>/data/kairo.db'. Relative values are
        resolved against the project root (like the .env file), so the
        database lands in the same place no matter which directory the
        process is started from. Absolute paths (e.g. /var/lib/kairo.db)
        are used as-is. The parent directory is created automatically.
        """
        raw = self._get("DB_PATH", "data/kairo.db")
        if os.path.isabs(raw):
            return raw
        return os.fspath((PROJECT_ROOT / raw).resolve())

    # ------------------------------------------------------------------ #
    # Logging                                                              #
    # ------------------------------------------------------------------ #

    _VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

    @property
    def log_level(self) -> str:
        """
        Logging verbosity level.

        Accepted values (case-insensitive): DEBUG, INFO, WARNING, ERROR, CRITICAL.
        Defaults to INFO. Invalid values fail fast at startup.
        """
        level = self._get("LOG_LEVEL", "INFO").upper()
        if level not in self._VALID_LOG_LEVELS:
            raise ConfigError(
                f"Invalid LOG_LEVEL: {level!r}. "
                f"Expected one of: {', '.join(sorted(self._VALID_LOG_LEVELS))}."
            )
        return level

    # ------------------------------------------------------------------ #
    # API                                                                  #
    # ------------------------------------------------------------------ #

    @property
    def api_host(self) -> str:
        """Host the REST API server binds to. Defaults to '127.0.0.1'."""
        return self._get("API_HOST", "127.0.0.1")

    @property
    def api_port(self) -> int:
        """Port the REST API server listens on. Defaults to 8080."""
        return self._get_int("API_PORT", 8080)

    @property
    def api_secret(self) -> str:
        """
        Shared secret used to authenticate requests with the X-API-Key header.

        Only required for API-key-protected endpoints (everything under
        /api/ except /api/v1/me). The dashboard login flow (/auth/*) does not
        use this secret — it authenticates with CLIENT_ID/CLIENT_SECRET
        server-side and a kairo_session cookie.
        """
        return self._get("API_SECRET", "")

    # ------------------------------------------------------------------ #
    # Dashboard / OAuth2                                                   #
    # ------------------------------------------------------------------ #

    @property
    def dashboard_url(self) -> str:
        """
        Public base URL of the web dashboard.

        Example: https://kairo.example.com
        Used to construct the OAuth2 redirect URI when OAUTH_REDIRECT is not
        explicitly provided.
        """
        return self._get("DASHBOARD_URL", "http://localhost:5173")

    @property
    def oauth_redirect(self) -> str:
        """
        Full OAuth2 redirect URI registered in the Discord Developer Portal.

        Defaults to <dashboard_url>/auth/callback.
        """
        explicit = self._get("OAUTH_REDIRECT")
        return explicit if explicit else f"{self.dashboard_url}/auth/callback"

    # ------------------------------------------------------------------ #
    # Runtime                                                              #
    # ------------------------------------------------------------------ #

    @property
    def debug(self) -> bool:
        """
        Enables debug mode.

        In debug mode:
          - Logging verbosity is forced to DEBUG.
          - discord.py logs are more verbose.
          - Slash commands are synced to the dev guild on startup.
        """
        return self._get_bool("DEBUG", False)
