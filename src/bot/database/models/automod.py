"""
src/bot/database/models/automod.py
------------------------------------
AutoMod Rule Models

Defines the data shapes and SQL schema for AutoMod rules and configurations.
AutoMod rules are per-guild and control automated moderation behavior.

Table: automod_config - Per-guild AutoMod settings
Table: automod_rules - Individual AutoMod rules for each guild
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AutoModRuleType(str, Enum):
    """Types of AutoMod rules."""
    SPAM = "spam"           # Too many messages in a short time
    MENTION_SPAM = "mention_spam"  # Too many mentions in a message
    LINKS = "links"         # Unauthorized links/invites
    WORDS = "words"         # Blocked words/phrases
    CAPS = "caps"           # Excessive capitalization
    RAID_PROTECTION = "raid_protection"  # Rapid mass joins


class AutoModAction(str, Enum):
    """Actions AutoMod can take when a rule is triggered."""
    WARN = "warn"           # Issue a warning
    TIMEOUT = "timeout"     # Temporary mute
    KICK = "kick"           # Kick from server
    BAN = "ban"             # Ban from server
    DELETE_MESSAGE = "delete_message"  # Delete the violating message
    NOTIFY = "notify"       # Notify moderators only


# SQL for automod_config table
CREATE_AUTOMOD_CONFIG_SQL = """
CREATE TABLE IF NOT EXISTS automod_config (
    -- Discord snowflake ID of the guild. Primary key.
    guild_id       INTEGER PRIMARY KEY REFERENCES guilds(id) ON DELETE CASCADE,

    -- Whether AutoMod is enabled for this guild
    enabled        INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),

    -- Global AutoMod settings
    notify_mods    INTEGER NOT NULL DEFAULT 1 CHECK (notify_mods IN (0, 1)),
    log_channel    INTEGER,

    -- Default action for rule violations
    default_action TEXT    NOT NULL DEFAULT 'warn',

    -- Spam detection settings
    spam_enabled   INTEGER NOT NULL DEFAULT 1 CHECK (spam_enabled IN (0, 1)),
    spam_messages  INTEGER NOT NULL DEFAULT 5,
    spam_window    INTEGER NOT NULL DEFAULT 10,

    -- Mention spam settings
    mention_spam_enabled INTEGER NOT NULL DEFAULT 1 CHECK (mention_spam_enabled IN (0, 1)),
    max_mentions   INTEGER NOT NULL DEFAULT 5,

    -- Link filtering settings
    link_filter_enabled INTEGER NOT NULL DEFAULT 0 CHECK (link_filter_enabled IN (0, 1)),
    block_invites   INTEGER NOT NULL DEFAULT 1 CHECK (block_invites IN (0, 1)),
    block_all_links INTEGER NOT NULL DEFAULT 0 CHECK (block_all_links IN (0, 1)),
    allowed_domains TEXT,

    -- Word filtering settings
    word_filter_enabled INTEGER NOT NULL DEFAULT 0 CHECK (word_filter_enabled IN (0, 1)),
    blocked_words    TEXT,

    -- Caps filtering settings
    caps_filter_enabled INTEGER NOT NULL DEFAULT 0 CHECK (caps_filter_enabled IN (0, 1)),
    max_caps_percent INTEGER NOT NULL DEFAULT 70,
    min_message_length INTEGER NOT NULL DEFAULT 10,

    -- Raid protection settings
    raid_protection_enabled INTEGER NOT NULL DEFAULT 1 CHECK (raid_protection_enabled IN (0, 1)),
    raid_threshold INTEGER NOT NULL DEFAULT 5,
    raid_window     INTEGER NOT NULL DEFAULT 30,
    raid_action     TEXT    NOT NULL DEFAULT 'timeout',

    -- Immutable timestamp
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

