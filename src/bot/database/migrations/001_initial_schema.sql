-- 001_initial_schema.sql
-- -------------------------
-- Kairo Initial Database Schema
--
-- Creates the core tables required for Phase 1 operation.
-- This migration is applied automatically on first startup.
--
-- Tables created:
--   guilds            — Per-guild configuration
--   users             — Per-user-per-guild records
--   moderation_cases  — Moderation action history
--   warnings          — Warning records (subset of cases)


-- ------------------------------------------------------------------ --
-- guilds                                                              --
-- ------------------------------------------------------------------ --

CREATE TABLE IF NOT EXISTS guilds (
    id              INTEGER PRIMARY KEY,
    name            TEXT    NOT NULL DEFAULT '',
    joined_at       INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    active          INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    mod_log_channel INTEGER,
    log_channel     INTEGER,
    mod_role        INTEGER,
    auto_role       INTEGER,
    locale          TEXT    NOT NULL DEFAULT 'en',
    updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
);


-- ------------------------------------------------------------------ --
-- users                                                               --
-- ------------------------------------------------------------------ --

CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER NOT NULL,
    guild_id    INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    username    TEXT    NOT NULL DEFAULT '',
    muted       INTEGER NOT NULL DEFAULT 0 CHECK (muted IN (0, 1)),
    warn_count  INTEGER NOT NULL DEFAULT 0,
    xp          INTEGER NOT NULL DEFAULT 0,
    first_seen  TEXT    NOT NULL DEFAULT (datetime('now')),
    last_seen   TEXT    NOT NULL DEFAULT (datetime('now')),

    PRIMARY KEY (user_id, guild_id)
);


-- ------------------------------------------------------------------ --
-- moderation_cases                                                    --
-- ------------------------------------------------------------------ --

CREATE TABLE IF NOT EXISTS moderation_cases (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id            INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    target_id           INTEGER NOT NULL,
    target_username     TEXT    NOT NULL DEFAULT '',
    moderator_id        INTEGER NOT NULL,
    moderator_username  TEXT    NOT NULL DEFAULT '',
    case_type           TEXT    NOT NULL,
    reason              TEXT,
    duration            INTEGER,
    resolved            INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1)),
    note                TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Index: look up cases by target user quickly
CREATE INDEX IF NOT EXISTS idx_cases_target
    ON moderation_cases (guild_id, target_id);


-- ------------------------------------------------------------------ --
-- warnings                                                            --
-- ------------------------------------------------------------------ --

CREATE TABLE IF NOT EXISTS warnings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id     INTEGER NOT NULL REFERENCES moderation_cases(id) ON DELETE CASCADE,
    guild_id    INTEGER NOT NULL REFERENCES guilds(id) ON DELETE CASCADE,
    user_id     INTEGER NOT NULL,
    reason      TEXT,
    pardoned    INTEGER NOT NULL DEFAULT 0 CHECK (pardoned IN (0, 1)),
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Index: look up warnings by user quickly
CREATE INDEX IF NOT EXISTS idx_warnings_user
    ON warnings (guild_id, user_id);
