"""
src/bot/features/__init__.py
------------------------------
Kairo Features Package

Each subdirectory is an independent feature module. Features are loaded
as discord.py cogs by KairoBot.setup_hook() at startup.

Feature structure (each feature follows this pattern):
    features/
    └── <feature_name>/
        ├── __init__.py   — exports the setup() function
        ├── cog.py        — discord.py Cog with commands and event listeners
        ├── service.py    — business logic (no discord.py dependencies)
        └── views.py      — Components V2 panels and views (optional)

Available features:
    moderation  — Ban, kick, timeout, warn, case management
    automod     — Automated rule enforcement
    logging     — Audit log and event logging to channels
    utility     — Info commands and general utilities

Adding a new feature:
    1. Create a new subdirectory under src/bot/features/.
    2. Implement cog.py with a Cog subclass and a setup() function.
    3. Add the module path to the cog list in src/bot/core/bot.py.
    4. Document the feature in docs/features/.
"""
