# Copilot Instructions for Kairo

## Project Overview

**Kairo** is a self-hostable Discord platform combining a Python bot backend,
a modern Vite-powered web dashboard, and an extensible component system.

The project is currently in **Phase 1 (Foundation)** and provides a working
architectural scaffold that Phase 2+ will build on.

---

## Technology Stack

| Component   | Technology             |
|-------------|------------------------|
| Bot backend | Python 3.11+, discord.py 2.7.1 |
| Database    | SQLite via aiosqlite   |
| API server  | aiohttp                |
| Dashboard   | Vite + TypeScript (Phase 4) |
| Auth        | Discord OAuth2         |
| Discord UI  | Components V2 (custom abstraction) |

---

## Directory Structure

```
Kairo/
├── src/
│   ├── run.py                    # Main entrypoint. Usage: python src/run.py [--with-api] [--debug]
│   ├── setup.py                  # Interactive setup wizard. Usage: python src/setup.py
│   │
│   ├── bot/
│   │   ├── core/                 # Shared infrastructure
│   │   │   ├── __init__.py
│   │   │   ├── bot.py            # KairoBot: extends discord.py Bot; owns config, bus, lifecycle
│   │   │   ├── config.py         # Config: loads .env; all env vars are properties here
│   │   │   ├── logging.py        # setup_logging() + get_logger() — use this everywhere
│   │   │   └── events.py         # EventBus: async pub/sub for cross-feature communication
│   │   │
│   │   ├── database/             # All data persistence
│   │   │   ├── __init__.py       # Exports Database
│   │   │   ├── connection.py     # Database: async SQLite wrapper with transaction support
│   │   │   ├── models/
│   │   │   │   ├── guild.py      # GuildConfig dataclass + CREATE_TABLE_SQL
│   │   │   │   ├── user.py       # UserRecord dataclass + CREATE_TABLE_SQL
│   │   │   │   └── moderation.py # ModerationCase, Warning, CaseType enum
│   │   │   ├── repositories/
│   │   │   │   ├── guild.py      # GuildRepository: get, create, update, deactivate, get_or_create
│   │   │   │   ├── user.py       # UserRepository: get, create, update, get_or_create, increment_xp
│   │   │   │   └── moderation.py # ModerationRepository: create_case, get cases/warnings, pardon
│   │   │   └── migrations/
│   │   │       ├── runner.py     # MigrationRunner: discovers and applies .sql files
│   │   │       └── 001_initial_schema.sql  # guilds, users, moderation_cases, warnings tables
│   │   │
│   │   ├── components/           # Discord Components V2 abstractions
│   │   │   ├── __init__.py       # Exports: Panel, Container, Section, Text, Separator,
│   │   │   │                     #          Button, ButtonStyle, SelectMenu, ActionRow,
│   │   │   │                     #          Modal, TextInput, Paginator
│   │   │   ├── panel.py          # Panel: top-level message owner; .send(), .edit(), .followup()
│   │   │   ├── container.py      # Container (type 17), Section (type 9)
│   │   │   ├── text.py           # Text (type 10), Separator (type 14)
│   │   │   ├── interactive.py    # Button (type 2), SelectMenu (type 3), ActionRow (type 1)
│   │   │   ├── modal.py          # Modal, TextInput, TextInputStyle
│   │   │   ├── pagination.py     # Paginator: multi-page navigation interface
│   │   │   └── base.py           # KairoComponent ABC with to_dict() interface
│   │   │
│   │   └── features/             # Independent feature modules
│   │       ├── moderation/
│   │       │   ├── cog.py        # Slash commands: /ban /kick /timeout /warn /history /case
│   │       │   └── service.py    # ModerationService: applies Discord actions + records cases
│   │       ├── automod/
│   │       │   └── cog.py        # AutoModCog: on_message + on_member_join listeners (scaffold)
│   │       ├── logging/
│   │       │   └── cog.py        # LoggingCog: member/message event listeners (scaffold)
│   │       └── utility/
│   │           └── cog.py        # Commands: /ping /botinfo /userinfo /serverinfo /avatar
│   │
│   ├── api/
│   │   ├── __init__.py           # API package documentation
│   │   └── app.py                # aiohttp app; create_app() + start_api(); /health + /api/v1/status
│   │
│   └── dashboard/                # Vite web dashboard — Phase 4 placeholder
│       ├── .gitignore
│       └── README.md
│
├── docs/                         # Documentation
│   ├── index.md                  # Documentation index
│   ├── getting-started.md        # Installation and first-run guide
│   ├── configuration.md          # All environment variables explained
│   ├── architecture.md           # System architecture and layer design
│   ├── components.md             # Components V2 usage guide
│   ├── database.md               # Database models, repositories, migrations
│   ├── features.md               # How to add and extend features
│   ├── api.md                    # REST API reference
│   ├── dashboard.md              # Dashboard design (Phase 4)
│   ├── self-hosting.md           # Self-hosting: Linux, VPS, Docker, tunnels
│   └── contributing.md          # Contributing guide
│
├── data/                         # SQLite database files (gitignored, created at runtime)
├── .env                          # Local configuration (gitignored)
├── .env.example                  # Configuration template with all variables documented
├── requirements.txt              # Pinned Python dependencies
├── README.md                     # Project overview and roadmap
└── DONATE.md
```

---

## Architecture Principles

### Layering (enforce strictly)

```
features → components, database, core
api      → database, core
database → core
core     → (no Kairo imports)
```

