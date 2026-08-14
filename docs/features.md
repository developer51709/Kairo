# Features

This guide explains how Kairo's feature system works and how to add new features. All features documented here are fully implemented as of Phase 3.

## Available Features

Kairo currently includes the following built-in features:

### 🔨 Moderation
Fully implemented moderation system with comprehensive case tracking.

- **Commands**: `/ban`, `/kick`, `/timeout`, `/warn`, `/history`, `/case`
- **Features**:
  - Ban, kick, and timeout commands with full Discord API integration
  - Warning system with case tracking and history
  - Moderation case management with unique case IDs
  - Full moderation logging to Discord channels with rich Components V2 formatting
  - All actions recorded in database with timestamps, moderator info, and reasons
  - Paginated history view for users with many cases
  - Individual case lookup by case number

### 🤖 AutoMod
Complete automated moderation rule engine with per-guild configuration.

- **Commands**: `/automod` (configuration interface)
- **Rule Types**:
  - Spam detection (messages in time window)
  - Mention spam detection (too many @mentions in a single message)
  - Link filtering (Discord invites, external URLs, domain whitelisting/blacklisting)
  - Word filtering (blocked words/phrases)
  - Caps filtering (excessive capitalization percentage)
  - Raid protection (rapid mass joins)
- **Configurable Actions**: warn, timeout, kick, ban, delete message, notify moderators
- **Features**:
  - Per-guild AutoMod configuration stored in database
  - Priority-based rule processing
  - AutoMod logging to configured channels
  - Event listeners for message and member join events
  - Whitelist/blacklist systems for domains and words

### 🎉 Welcome & Roles
Complete welcome message and auto-role system.

- **Commands**: `/welcome set`, `/welcome leave`, `/welcome disable`, `/autorole set`, `/autorole clear`
- **Features**:
  - Configurable welcome messages with template variables
  - Configurable leave messages with template variables
  - Auto-role assignment for new members
  - Enable/disable toggles for welcome and leave messages
  - Template variables: `{member}`, `{server}`, `{count}`, `{mention}`, `{user}`
  - Welcome/leave channels configurable per guild
  - Messages use Components V2 for rich formatting

### 🎭 Roles
Interactive role assignment system using Discord Components V2.

- **Commands**: `/role_button`, `/role_menu`, `/role_panel`, `/addrole`, `/removerole`
- **Features**:
  - Interactive role buttons (click to get role)
  - Role selection menus (dropdown selection with multi-select support)
  - Multi-button role panels (modal-based creation)
  - Toggle behavior (click to get role, click again to remove)
  - Support for role emojis and custom labels
  - Manual role assignment/removal commands
  - Configurable max selections for menus (1-25)
  - Automatic role assignment on member join (via auto-role)

### ⚙️ Configuration
Centralized server configuration system for all Kairo features.

- **Commands**: `/setup`, `/set_modlog`, `/set_locale`, `/set_modrole`, `/config_show`, `/config_reset`, `/toggle_welcome`, `/toggle_leave`
- **Features**:
  - Centralized server configuration stored in SQLite database
  - Per-guild settings for all features
  - Set mod-log channel for moderation action logging
  - Set log channel for general server events
  - Set welcome and leave channels
  - Set moderator role (grants access to moderation commands)
  - Set auto-role (automatically assigned to new members)
  - Set server locale for localized messages
  - Feature toggles for welcome/leave messages
  - View complete configuration status
  - Reset configuration to defaults with confirmation
  - Interactive setup panel with quick configuration options

### 📋 Logging
Event logging system with database tracking.

- **Features**:
  - Guild join/remove event logging
  - Message edit and delete tracking
  - Member ban/unban tracking
  - Scaffold for comprehensive event logging
  - All events stored in database for audit purposes
  - Future: Rich Components V2 panels for log displays

### 🔧 Utility
General purpose commands for server members.

- **Commands**: `/help`, `/ping`, `/botinfo`, `/userinfo`, `/serverinfo`, `/avatar`
- **Features**:
  - Help command with Components V2 formatting and category filtering
  - Ping/latency check with detailed response times
  - Bot information display (version, uptime, server count)
  - User information display (joined date, roles, status)
  - Server information display (member count, channels, roles)
  - Avatar display with high-resolution image links

---

This guide explains how Kairo's feature system works and how to add new features.

---

## What is a Feature?

A feature is a self-contained module that provides a discrete set of
functionality — moderation commands, automod rules, ticket handling, etc.

Features live in `src/bot/features/`. Each feature is a Python package
(directory with `__init__.py`) that follows a consistent structure.

---

## Feature Structure

```
src/bot/features/<feature_name>/
├── __init__.py   ← Exports setup() — required for discord.py to load the feature
├── cog.py        ← discord.py Cog: slash commands, event listeners
├── service.py    ← Business logic (no discord.py types in method signatures)
└── views.py      ← Complex LayoutView subclasses (optional)
```

### `__init__.py`

Must export a `setup(bot)` async function that registers the cog:

```python
from .cog import MyCog

async def setup(bot) -> None:
    await bot.add_cog(MyCog(bot))
```

### `cog.py`

The Cog handles Discord-facing concerns:
- Slash command definitions (`@app_commands.command`)
- Event listeners (`@commands.Cog.listener`)
- Permission checks
- Delegates business logic to the service

```python
class MyCog(commands.Cog, name="MyFeature"):
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self.service = MyService(bot)

    @app_commands.command(name="mycommand", description="Does something.")
    @app_commands.guild_only()
    async def mycommand(self, interaction: discord.Interaction, ...) -> None:
        await self.service.do_something(interaction, ...)
```

