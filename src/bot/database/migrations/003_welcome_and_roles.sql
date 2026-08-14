-- 003_welcome_and_roles.sql
-- -------------------------------
-- Kairo Welcome Messages and Auto Roles
--
-- Adds welcome/leave message and role-related configuration to the guilds table.
-- This migration supports Phase 3 welcome/leave messages and auto-role functionality.
--
-- Tables modified:
--   guilds — Add welcome/leave message and role configuration fields

-- ------------------------------------------------------------------ --
-- Modify guilds table to add welcome/leave configuration                 --
-- ------------------------------------------------------------------ --

ALTER TABLE guilds ADD COLUMN welcome_channel INTEGER;

ALTER TABLE guilds ADD COLUMN leave_channel INTEGER;

ALTER TABLE guilds ADD COLUMN welcome_message TEXT DEFAULT 'Welcome {member} to {server}!';

ALTER TABLE guilds ADD COLUMN leave_message TEXT DEFAULT '{member} has left {server}.';

ALTER TABLE guilds ADD COLUMN welcome_enabled INTEGER NOT NULL DEFAULT 1 CHECK (welcome_enabled IN (0, 1));

ALTER TABLE guilds ADD COLUMN leave_enabled INTEGER NOT NULL DEFAULT 0 CHECK (leave_enabled IN (0, 1));

-- Index for welcome/leave channels
CREATE INDEX IF NOT EXISTS idx_guilds_welcome_channel ON guilds (welcome_channel);
CREATE INDEX IF NOT EXISTS idx_guilds_leave_channel ON guilds (leave_channel);