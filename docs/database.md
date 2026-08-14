# Database

Kairo uses **SQLite** as its default database, accessed through **aiosqlite**
for non-blocking async I/O. All database interaction goes through the
repository layer — feature cogs never write SQL directly.

---

## Overview

The database layer has four components:

| Component      | Location                              | Responsibility                          |
|----------------|---------------------------------------|-----------------------------------------|
| `Database`     | `src/bot/database/connection.py`      | Connection, helpers, transactions       |
| Models         | `src/bot/database/models/`            | Python dataclasses mirroring each table |
| Repositories   | `src/bot/database/repositories/`      | Typed async data access objects         |
| Migrations     | `src/bot/database/migrations/`        | SQL files + runner                      |

---

## Database Connection

The `Database` class wraps an aiosqlite connection with helper methods.

```python
from src.bot.database import Database

db = Database(path="data/kairo.db")
await db.connect()      # Opens the file, applies pragmas
await db.run_migrations()  # Runs pending migrations

# Use helper methods:
row  = await db.fetch_one("SELECT * FROM guilds WHERE id = ?", (guild_id,))
rows = await db.fetch_all("SELECT * FROM guilds WHERE active = 1")
await db.execute("UPDATE guilds SET name = ? WHERE id = ?", (name, guild_id))

# Transactions:
async with db.transaction():
    await db.execute("INSERT INTO ...")
    await db.execute("UPDATE ...")

await db.close()
```

### Pragmas applied at connection time

| Pragma             | Value    | Reason                                    |
|--------------------|----------|-------------------------------------------|
| `journal_mode`     | `WAL`    | Better concurrent reads, crash resilience |
| `foreign_keys`     | `ON`     | Enforce referential integrity             |
| `synchronous`      | `NORMAL` | Balance between safety and performance    |

---

## Models

Models are plain Python dataclasses that mirror the shape of each database
table. They provide type safety and IDE autocompletion for data returned
by repositories.

Models are **not** an ORM. There is no magic mapping. Repositories return
model instances by constructing them from aiosqlite rows via `from_row()`.

### Available Models

| Model              | Table                | Description                            |
|--------------------|----------------------|----------------------------------------|
| `GuildConfig`      | `guilds`             | Per-guild configuration with welcome/leave settings |
| `UserRecord`       | `users`              | Per-user-per-guild record              |
| `ModerationCase`   | `moderation_cases`   | Single moderation action               |
| `Warning`          | `warnings`           | Warning entry linked to a case         |
| `AutoModConfig`    | `automod_config`     | Per-guild AutoMod settings             |
| `AutoModRule`      | `automod_rules`      | Individual AutoMod rules per guild     |

### Example

```python
from src.bot.database.models import GuildConfig

config = GuildConfig(id=123456789)
config.mod_log_channel = 987654321
print(config.locale)   # "en"
```

Models also contain the `CREATE_TABLE_SQL` used by migrations, so the
schema definition stays next to the dataclass.

---

## Repositories

Repositories are the only place in Kairo where SQL is written.
Each class handles one domain entity.

### Using repositories

```python
from src.bot.database.repositories import GuildRepository

repo = GuildRepository(db)

# Get or create
config = await repo.get_or_create(guild_id=123456789, name="My Server")

# Read
config = await repo.get(guild_id=123456789)
all_active = await repo.get_all_active()

# Update
config.mod_log_channel = 987654321
await repo.update(config)

# Deactivate (bot left the server)
await repo.deactivate(guild_id=123456789)
```

### Available Repositories

| Repository              | Entity            | Key methods                                    |
|-------------------------|-------------------|------------------------------------------------|
| `GuildRepository`       | `guilds`          | get, create, update, deactivate, get_or_create |
| `UserRepository`        | `users`           | get, create, update, get_or_create, increment_xp |
| `ModerationRepository`  | cases + warnings  | create_case, get_case, get_cases_for_user, create_warning, pardon_warning |
| `AutoModRepository`     | automod_config + automod_rules | get_or_create_config, update_config, get_rules_for_guild, create_rule, update_rule, delete_rule |

---

## Migrations

Migrations are numbered SQL files in `src/bot/database/migrations/`.
They are applied automatically at startup by `db.run_migrations()`.

### File naming

```
001_initial_schema.sql
002_add_automod_config.sql
003_add_ticket_tables.sql
```

Each file gets a sequential three-digit prefix. Files are discovered and run
in alphabetical order, so the prefix ensures correct ordering.

### How migrations work