# SQL for automod_rules table
CREATE_AUTOMOD_RULES_SQL = """
CREATE TABLE IF NOT EXISTS automod_rules (
    -- Auto-incrementing rule ID
    id              INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Guild this rule applies to
    guild_id        INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,

    -- Rule type (spam, mention_spam, links, words, caps, raid_protection)
    rule_type      TEXT    NOT NULL,

    -- Rule configuration (JSON serialized)
    config         TEXT    NOT NULL DEFAULT '{}',

    -- Action to take when rule is triggered
    action         TEXT    NOT NULL DEFAULT 'warn',

    -- Duration for timeout/ban actions (seconds)
    duration       INTEGER,

    -- Custom reason for this rule
    custom_reason  TEXT,

    -- Whether this rule is enabled
    enabled        INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0, 1)),

    -- Rule priority (higher = processed first)
    priority       INTEGER NOT NULL DEFAULT 0,

    -- Timestamp
    created_at     TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT    NOT NULL DEFAULT (datetime('now')),

    -- Foreign key
    FOREIGN KEY (guild_id) REFERENCES guilds(id) ON DELETE CASCADE
);

-- Index for faster rule lookup by guild
CREATE INDEX IF NOT EXISTS idx_automod_rules_guild
    ON automod_rules (guild_id, rule_type, priority);
"""


@dataclass
class AutoModConfig:
    """
    Represents the AutoMod configuration for a guild.
    
    This contains global AutoMod settings that apply across all rules.
    """
    guild_id: int
    enabled: bool = True
    notify_mods: bool = True
    log_channel: Optional[int] = None
    default_action: str = "warn"
    
    # Spam detection settings
    spam_enabled: bool = True
    spam_messages: int = 5
    spam_window: int = 10
    
    # Mention spam settings
    mention_spam_enabled: bool = True
    max_mentions: int = 5
    
    # Link filtering settings
    link_filter_enabled: bool = False
    block_invites: bool = True
    block_all_links: bool = False
    allowed_domains: str = ""
    
    # Word filtering settings
    word_filter_enabled: bool = False
    blocked_words: str = ""
    
    # Caps filtering settings
    caps_filter_enabled: bool = False
    max_caps_percent: int = 70
    min_message_length: int = 10
    
    # Raid protection settings
    raid_protection_enabled: bool = True
    raid_threshold: int = 5
    raid_window: int = 30
    raid_action: str = "timeout"
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row: object) -> AutoModConfig:
        """Construct an AutoModConfig from an aiosqlite.Row."""
        return cls(
            guild_id=row["guild_id"],
            enabled=bool(row["enabled"]),
            notify_mods=bool(row["notify_mods"]),
            log_channel=row["log_channel"],
            default_action=row["default_action"],
            spam_enabled=bool(row["spam_enabled"]),
            spam_messages=row["spam_messages"],
            spam_window=row["spam_window"],
            mention_spam_enabled=bool(row["mention_spam_enabled"]),
            max_mentions=row["max_mentions"],
            link_filter_enabled=bool(row["link_filter_enabled"]),
            block_invites=bool(row["block_invites"]),
            block_all_links=bool(row["block_all_links"]),
            allowed_domains=row["allowed_domains"],
            word_filter_enabled=bool(row["word_filter_enabled"]),
            blocked_words=row["blocked_words"],
            caps_filter_enabled=bool(row["caps_filter_enabled"]),
            max_caps_percent=row["max_caps_percent"],
            min_message_length=row["min_message_length"],
            raid_protection_enabled=bool(row["raid_protection_enabled"]),
            raid_threshold=row["raid_threshold"],
            raid_window=row["raid_window"],
            raid_action=row["raid_action"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def get_allowed_domains_list(self) -> list[str]:
        """Parse allowed domains from comma-separated string."""
        return [d.strip() for d in self.allowed_domains.split(",") if d.strip()]
    
    def get_blocked_words_list(self) -> list[str]:
        """Parse blocked words from comma-separated string."""
        return [w.strip().lower() for w in self.blocked_words.split(",") if w.strip()]


@dataclass
class AutoModRule:
    """
    Represents an individual AutoMod rule.
    """
    id: int
    guild_id: int
    rule_type: str
    config: str = "{}"  # JSON serialized configuration
    action: str = "warn"
    duration: Optional[int] = None
    custom_reason: Optional[str] = None
    enabled: bool = True
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @classmethod
    def from_row(cls, row: object) -> AutoModRule:
        """Construct an AutoModRule from an aiosqlite.Row."""
        return cls(
            id=row["id"],
            guild_id=row["guild_id"],
            rule_type=row["rule_type"],
            config=row["config"],
            action=row["action"],
            duration=row["duration"],
            custom_reason=row["custom_reason"],
            enabled=bool(row["enabled"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def get_config_dict(self) -> dict:
        """Parse config from JSON string."""
        import json
        try:
            return json.loads(self.config)
        except json.JSONDecodeError:
            return {}
