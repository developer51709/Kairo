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
| `GuildConfig`      | `guilds`             | Per-guild configuration                |
| `UserRecord`       | `users`              | Per-user-per-guild record              |
| `ModerationCase`   | `moderation_cases`   | Single moderation action               |
| `Warning`          | `warnings`           | Warning entry linked to a case         |

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
| `created_at`| TEXT    | ISO 8601 creation timestamp           |
