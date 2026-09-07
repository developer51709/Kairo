"""
src/api/app.py
---------------
Kairo API Application

Defines and starts the aiohttp web application that serves as the
communication layer between the web dashboard and the Discord bot.

The API runs in the same asyncio event loop as the bot, allowing it
to directly call bot methods, access the database, and emit internal events.

Usage (from run.py):
    from src.api.app import create_app, start_api

    app = create_app(bot=bot, config=config)
    await start_api(app, host=config.api_host, port=config.api_port)
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from aiohttp import web

if TYPE_CHECKING:
    from src.bot.core.bot import KairoBot
    from src.bot.core.config import Config

from src.bot.core.logging import get_logger

log = get_logger(__name__)


# ------------------------------------------------------------------ #
# Middleware                                                           #
# ------------------------------------------------------------------ #

@web.middleware
async def auth_middleware(request: web.Request, handler):
    """
    API key authentication middleware.

    Only requests that target API-key-protected endpoints (anything under
    /api/ except /api/v1/me) are checked against API_SECRET. Everything else
    is public or cookie-authenticated:

        /health         — public health check
        /auth/*         — public Discord OAuth2 flow (start/callback/logout)
        /api/v1/me      — authenticated via the kairo_session cookie

    CLIENT_ID and CLIENT_SECRET do NOT protect these endpoints — the key that
    unlocks /api/* is API_SECRET from the project .env.
    """
    path = request.path
    is_cookie_or_public = (
        path == "/health"
        or path == "/api/v1/me"
        or path.startswith("/auth")
    )
    if is_cookie_or_public:
        return await handler(request)

    # Unknown/non-API paths (e.g. the API root) are left to the router so
    # they produce a normal 404 instead of an auth error.
    if not path.startswith("/api/"):
        return await handler(request)

    api_secret = request.app["config"].api_secret
    if not api_secret:
        # API_SECRET (not CLIENT_ID/CLIENT_SECRET) gates these endpoints.
        return web.json_response(
            {
                "error": "API_SECRET is not configured.",
                "detail": (
                    "Set API_SECRET in the project .env (next to .env.example) "
                    "to enable API-key protected endpoints. CLIENT_ID and "
                    "CLIENT_SECRET do not protect /api endpoints."
                ),
            },
            status=503,
        )

    provided_key = request.headers.get("X-API-Key", "")
    if provided_key != api_secret:
        return web.json_response(
            {"error": "Unauthorized. Invalid or missing API key."},
            status=401,
        )

    return await handler(request)


@web.middleware
async def error_middleware(request: web.Request, handler):
    """
    Global error handler. Returns JSON for all unhandled exceptions.
    """
    try:
        return await handler(request)
    except web.HTTPException:
        raise  # Let aiohttp handle HTTP exceptions natively
    except Exception as exc:
        log.exception("Unhandled API error for %s %s", request.method, request.path)
        return web.json_response(
            {"error": "Internal server error.", "detail": str(exc)},
            status=500,
        )


# ------------------------------------------------------------------ #
# Route handlers                                                       #
# ------------------------------------------------------------------ #

async def health(request: web.Request) -> web.Response:
    """
    GET /health

    Public health check endpoint. Returns HTTP 200 if the API is running.
    Does NOT require authentication.

    Response:
        {"status": "ok", "bot_ready": true/false}
    """
    bot: KairoBot = request.app["bot"]
    return web.json_response({
        "status": "ok",
        "bot_ready": not bot.is_closed() and bot.is_ready(),
    })


async def status(request: web.Request) -> web.Response:
    """
    GET /api/v1/status

    Returns bot operational status.

    Response:
        {"guild_count": N, "latency_ms": N, "user": {"id": ..., "name": ...}}
    """
    bot: KairoBot = request.app["bot"]
    return web.json_response({
        "guild_count": len(bot.guilds),
        "latency_ms": round(bot.latency * 1000),
        "user": {
            "id": str(bot.user.id) if bot.user else None,
            "name": str(bot.user) if bot.user else None,
        },
    })


# ------------------------------------------------------------------ #
# Application factory                                                  #
# ------------------------------------------------------------------ #

def create_app(bot: "KairoBot", config: "Config") -> web.Application:
    """
    Create and configure the aiohttp Application.

    Args:
        bot:    The running KairoBot instance.
        config: The loaded Config.

    Returns:
        A configured aiohttp.web.Application ready to be started.
    """
    app = web.Application(middlewares=[error_middleware, auth_middleware])

    # Attach shared state
    app["bot"] = bot
    app["config"] = config

    # Discord OAuth2 + dashboard sessions (public flow — see src/api/oauth.py)
    from src.api.oauth import OAuthManager, register_routes
    app["oauth"] = OAuthManager(config=config, bot=bot)
    register_routes(app)

    # Register routes
    app.router.add_get("/health", health)
    app.router.add_get("/api/v1/status", status)

    # TODO: Register guild, moderation, and config routes in Phase 4.

    log.info("API application created.")
    return app


async def start_api(app: web.Application, host: str, port: int) -> web.AppRunner:
    """
    Start the API server.

    Args:
        app:  The aiohttp Application.
        host: Host to bind to (e.g. "127.0.0.1").
        port: Port to listen on.

    Returns:
        The AppRunner (call runner.cleanup() on shutdown).
    """
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    log.info("API server started on http://%s:%d", host, port)
    return runner
