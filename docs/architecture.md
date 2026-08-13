# Architecture

Kairo is a multi-layer, modular platform. This document describes the
overall structure, the purpose of each layer, and how the layers interact.

---

## Overview

```
Kairo/
│
├── src/
│   ├── run.py               ← Main entrypoint
│   ├── setup.py             ← Interactive setup wizard
│   │
│   ├── bot/                 ← Discord bot (Python)
│   │   ├── core/            ← Shared infrastructure
│   │   │   ├── bot.py       ← KairoBot class
│   │   │   ├── config.py    ← Configuration system
│   │   │   ├── logging.py   ← Logging setup
│   │   │   └── events.py    ← Internal event bus
│   │   │
│   │   ├── database/        ← Data layer
│   │   │   ├── connection.py     ← Async SQLite wrapper
│   │   │   ├── models/           ← Table schema + dataclasses
│   │   │   ├── repositories/     ← Typed data access objects
│   │   │   └── migrations/       ← SQL migration files + runner
│   │   │
│   │   ├── components/      ← Discord Components V2 abstractions
│   │   │   ├── panel.py     ← High-level Panel builder
│   │   │   ├── container.py ← Container + Section
│   │   │   ├── text.py      ← Text + Separator
│   │   │   ├── interactive.py ← Button, SelectMenu, ActionRow
│   │   │   ├── modal.py     ← Modal dialog builder
│   │   │   └── pagination.py ← Multi-page interface
│   │   │
│   │   └── features/        ← Independent feature modules
│   │       ├── moderation/  ← Ban, kick, warn, cases
│   │       ├── automod/     ← Automated rule enforcement
│   │       ├── logging/     ← Server event logging
│   │       └── utility/     ← Info commands and utilities
│   │
│   ├── api/                 ← REST API (aiohttp)
│   │   └── app.py           ← API application + route handlers
│   │
│   └── dashboard/           ← Web dashboard (Vite) — Phase 4
│
├── docs/                    ← Documentation (this directory)
├── data/                    ← Database files (gitignored)
├── .env                     ← Local configuration (gitignored)
├── .env.example             ← Configuration template
└── requirements.txt         ← Python dependencies
```

---

## Layers

### 1. Core (`src/bot/core/`)

The foundation that all other layers depend on. Intentionally minimal.

| Module       | Responsibility                                                    |
|--------------|-------------------------------------------------------------------|
| `bot.py`     | `KairoBot` — extends discord.py Bot with Kairo infrastructure.    |
| `config.py`  | Loads and validates environment variables. Single source of truth.|
| `logging.py` | Configures Python logging. All modules use `get_logger(__name__)`.|
| `events.py`  | Internal pub/sub bus for cross-feature communication.             |

**Key principle:** Nothing in core knows about specific features. Core is a
stable foundation that features build on — never the reverse.

---

### 2. Database (`src/bot/database/`)

All persistent storage flows through this layer.

| Component      | Responsibility                                                     |
|----------------|--------------------------------------------------------------------|
| `connection.py`| Async SQLite connection, helper methods (execute, fetch, transaction). |
| `models/`      | Python dataclasses mirroring each database table.                  |
| `repositories/`| One class per domain entity with typed async query methods.        |
| `migrations/`  | Numbered SQL files + runner that applies them in order.            |

**Key principle:** Feature cogs never write SQL. They call repository methods.
This keeps SQL centralised, auditable, and testable.

---

### 3. Components (`src/bot/components/`)

Abstractions over Discord Components V2. Features use these instead of
constructing raw component dicts.

| Component      | Responsibility                                                    |
|----------------|-------------------------------------------------------------------|
| `panel.py`     | `Panel` — owns containers and sends/edits interaction responses.  |
| `container.py` | `Container`, `Section` — top-level layout blocks.                 |
| `text.py`      | `Text`, `Separator` — content and spacing.                        |
| `interactive.py`| `Button`, `SelectMenu`, `ActionRow` — interactive elements.      |
| `modal.py`     | `Modal`, `TextInput` — pop-up form dialogs.                       |
| `pagination.py`| `Paginator` — multi-page navigation interface.                    |

**Key principle:** Components are stateless value objects. They describe
*what* to render, not *how* to send it. Panel handles the sending.

---

### 4. Features (`src/bot/features/`)

Independent modules that each provide a discrete set of functionality.
Each feature follows a consistent internal structure:

```
features/<name>/
├── __init__.py   ← setup() function called by discord.py on load
├── cog.py        ← Cog with commands and event listeners
└── service.py    ← Business logic (no discord.py dependencies)
```

| Feature      | Responsibility                                                    |
|--------------|-------------------------------------------------------------------|
| `moderation` | Ban, kick, timeout, warn, case management.                        |
| `automod`    | Automated rule checks on messages and joins.                      |
| `logging`    | Posts server events to configured Discord channels.               |
| `utility`    | Info commands (userinfo, serverinfo, avatar, ping).               |

**Key principle:** Features are isolated. A feature cog imports from core,
database, and components — but never from other feature modules directly.
Cross-feature communication uses the event bus.

---

### 5. API (`src/api/`)

A lightweight aiohttp HTTP server that runs in the same asyncio event loop
as the bot. It is the only interface between the web dashboard and the bot.

The API is optional — only needed when running the dashboard.

```
api/
├── __init__.py   ← Package documentation
└── app.py        ← Application factory + route handlers
```

**Key principle:** The API does not access the database independently. It
delegates to bot methods and repositories via the shared KairoBot reference.

---

### 6. Dashboard (`src/dashboard/`)

A Vite-based single-page web application (Phase 4). Communicates with the
bot exclusively through the REST API. Never accesses the database directly.

---

## Data Flow

### Slash Command (e.g. /ban)

```
Discord → discord.py → ModerationCog.ban()
                            ↓
                    ModerationService.ban()
                            ↓
                    discord.Member.ban()    ← Discord API
                            ↓
                    ModerationRepository.create_case()
                            ↓
                    Database.execute()      ← SQLite
                            ↓
                    Panel.send(interaction) ← Discord interaction response
```

### Dashboard Configuration Update

```
Browser → PATCH /api/v1/guilds/{id}/config
              ↓ (auth middleware validates X-API-Key)
          API route handler
              ↓
          GuildRepository.update()
              ↓
          Database.execute()               ← SQLite
              ↓
          EventBus.emit("guild_config_updated")
              ↓
          Feature cogs reload their cache
```

---

## Dependency Rules

To prevent circular imports and maintain layering:

```
features → components, database, core
api      → database, core
database → core
core     → (no Kairo imports)
```

Features must not import from other features. Use the event bus for
cross-feature communication.

---

## Adding a New Feature

See [features.md](features.md) for a step-by-step guide.

## Database Changes

See [database.md](database.md) for how to add models, repositories, and migrations.

## Components V2

See [components.md](components.md) for how to use the component abstractions.
