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

    Skips authentication for /health (public endpoint).
    All other routes require the X-API-Key header to match the
    configured API_SECRET.
    """
    if request.path == "/health":
        return await handler(request)

    api_secret = request.app["config"].api_secret
    if not api_secret:
        # No secret configured — reject all non-health requests.
        return web.json_response(
            {"error": "API authentication is not configured."},
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