1. On startup, `MigrationRunner` reads the `schema_migrations` tracking table.
2. It discovers `.sql` files in the migrations directory.
3. For each file not yet in `schema_migrations`, it:
   a. Opens the file and splits it into SQL statements (on `;`).
   b. Executes each statement inside a transaction.
   c. Inserts the filename into `schema_migrations`.
4. If any statement fails, the transaction is rolled back and startup is aborted.

### Adding a migration

1. Create a new SQL file:

```sql
-- 002_add_automod_config.sql
CREATE TABLE IF NOT EXISTS automod_config (
    guild_id  INTEGER PRIMARY KEY REFERENCES guilds(id) ON DELETE CASCADE,
    enabled   INTEGER NOT NULL DEFAULT 0,
    ...
);
```

2. The file will be applied automatically on next startup.

> Never modify an existing migration that has already been applied.
> If you need to change the schema, create a new migration file.

---

## Schema

### guilds

The guilds table stores per-server configuration. Added in Phase 3: welcome/leave message and auto-role fields.

| Column           | Type    | Description                                |
|------------------|---------|--------------------------------------------|
| `id`             | INTEGER | Discord guild snowflake ID (primary key)   |
| `name`           | TEXT    | Current guild name                         |
| `joined_at`      | INTEGER | Unix timestamp when bot joined             |
| `active`         | INTEGER | 1 = bot is in guild, 0 = bot was removed   |
| `mod_log_channel`| INTEGER | Channel ID for mod-log messages            |
| `log_channel`    | INTEGER | Channel ID for general logs                |
| `mod_role`       | INTEGER | Role ID granting moderator access          |
| `auto_role`      | INTEGER | Role ID for auto-assignment on join        |
| `locale`         | TEXT    | Locale code (default: 'en')                |
| `welcome_channel`| INTEGER | Channel for welcome messages (Phase 3)     |
| `welcome_message`| TEXT    | Welcome message template (Phase 3)         |
| `welcome_enabled`| INTEGER | Whether welcome messages are enabled (Phase 3) |
| `leave_channel`  | INTEGER | Channel for leave messages (Phase 3)      |
| `leave_message`  | TEXT    | Leave message template (Phase 3)           |
| `leave_enabled`  | INTEGER | Whether leave messages are enabled (Phase 3) |
| `updated_at`     | TEXT    | ISO 8601 last modification timestamp       |

### users

| Column      | Type    | Description                          |
|-------------|---------|--------------------------------------|
| `user_id`   | INTEGER | Discord user snowflake ID            |
| `guild_id`  | INTEGER | Discord guild snowflake ID (FK)      |
| `username`  | TEXT    | Cached Discord username              |
| `muted`     | INTEGER | 1 = currently muted                  |
| `warn_count`| INTEGER | Total warnings received              |
| `xp`        | INTEGER | Experience points (leveling)         |
| `first_seen`| TEXT    | ISO 8601 first interaction timestamp |
| `last_seen` | TEXT    | ISO 8601 last interaction timestamp  |

Primary key: `(user_id, guild_id)`

### moderation_cases

| Column               | Type    | Description                           |
|----------------------|---------|---------------------------------------|
| `id`                 | INTEGER | Auto-incrementing case number         |
| `guild_id`           | INTEGER | Guild this case belongs to (FK)       |
| `target_id`          | INTEGER | Discord ID of the actioned user       |
| `target_username`    | TEXT    | Cached display name of target         |
| `moderator_id`       | INTEGER | Discord ID of the moderator           |
| `moderator_username` | TEXT    | Cached display name of moderator      |
| `case_type`          | TEXT    | Type: ban, kick, timeout, warn, etc.  |
| `reason`             | TEXT    | Human-readable reason                 |
| `duration`           | INTEGER | Timeout duration in seconds           |
| `resolved`           | INTEGER | 1 = case is closed                    |
| `note`               | TEXT    | Moderator note added after the fact   |
| `created_at`         | TEXT    | ISO 8601 creation timestamp           |
| `updated_at`         | TEXT    | ISO 8601 last modification timestamp  |

### warnings

| Column      | Type    | Description                           |
|-------------|---------|---------------------------------------|
| `id`        | INTEGER | Auto-incrementing warning ID          |
| `case_id`   | INTEGER | Linked moderation case (FK)           |
| `guild_id`  | INTEGER | Guild this warning belongs to (FK)    |
| `user_id`   | INTEGER | Discord ID of the warned user         |
| `reason`    | TEXT    | Warning reason                        |
| `pardoned`  | INTEGER | 1 = warning has been pardoned         |
| `created_at`| TEXT    | ISO 8601 creation timestamp