### `service.py`

Contains all business logic. This separation allows:
- Logic to be called from other contexts (automod triggering a moderation action)
- Testing without Discord interactions
- Keeping cogs thin and readable

```python
import discord
from ...components import send_layout

class MyService:
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot

    async def do_something(self, interaction: discord.Interaction, ...) -> None:
        view = discord.ui.LayoutView()
        view.add_item(discord.ui.Container(
            discord.ui.TextDisplay("✅ Done!"),
        ))
        await send_layout(interaction, view, ephemeral=True)
```

---

## Auto-Discovery

Kairo automatically discovers and loads feature cogs at startup. There is
**no registration step** — you only need to create the files.

The loader scans `src/bot/features/` and loads any subdirectory that:
1. Is a Python package (contains `__init__.py`)
2. Contains a `cog.py` file

Directories starting with `_` (e.g. `__pycache__`) are skipped automatically.

At startup you will see log output like:

```
Discovered 4 feature cog(s): automod, logging, moderation, utility
Loaded cog: src.bot.features.automod.cog
Loaded cog: src.bot.features.logging.cog
Loaded cog: src.bot.features.moderation.cog
Loaded cog: src.bot.features.utility.cog
Cog loading complete: 4 loaded, 0 failed.
```

If a cog fails to load (syntax error, missing dependency, etc.), the error
is logged and the remaining cogs continue loading.

---

## Adding a New Feature

### Step 1 — Create the directory

```bash
mkdir src/bot/features/tickets
touch src/bot/features/tickets/__init__.py
touch src/bot/features/tickets/cog.py
touch src/bot/features/tickets/service.py
```

### Step 2 — Write the `__init__.py`

```python
# src/bot/features/tickets/__init__.py
"""
Tickets feature — support ticket system.

Commands:
    /ticket open    — Open a new support ticket
    /ticket close   — Close the current ticket
    /ticket add     — Add a user to the ticket
"""

from .cog import TicketsCog

async def setup(bot) -> None:
    await bot.add_cog(TicketsCog(bot))
```

### Step 3 — Write the Cog

```python
# src/bot/features/tickets/cog.py
import discord
from discord import app_commands
from discord.ext import commands

from ...core.bot import KairoBot
from .service import TicketsService


class TicketsCog(commands.Cog, name="Tickets"):
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self.service = TicketsService(bot)

    @app_commands.command(name="ticket", description="Open a support ticket.")
    @app_commands.guild_only()
    async def ticket(self, interaction: discord.Interaction) -> None:
        await self.service.open_ticket(interaction)


async def setup(bot: KairoBot) -> None:
    await bot.add_cog(TicketsCog(bot))
```

That's it — restart the bot and the `tickets` feature will be discovered
and loaded automatically. No changes to `bot.py` are required.

### Step 4 — Document it

Add the feature to the table at the bottom of this file and create
`docs/features/tickets.md` with command documentation.

---

## Database Access from a Feature

Features should use repositories, not raw SQL:

```python
from ...database.repositories.guild import GuildRepository

class TicketsService:
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot

    def _guild_repo(self) -> GuildRepository:
        return GuildRepository(self.bot.db)

    async def open_ticket(self, interaction: discord.Interaction) -> None:
        config = await self._guild_repo().get_or_create(interaction.guild.id)
        # ... use config to find the ticket category channel ...
```

If your feature needs new tables, create a migration. See [database.md](database.md).

---

## Components V2 in Features

All Discord interfaces use `discord.ui.LayoutView`. See [components.md](components.md)
for the full guide. The short version:

```python
import discord
from ...components import send_layout

# Build the view
view = discord.ui.LayoutView()
view.add_item(discord.ui.Container(
    discord.ui.TextDisplay("✅ Action completed."),
))

# Send it
await send_layout(interaction, view, ephemeral=True)
```

---

## Cross-Feature Communication

Features must not import from each other. Use the event bus instead:

```python
# In moderation/service.py — emit an event
await self.bot.bus.emit("moderation_action", case=case)

# In logging/cog.py — listen for the event
@bot.bus.on("moderation_action")
async def handle_mod_action(case: ModerationCase) -> None:
    await post_to_mod_log(case)
```

---

## Permission Checks

Always check permissions before executing a moderation action:

```python
async def _check_moderator(self, interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator:
        return True
    if interaction.user.guild_permissions.manage_guild:
        return True
    await interaction.response.send_message(
        "❌ You do not have permission to use this command.",
        ephemeral=True,
    )
    return False
```

For commands that affect other users, also verify the bot has the
necessary permissions before attempting the action.

---

## Existing Features

| Feature      | Module path                       | Commands                                                   |
|--------------|-----------------------------------|------------------------------------------------------------|
| Moderation   | `src.bot.features.moderation.cog` | /ban, /kick, /timeout, /warn, /history, /case             |
| AutoMod      | `src.bot.features.automod.cog`    | /automod                                                   |
| Logging      | `src.bot.features.logging.cog`    | (automatic — event listeners)                              |
| Utility      | `src.bot.features.utility.cog`    | /help, /ping, /botinfo, /userinfo, /serverinfo, /avatar   |
| Welcome      | `src.bot.features.welcome.cog`    | /welcome set, /welcome leave, /welcome disable, /autorole set, /autorole clear |
| Roles        | `src.bot.features.roles.cog`      | /role_button, /role_menu, /role_panel, /addrole, /removerole |
| Config       | `src.bot.features.config.cog`     | /setup, /set_modlog, /set_locale, /set_modrole, /config_show, /config_reset, /toggle_welcome, /toggle_leave |
