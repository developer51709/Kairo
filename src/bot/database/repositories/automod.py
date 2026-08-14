"""
src/bot/database/repositories/automod.py
-----------------------------------------
AutoMod Repository

Provides all database operations for AutoMod configurations and rules.
The AutoMod feature cog should use this repository exclusively.

Usage:
    repo = AutoModRepository(db)

    # Get or create config for a guild
    config = await repo.get_config(guild_id)
    if config is None:
        config = await repo.create_config(guild_id)

    # Update config
    config.spam_enabled = True
    await repo.update_config(config)

    # Get rules for a guild
    rules = await repo.get_rules_for_guild(guild_id)
"""

import json
from datetime import datetime
from typing import List, Optional

from ..connection import Database
from ..models.automod import AutoModConfig, AutoModRule
from ...core.logging import get_logger

log = get_logger(__name__)


class AutoModRepository:
    """
    Data access object for the automod_config and automod_rules tables.

    Attributes:
        _db (Database): The shared database connection.
    """

    def __init__(self, db: Database) -> None:
        self._db = db

    # ------------------------------------------------------------------ #
    # Configuration                                                        #
    # ------------------------------------------------------------------ #

    async def get_config(self, guild_id: int) -> Optional[AutoModConfig]:
        """
        Retrieve the AutoMod configuration for a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            AutoModConfig if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM automod_config WHERE guild_id = ?",
            (guild_id,),
        )
        return AutoModConfig.from_row(row) if row else None

    async def create_config(self, guild_id: int) -> AutoModConfig:
        """
        Create a new AutoMod configuration for a guild with default values.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            The newly created AutoModConfig.
        """
        await self._db.execute(
            """
            INSERT INTO automod_config (guild_id)
            VALUES (?)
            """,
            (guild_id,),
        )
        config = await self.get_config(guild_id)
        assert config is not None
        log.info("AutoMod config created for guild %d", guild_id)
        return config

    async def get_or_create_config(self, guild_id: int) -> AutoModConfig:
        """
        Get the config for a guild, creating it with defaults if it doesn't exist.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            Existing or newly created AutoModConfig.
        """
        config = await self.get_config(guild_id)
        if config is None:
            config = await self.create_config(guild_id)
        return config

    async def update_config(self, config: AutoModConfig) -> None:
        """
        Update an existing AutoMod configuration.

        Args:
            config: The modified AutoModConfig instance.
        """
        # Convert lists back to comma-separated strings for storage
        allowed_domains = ",".join(config.get_allowed_domains_list())
        blocked_words = ",".join(config.get_blocked_words_list())
        
        await self._db.execute(
            """
            UPDATE automod_config SET
                enabled = ?,
                notify_mods = ?,
                log_channel = ?,
                default_action = ?,
                spam_enabled = ?,
                spam_messages = ?,
                spam_window = ?,
                mention_spam_enabled = ?,
                max_mentions = ?,
                link_filter_enabled = ?,
                block_invites = ?,
                block_all_links = ?,
                allowed_domains = ?,
                word_filter_enabled = ?,
                blocked_words = ?,
                caps_filter_enabled = ?,
                max_caps_percent = ?,
                min_message_length = ?,
                raid_protection_enabled = ?,
                raid_threshold = ?,
                raid_window = ?,
                raid_action = ?,
                updated_at = datetime('now')
            WHERE guild_id = ?
            """,
            (
                int(config.enabled),
                int(config.notify_mods),
                config.log_channel,
                config.default_action,
                int(config.spam_enabled),
                config.spam_messages,
                config.spam_window,
                int(config.mention_spam_enabled),
                config.max_mentions,
                int(config.link_filter_enabled),
                int(config.block_invites),
                int(config.block_all_links),
                allowed_domains,
                int(config.word_filter_enabled),
                blocked_words,
                int(config.caps_filter_enabled),
                config.max_caps_percent,
                config.min_message_length,
                int(config.raid_protection_enabled),
                config.raid_threshold,
                config.raid_window,
                config.raid_action,
                config.guild_id,
            ),
        )
        log.debug("AutoMod config updated for guild %d", config.guild_id)

    # ------------------------------------------------------------------ #
    # Rules                                                                 #
    # ------------------------------------------------------------------ #

    async def get_rule(self, rule_id: int, guild_id: int) -> Optional[AutoModRule]:
        """
        Retrieve a specific AutoMod rule.

        Args:
            rule_id: The rule's database ID.
            guild_id: The guild the rule belongs to.

        Returns:
            AutoModRule if found, None otherwise.
        """
        row = await self._db.fetch_one(
            "SELECT * FROM automod_rules WHERE id = ? AND guild_id = ?",
            (rule_id, guild_id),
        )
        return AutoModRule.from_row(row) if row else None

    async def get_rules_for_guild(self, guild_id: int) -> List[AutoModRule]:
        """
        Retrieve all rules for a guild, ordered by priority.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            List of AutoModRule instances (may be empty).
        """
        rows = await self._db.fetch_all(
            "SELECT * FROM automod_rules WHERE guild_id = ? ORDER BY priority DESC",
            (guild_id,),
        )
        return [AutoModRule.from_row(row) for row in rows]

    async def get_rules_by_type(self, guild_id: int, rule_type: str) -> List[AutoModRule]:
        """
        Retrieve all rules of a specific type for a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.
            rule_type: The rule type to filter by.

        Returns:
            List of AutoModRule instances (may be empty).
        """
        rows = await self._db.fetch_all(
            "SELECT * FROM automod_rules WHERE guild_id = ? AND rule_type = ? ORDER BY priority DESC",
            (guild_id, rule_type),
        )
        return [AutoModRule.from_row(row) for row in rows]

    async def create_rule(
        self,
        guild_id: int,
        rule_type: str,
        config: dict = None,
        action: str = "warn",
        duration: Optional[int] = None,
        custom_reason: Optional[str] = None,
        enabled: bool = True,
        priority: int = 0,
    ) -> AutoModRule:
        """
        Create a new AutoMod rule.

        Args:
            guild_id: Discord snowflake ID of the guild.
            rule_type: Type of rule (e.g., 'spam', 'links', 'words').
            config: Rule-specific configuration as a dictionary.
            action: Action to take when rule is triggered.
            duration: Duration for timeout/ban actions in seconds.
            custom_reason: Custom reason for this rule.
            enabled: Whether the rule is enabled.
            priority: Rule priority (higher = processed first).

        Returns:
            The newly created AutoModRule.
        """
        config_json = json.dumps(config or {})
        
        cursor = await self._db.execute(
            """
            INSERT INTO automod_rules (
                guild_id, rule_type, config, action, duration, 
                custom_reason, enabled, priority
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (guild_id, rule_type, config_json, action, duration, custom_reason, int(enabled), priority),
        )
        
        # Get the new rule ID
        rule_id = cursor.lastrowid
        
        rule = await self.get_rule(rule_id, guild_id)
        assert rule is not None
        log.info("AutoMod rule created: #%d for guild %d (type: %s)", rule_id, guild_id, rule_type)
        return rule

    async def update_rule(self, rule: AutoModRule) -> None:
        """
        Update an existing AutoMod rule.

        Args:
            rule: The modified AutoModRule instance.
        """
        config_json = json.dumps(rule.get_config_dict())
        
        await self._db.execute(
            """
            UPDATE automod_rules SET
                rule_type = ?,
                config = ?,
                action = ?,
                duration = ?,
                custom_reason = ?,
                enabled = ?,
                priority = ?,
                updated_at = datetime('now')
            WHERE id = ? AND guild_id = ?
            """,
            (
                rule.rule_type,
                config_json,
                rule.action,
                rule.duration,
                rule.custom_reason,
                int(rule.enabled),
                rule.priority,
                rule.id,
                rule.guild_id,
            ),
        )
        log.debug("AutoMod rule updated: #%d for guild %d", rule.id, rule.guild_id)

    async def delete_rule(self, rule_id: int, guild_id: int) -> bool:
        """
        Delete an AutoMod rule.

        Args:
            rule_id: The rule's database ID.
            guild_id: The guild the rule belongs to.

        Returns:
            True if a rule was deleted, False otherwise.
        """
        cursor = await self._db.execute(
            "DELETE FROM automod_rules WHERE id = ? AND guild_id = ?",
            (rule_id, guild_id),
        )
        deleted = cursor.rowcount > 0
        if deleted:
            log.info("AutoMod rule deleted: #%d for guild %d", rule_id, guild_id)
        return deleted

    async def delete_all_rules(self, guild_id: int) -> int:
        """
        Delete all AutoMod rules for a guild.

        Args:
            guild_id: Discord snowflake ID of the guild.

        Returns:
            Number of rules deleted.
        """
        cursor = await self._db.execute(
            "DELETE FROM automod_rules WHERE guild_id = ?",
            (guild_id,),
        )
        count = cursor.rowcount
        if count > 0:
            log.info("Deleted %d AutoMod rules for guild %d", count, guild_id)
        return count