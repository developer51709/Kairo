-- 002_automod_tables.sql
-- ---------------------------
-- Kairo AutoMod Tables
--
-- Creates the tables required for Phase 3 AutoMod functionality.
-- This migration adds support for configurable auto-moderation rules.
--
-- Tables created:
--   automod_config — Per-guild AutoMod settings
--   automod_rules — Individual AutoMod rules for each guild

-- ------------------------------------------------------------------ --
-- automod_config                                                         --
-- ------------------------------------------------------------------ --

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

-- ------------------------------------------------------------------ --
-- automod_rules                                                          --
-- ------------------------------------------------------------------ --

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