---

## AutoMod Tables (Phase 3)

Added in migration `002_automod_tables.sql`:

### automod_config

Per-guild AutoMod settings.

| Column | Type | Description |
|--------|------|-------------|
| `guild_id` | INTEGER | Guild ID (PK, FK to guilds) |
| `enabled` | INTEGER | Whether AutoMod is enabled |
| `notify_mods` | INTEGER | Whether to notify moderators |
| `log_channel` | INTEGER | Channel for AutoMod logs |
| `default_action` | TEXT | Default action for violations |
| `spam_enabled` | INTEGER | Enable spam detection |
| `spam_messages` | INTEGER | Messages threshold for spam |
| `spam_window` | INTEGER | Time window in seconds |
| `mention_spam_enabled` | INTEGER | Enable mention spam detection |
| `max_mentions` | INTEGER | Maximum allowed mentions |
| `link_filter_enabled` | INTEGER | Enable link filtering |
| `block_invites` | INTEGER | Block Discord invites |
| `block_all_links` | INTEGER | Block all external links |
| `allowed_domains` | TEXT | Comma-separated allowed domains |
| `word_filter_enabled` | INTEGER | Enable word filtering |
| `blocked_words` | TEXT | Comma-separated blocked words |
| `caps_filter_enabled` | INTEGER | Enable caps filtering |
| `max_caps_percent` | INTEGER | Maximum caps percentage |
| `min_message_length` | INTEGER | Minimum message length for caps check |
| `raid_protection_enabled` | INTEGER | Enable raid protection |
| `raid_threshold` | INTEGER | Joins threshold for raid detection |
| `raid_window` | INTEGER | Time window for raid detection |
| `raid_action` | TEXT | Action to take on raid |
| `created_at` | TEXT | ISO 8601 creation timestamp |
| `updated_at` | TEXT | ISO 8601 last update timestamp |

### automod_rules

Individual AutoMod rules for each guild.

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Auto-incrementing rule ID (PK) |
| `guild_id` | INTEGER | Guild this rule belongs to (FK) |
| `rule_type` | TEXT | Rule type (spam, links, words, etc.) |
| `config` | TEXT | JSON-serialized rule configuration |
| `action` | TEXT | Action to take when triggered |
| `duration` | INTEGER | Duration for timeout/ban in seconds |
| `custom_reason` | TEXT | Custom reason for this rule |
| `enabled` | INTEGER | Whether rule is enabled |
| `priority` | INTEGER | Rule priority (higher = first) |
| `created_at` | TEXT | ISO 8601 creation timestamp |
| `updated_at` | TEXT | ISO 8601 last update timestamp |

Index: `idx_automod_rules_guild` on (guild_id, rule_type, priority)

---

## Enhanced Guilds Table (Phase 3)

Added in migration `003_welcome_and_roles.sql`:

New columns added to the `guilds` table:

| Column | Type | Description |
|--------|------|-------------|
| `welcome_channel` | INTEGER | Channel for welcome messages |
| `welcome_message` | TEXT | Welcome message template |
| `welcome_enabled` | INTEGER | Whether welcome messages are enabled |
| `leave_channel` | INTEGER | Channel for leave messages |
| `leave_message` | TEXT | Leave message template |
| `leave_enabled` | INTEGER | Whether leave messages are enabled |

---

## Models (Python Dataclasses)

Kairo uses Python dataclasses to represent database rows, providing type safety.

### Phase 3 Models

```python
# AutoMod models
from src.bot.database.models.automod import (
    AutoModConfig,
    AutoModRule,
    AutoModRuleType,  # Enum: SPAM, MENTION_SPAM, LINKS, WORDS, CAPS, RAID_PROTECTION
    AutoModAction,   # Enum: WARN, TIMEOUT, KICK, BAN, DELETE_MESSAGE, NOTIFY
)

# Updated Guild model
from src.bot.database.models.guild import GuildConfig
# GuildConfig now includes welcome/leave configuration fields
```

### Repository Usage

```python
from src.bot.database.repositories.automod import AutoModRepository

repo = AutoModRepository(db)

# Get or create config for a guild
config = await repo.get_or_create_config(guild_id)
config.spam_enabled = True
config.max_mentions = 10
await repo.update_config(config)

# Manage rules
rules = await repo.get_rules_for_guild(guild_id)
rule = await repo.create_rule(
    guild_id=guild_id,
    rule_type="words",
    config={"words": ["badword1", "badword2"]},
    action="warn",
)
```
