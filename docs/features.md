# Features

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
└── views.py      ← Components V2 panels (optional — for complex UIs)
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
class MyService:
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot

    async def do_something(self, interaction: discord.Interaction, ...) -> None:
        # ... logic here ...
        panel = Panel(Container(Text("Done!")), ephemeral=True)
        await panel.send(interaction)
```

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
from discord.ext import commands
from discord import app_commands
import discord

from ...core.bot import KairoBot
from .service import TicketsService

class TicketsCog(commands.Cog, name="Tickets"):
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot
        self.service = TicketsService(bot)

    @app_commands.command(name="ticket", description="Manage support tickets.")
    @app_commands.guild_only()
    async def ticket(self, interaction: discord.Interaction) -> None:
        await self.service.open_ticket(interaction)

async def setup(bot: KairoBot) -> None:
    await bot.add_cog(TicketsCog(bot))
```

### Step 4 — Register the feature

Add the module path to the cog list in `src/bot/core/bot.py`:

```python
cog_modules: list[str] = [
    "src.bot.features.moderation.cog",
    "src.bot.features.automod.cog",
    "src.bot.features.logging.cog",
    "src.bot.features.utility.cog",
    "src.bot.features.tickets.cog",   # ← Add this
]
```

### Step 5 — Document it

Add the feature to `docs/features.md` and create `docs/features/tickets.md`
with command documentation.

---

## Database Access from a Feature

Features should use repositories, not raw SQL:

```python
from ...database.repositories.guild import GuildRepository

class TicketsService:
    def __init__(self, bot: KairoBot) -> None:
        self.bot = bot

    def _guild_repo(self):
        return GuildRepository(self.bot.db)

    async def open_ticket(self, interaction: discord.Interaction) -> None:
        config = await self._guild_repo().get_or_create(interaction.guild.id)
        # ... use config to find the ticket category channel ...
```

If your feature needs new tables, create a migration. See [database.md](database.md).

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

| Feature      | Module path                           | Commands                        |
|--------------|---------------------------------------|---------------------------------|
| Moderation   | `src.bot.features.moderation.cog`     | /ban, /kick, /timeout, /warn, /history, /case |
| AutoMod      | `src.bot.features.automod.cog`        | (automatic — no commands yet)   |
| Logging      | `src.bot.features.logging.cog`        | (automatic — no commands yet)   |
| Utility      | `src.bot.features.utility.cog`        | /ping, /botinfo, /userinfo, /serverinfo, /avatar |