Features must never import from other features. Use `bot.bus.emit()` / `bot.bus.on()`.

### Core patterns

- **Config via Config:** Never read `os.environ` directly. Add a property to `src/bot/core/config.py`.
- **Logging via get_logger:** `from src.bot.core.logging import get_logger; log = get_logger(__name__)`
- **SQL via Repositories:** Never write SQL outside `src/bot/database/repositories/`.
- **Discord UI via Components:** Use `Panel`, `Container`, `Text`, etc. — never raw dicts.
- **Dependency injection:** Features receive `bot` in `__init__`. No module-level globals for shared state.

---

## Key Classes

### `KairoBot` (src/bot/core/bot.py)
- Extends `discord.ext.commands.Bot`
- `bot.config` — `Config` instance
- `bot.bus` — `EventBus` instance
- `bot.db` — `Database` instance (attached in `setup_hook`)
- `bot.start_kairo()` — async entrypoint (called by `run.py`)

### `Config` (src/bot/core/config.py)
- Loads `.env` via `python-dotenv` in `__post_init__`
- Properties: `bot_token`, `client_id`, `client_secret`, `prefix`, `guild_id`, `db_path`, `log_level`, `api_host`, `api_port`, `api_secret`, `dashboard_url`, `oauth_redirect`, `debug`
- Raises `ConfigError` on missing required variables

### `EventBus` (src/bot/core/events.py)
- `bus.on("event_name")` — decorator for persistent listeners
- `bus.once("event_name")` — decorator for one-time listeners
- `await bus.emit("event_name", **kwargs)` — fire event concurrently to all listeners
- `bus.off("event_name", handler)` — unregister a listener

### `Database` (src/bot/database/connection.py)
- `await db.connect()` — open connection with WAL + foreign keys
- `await db.run_migrations()` — apply pending migrations
- `await db.fetch_one(sql, params)` — returns `aiosqlite.Row | None`
- `await db.fetch_all(sql, params)` — returns `list[aiosqlite.Row]`
- `await db.execute(sql, params)` — returns cursor
- `async with db.transaction():` — wraps statements in a transaction

### `Panel` (src/bot/components/panel.py)
- `Panel(*containers, ephemeral=False)`
- `await panel.send(interaction)` — primary response
- `await panel.edit(interaction)` — edit existing response
- `await panel.followup(interaction)` — followup after defer
- `await panel.send_to_channel(channel)` — proactive channel message

---

## Adding Features

1. Create `src/bot/features/<name>/__init__.py`, `cog.py`, `service.py`
2. `__init__.py` must export `async def setup(bot) -> None`
3. Add the module path to `cog_modules` list in `src/bot/core/bot.py`
4. See `docs/features.md` for full guide

## Adding Database Tables

1. Create model in `src/bot/database/models/<name>.py`
2. Create repository in `src/bot/database/repositories/<name>.py`
3. Create migration `src/bot/database/migrations/NNN_description.sql`
4. Export from `models/__init__.py` and `repositories/__init__.py`
5. See `docs/database.md` for full guide

---

## Environment Variables (Required)

| Variable       | Description                     |
|----------------|---------------------------------|
| `BOT_TOKEN`    | Discord bot token               |
| `CLIENT_ID`    | Discord application Client ID   |
| `CLIENT_SECRET`| Discord OAuth2 Client Secret    |

See `.env.example` and `docs/configuration.md` for all variables.

---

## Commands

```bash
# First-time setup
python src/setup.py

# Run the bot
python src/run.py

# Run the bot + API server
python src/run.py --with-api

# Run in debug mode
python src/run.py --debug
```

---

## Current Status (Phase 1)

### Implemented ✅
- Project structure and all packages
- `KairoBot` with lifecycle, intents, cog loading, slash sync
- `Config` with all env var properties and validation
- `setup_logging()` + `get_logger()` with coloured console output
- `EventBus` with async pub/sub, once-listeners, concurrent dispatch
- `Database` with aiosqlite, WAL, foreign keys, transaction context manager
- `MigrationRunner` with tracking table and ordered file discovery
- Models: `GuildConfig`, `UserRecord`, `ModerationCase`, `Warning`, `CaseType`
- Repositories: `GuildRepository`, `UserRepository`, `ModerationRepository`
- Migration: `001_initial_schema.sql` (guilds, users, moderation_cases, warnings)
- Components: `Panel`, `Container`, `Section`, `Text`, `Separator`, `Button`, `ButtonStyle`, `SelectMenu`, `SelectOption`, `ActionRow`, `Modal`, `TextInput`, `Paginator`
- Feature scaffolds: moderation (cog + service), automod, logging, utility
- Utility commands: `/ping`, `/botinfo`, `/userinfo`, `/serverinfo`, `/avatar`
- Moderation commands: `/ban`, `/kick`, `/timeout`, `/warn`, `/history`, `/case`
- API: `create_app()` + `start_api()` + `/health` + `/api/v1/status`
- `src/run.py` — full entrypoint with arg parsing, graceful shutdown, optional API
- `src/setup.py` — interactive wizard writing `.env`, optional pip install
- `requirements.txt`, `.env.example`
- Full documentation: 10 docs in `docs/`

### Planned (Phase 2+)
- Database attached to KairoBot in `setup_hook`
- Components V2 full integration (pending discord.py 2.x API surface confirmation)
- Full moderation service with database writes
- AutoMod rule engine
- Logging feature channel output
- REST API full endpoint suite
- Web dashboard (Vite)
- Docker support
- Plugin system
