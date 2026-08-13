"""
src/api/__init__.py
--------------------
Kairo REST API Package

The API is a lightweight HTTP server that allows the web dashboard
to communicate with the running bot. It runs in the same process as
the bot using aiohttp, sharing the bot's asyncio event loop.

Architecture:
    - The API is authentication-protected via a shared secret (API_SECRET env var).
    - All endpoints require the X-API-Key header matching the secret.
    - The API talks to the bot through the same Database instance and KairoBot
      reference — it does NOT access the database directly on behalf of the dashboard.
    - The dashboard authenticates users via Discord OAuth2, then calls the API
      with the bot's API secret to perform actions.

Planned endpoints:

    Auth / Meta:
        GET  /health            — Health check (no auth required)
        GET  /api/v1/status     — Bot status, guild count, latency

    Guilds:
        GET  /api/v1/guilds                      — Guilds the bot is in
        GET  /api/v1/guilds/{guild_id}           — Guild config
        PATCH /api/v1/guilds/{guild_id}          — Update guild config

    Moderation:
        GET  /api/v1/guilds/{guild_id}/cases     — Recent cases
        GET  /api/v1/guilds/{guild_id}/cases/{id} — Specific case
        GET  /api/v1/guilds/{guild_id}/users/{user_id}/warnings — User warnings

    Configuration:
        GET  /api/v1/guilds/{guild_id}/config/moderation  — Moderation config
        PATCH /api/v1/guilds/{guild_id}/config/moderation — Update moderation config
        GET  /api/v1/guilds/{guild_id}/config/automod     — AutoMod config
        PATCH /api/v1/guilds/{guild_id}/config/automod    — Update automod config

Phase 1: Scaffold only — app.py and a health check endpoint.
Phase 4: Full implementation with all dashboard endpoints.
"""
