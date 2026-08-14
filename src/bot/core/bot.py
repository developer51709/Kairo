"""
src/bot/core/bot.py
-------------------
Kairo Bot — Main Bot Class

Defines KairoBot, the central class that extends discord.ext.commands.Bot
with Kairo-specific infrastructure: configuration, logging, the internal
event bus, and lifecycle management.

KairoBot is the single object that owns the core state shared by all cogs
and features. Dependencies (config, database, event bus) should be accessed
through the bot instance passed to each cog's constructor rather than through
module-level globals.

Lifecycle:
    1. KairoBot is instantiated with a Config object.
    2. KairoBot.start_kairo() is called from src/run.py.
    3. start_kairo() connects to Discord and calls setup_hook() before
       the bot's READY event fires.
    4. setup_hook() initialises the database, loads all feature cogs, and
       optionally syncs slash commands.
    5. When the process receives SIGINT/SIGTERM, close() shuts everything
       down gracefully.

Usage:
    config = Config()
    bot = KairoBot(config=config)
    asyncio.run(bot.start_kairo())
"""

import asyncio
from typing import Optional

import discord
from discord.ext import commands

from .config import Config
from .events import EventBus
from .logging import get_logger, setup_logging

log = get_logger(__name__)


class KairoBot(commands.Bot):
    """
    The main Kairo bot class.

    Extends discord.ext.commands.Bot with:
        - config    — the loaded Config instance
        - bus       — the internal EventBus for cross-feature communication
        - Structured startup / shutdown logging
        - Slash command sync helpers

    Attributes:
        config (Config):    Loaded configuration.
        bus    (EventBus):  Internal pub/sub event bus.
    """

    def __init__(self, config: Config) -> None:
        """
        Initialise KairoBot.

        Args:
            config: A loaded and validated Config instance.
        """
        self.config: Config = config
        self.bus: EventBus = EventBus()

        # Configure logging before anything else so all subsequent messages
        # are captured.
        setup_logging(level=config.log_level, debug=config.debug)

        intents = self._build_intents()

        super().__init__(
            command_prefix=config.prefix,
            intents=intents,
            # Disable the default help command — we provide a Components V2 one.
            help_command=None,
            # Allow the bot to see its own messages (needed for some utilities).
            case_insensitive=True,
        )

        log.info("KairoBot initialised.")

    # ------------------------------------------------------------------ #
    # Intents                                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _build_intents() -> discord.Intents:
        """
        Build the Discord gateway intents required by Kairo.

        Intents control which events Discord sends to the bot. Only the
        intents actually needed by Kairo's features are requested. Requesting
        unnecessary privileged intents (members, presences, message_content)
        requires approval from Discord for large bots, so this is kept
        minimal and documented.

        Returns:
            discord.Intents configured for Kairo.

        Privileged intents in use:
            members         — Required for welcome/leave messages, auto-roles,
                              and member moderation lookups.
            message_content — Required for prefix commands and AutoMod content
                              scanning.
        """
        intents = discord.Intents.default()
        intents.members = True           # Privileged — required for member events
        intents.message_content = True   # Privileged — required for prefix commands / automod
        return intents

    # ------------------------------------------------------------------ #
    # Startup                                                              #
    # ------------------------------------------------------------------ #

    async def setup_hook(self) -> None:
        """
        Called by discord.py after login but before READY.

        This is the correct place to:
            - Initialise the database connection.
            - Load feature cogs.
            - Sync application (slash) commands.

        It runs inside the bot's event loop so async operations are safe here.
        """
        log.info("Running setup_hook...")

        await self._load_cogs()
        await self._sync_commands()

        log.info("setup_hook complete.")

    async def _load_cogs(self) -> None:
        """
        Discover and load all feature cogs.

        Currently loads cogs from a hardcoded list. A future version will
        scan the features directory automatically and respect an enable/disable
        configuration per guild.
        """
        # TODO: Replace with auto-discovery once feature cogs are implemented.
        cog_modules: list[str] = [
            "src.bot.features.moderation.cog",
            "src.bot.features.automod.cog",
            "src.bot.features.logging.cog",
            "src.bot.features.utility.cog",
        ]

        for module in cog_modules:
            try:
                await self.load_extension(module)
                log.info("Loaded cog: %s", module)
            except Exception:  # noqa: BLE001
                log.exception("Failed to load cog: %s", module)

    async def _sync_commands(self) -> None:
        """
        Sync slash commands with Discord.

        In debug mode, commands are synced to the development guild only
        (instant). In production, global sync is used (can take up to 1 hour).

        Syncing on every startup is only appropriate during development.
        Production deployments should sync commands explicitly (e.g. as part
        of a deployment script) to avoid hitting rate limits.
        """
        if self.config.debug and self.config.guild_id:
            guild = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            log.info("Synced %d slash command(s) to dev guild %d.", len(synced), self.config.guild_id)
        else:
            synced = await self.tree.sync()
            log.info("Synced %d global slash command(s).", len(synced))

    # ------------------------------------------------------------------ #
    # Discord Events                                                       #
    # ------------------------------------------------------------------ #

    async def on_ready(self) -> None:
        """
        Fired when the bot has connected and is ready to receive events.

        Note: on_ready can fire multiple times during a session if the bot
        reconnects after a network interruption. Code that should only run
        once at startup belongs in setup_hook(), not here.
        """
        assert self.user is not None  # guaranteed once on_ready fires
        log.info(
            "Kairo is ready! Logged in as %s (ID: %d). Serving %d guild(s).",
            self.user,
            self.user.id,
            len(self.guilds),
        )
        await self.bus.emit("bot_ready", bot=self)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        """Fired when Kairo joins a new guild."""
        log.info("Joined guild: %s (ID: %d)", guild.name, guild.id)
        await self.bus.emit("guild_join", guild=guild)

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Fired when Kairo is removed from a guild."""
        log.info("Removed from guild: %s (ID: %d)", guild.name, guild.id)
        await self.bus.emit("guild_remove", guild=guild)

    async def on_error(self, event_method: str, *args: object, **kwargs: object) -> None:
        """Global error handler for uncaught exceptions in event listeners."""
        log.exception("Unhandled exception in event '%s'.", event_method)

    # ------------------------------------------------------------------ #
    # Entrypoint                                                           #
    # ------------------------------------------------------------------ #

    async def start_kairo(self) -> None:
        """
        Connect to Discord and run the bot.

        This wraps discord.py's Bot.start() with a graceful shutdown handler
        so SIGINT (Ctrl-C) and SIGTERM produce clean log output.

        Called from src/run.py:
            asyncio.run(bot.start_kairo())
        """
        log.info("Starting Kairo...")
        try:
            await self.start(self.config.bot_token)
        except KeyboardInterrupt:
            log.info("Received keyboard interrupt. Shutting down...")
        finally:
            if not self.is_closed():
                await self.close()
            log.info("Kairo has shut down.")

    async def close(self) -> None:
        """
        Graceful shutdown. Called automatically when the process is
        interrupted or when start_kairo() exits.
        """
        log.info("Closing Kairo...")
        await self.bus.emit("bot_closing", bot=self)
        await super().close()
        log.info("Discord connection closed.")
