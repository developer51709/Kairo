"""
src/api/oauth.py
----------------
Discord OAuth2 + dashboard sessions.

Implements the server-side half of the dashboard login flow described in
docs/dashboard.md. The Discord application credentials (CLIENT_ID and
CLIENT_SECRET from the root .env) are consumed here — inside the API
process — and are never exposed to the browser.

Routes (all public — no X-API-Key required):
    GET /auth/discord    → 302 to Discord's consent screen
    GET /auth/callback   → exchanges ?code= for a session cookie, redirects
                           back to the dashboard
    GET /auth/logout     → clears the session cookie, redirects to dashboard
    GET /api/v1/me       → current user + manageable guilds (session cookie)

Sessions are stored in memory for now (fine for a single self-hosted
instance). Persisting them (e.g. in the SQLite database) is future work.
"""

from __future__ import annotations

import secrets
import time
from typing import TYPE_CHECKING, Optional
from urllib.parse import urlencode

import aiohttp
from aiohttp import web

if TYPE_CHECKING:
    from src.bot.core.bot import KairoBot
    from src.bot.core.config import Config

DISCORD_API = "https://discord.com/api"
DISCORD_AUTHORIZE_URL = "https://discord.com/oauth2/authorize"
DISCORD_SCOPES = "identify guilds"

SESSION_COOKIE = "kairo_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 days
STATE_TTL_SECONDS = 10 * 60  # OAuth state must be redeemed quickly

# Discord permissions — required to manage a server from the dashboard.
MANAGE_GUILD_PERMISSION = 1 << 5
ADMINISTRATOR_PERMISSION = 1 << 3


class OAuthError(Exception):
    """Raised when the Discord OAuth exchange fails."""


class OAuthManager:
    """
    Owns CSRF states and user sessions for one API application instance.

    Attached to the aiohttp app as app["oauth"] by create_app().
    """

    def __init__(self, config: "Config", bot: Optional["KairoBot"] = None) -> None:
        self.config = config
        self.bot = bot
        self._states: dict[str, float] = {}  # state token -> created_at
        self._sessions: dict[str, dict] = {}  # session token -> payload

    # ------------------------------------------------------------------ #
    # OAuth start                                                         #
    # ------------------------------------------------------------------ #

    def build_authorize_url(self) -> str:
        """
        Discord authorization URL with a fresh CSRF state token.

        Uses the configured CLIENT_ID and OAUTH_REDIRECT (which defaults to
        DASHBOARD_URL/auth/callback). CLIENT_SECRET is never part of this URL.
        """
        state = secrets.token_urlsafe(24)
        self._states[state] = time.time()

        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.oauth_redirect,
            "scope": DISCORD_SCOPES,
            "state": state,
        }
        return f"{DISCORD_AUTHORIZE_URL}?{urlencode(params)}"

    def consume_state(self, state: str) -> bool:
        """Validate and consume a CSRF state token. Returns True if valid."""
        created = self._states.pop(state, None)
        if created is None:
            return False
        return (time.time() - created) <= STATE_TTL_SECONDS

    # ------------------------------------------------------------------ #
    # Discord API helpers                                                 #
    # ------------------------------------------------------------------ #

    async def exchange_code(self, code: str) -> str:
        """
        Exchange an authorization code for an access token.

        CLIENT_SECRET is sent from the server to Discord here — never from
        the browser. Raises OAuthError on any HTTP or transport failure.
        """
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.config.oauth_redirect,
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{DISCORD_API}/oauth2/token", data=data
                ) as response:
                    body = await response.json(content_type=None)
        except (aiohttp.ClientError, ValueError) as exc:
            raise OAuthError(
                f"Discord token exchange failed: {exc}"
            ) from exc
        if response.status != 200:
            raise OAuthError(
                f"Discord token exchange failed (HTTP {response.status})."
            )
        return body.get("access_token", "")

    async def fetch_identity(self, access_token: str) -> tuple[dict, list]:
        """
        Fetch the authenticated user and their guilds from Discord.

        Returns (user, guilds). Raises OAuthError when Discord rejects the
        token or returns an unexpected payload.
        """
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{DISCORD_API}/users/@me", headers=headers
                ) as response:
                    user = await response.json(content_type=None)
                async with session.get(
                    f"{DISCORD_API}/users/@me/guilds", headers=headers
                ) as response:
                    guilds = await response.json(content_type=None)
        except (aiohttp.ClientError, ValueError) as exc:
            raise OAuthError(f"Discord identity request failed: {exc}") from exc

        if response.status != 200 or not isinstance(user, dict):
            raise OAuthError(
                f"Discord identity request failed (HTTP {response.status})."
            )
        if not isinstance(guilds, list):
            guilds = []  # Discord error payload (dict) — treat as no guilds
        return user, guilds

    # ------------------------------------------------------------------ #
    # Sessions                                                            #
    # ------------------------------------------------------------------ #

    def create_session(self, payload: dict) -> str:
        # Opportunistically prune expired sessions so the in-memory store
        # cannot grow without bound on a long-lived instance.
        if len(self._sessions) >= 1000:
            now = time.time()
            expired = [
                token
                for token, data in self._sessions.items()
                if (now - data["created_at"]) > SESSION_TTL_SECONDS
            ]
            for token in expired:
                self._sessions.pop(token, None)

        token = secrets.token_urlsafe(32)
        payload = dict(payload)
        payload["created_at"] = time.time()
        self._sessions[token] = payload
        return token

    def get_session(self, token: Optional[str]) -> Optional[dict]:
        if not token:
            return None
        payload = self._sessions.get(token)
        if payload is None:
            return None
        if (time.time() - payload["created_at"]) > SESSION_TTL_SECONDS:
            self._sessions.pop(token, None)
            return None
        return payload

    def destroy_session(self, token: Optional[str]) -> None:
        if token:
            self._sessions.pop(token, None)

    def manageable_guilds(self, guilds: list) -> list[dict]:
        """
        Filter Discord guilds to those the user can manage from the dashboard:
          - The user has MANAGE_GUILD on the server.
          - Kairo is installed there (when the bot is connected).

        guilds: raw payload from GET /users/@me/guilds.
        """
        if not isinstance(guilds, list):
            return []

        bot_guild_ids = {str(g.id) for g in self.bot.guilds} if (
            self.bot is not None and self.bot.is_ready()
        ) else None

        manageable = []
        for guild in guilds:
            try:
                permissions = int(guild.get("permissions") or 0)
            except (TypeError, ValueError):
                permissions = 0
            can_manage = bool(
                permissions & MANAGE_GUILD_PERMISSION
                or permissions & ADMINISTRATOR_PERMISSION
            )
            if not can_manage:
                continue
            guild_id = str(guild.get("id", ""))
            bot_installed = (
                bot_guild_ids is None or guild_id in bot_guild_ids
            )
            manageable.append(
                {
                    "id": guild_id,
                    "name": guild.get("name", ""),
                    "icon": guild.get("icon"),
                    "bot_installed": bot_installed,
                }
            )
        return manageable


# ------------------------------------------------------------------ #
# Route handlers                                                       #
# ------------------------------------------------------------------ #

def _oauth(request: web.Request) -> OAuthManager:
    return request.app["oauth"]


async def auth_discord(request: web.Request) -> web.Response:
    """GET /auth/discord — start the Discord OAuth flow."""
    authorize_url = _oauth(request).build_authorize_url()
    raise web.HTTPFound(location=authorize_url)


async def auth_callback(request: web.Request) -> web.Response:
    """
    GET /auth/callback — exchange the Discord authorization code.

    Discord redirects here (DASHBOARD_URL/auth/callback). On success a
    kairo_session cookie is set and the browser is sent back to the
    dashboard landing page.
    """
    manager = _oauth(request)
    dashboard_url = manager.config.dashboard_url

    query = request.query
    if query.get("error"):
        raise web.HTTPFound(location=f"{dashboard_url}/?auth=error")

    code = query.get("code", "")
    state = query.get("state", "")
    if not code or not manager.consume_state(state):
        raise web.HTTPFound(location=f"{dashboard_url}/?auth=error")

    try:
        access_token = await manager.exchange_code(code)
        user, guilds = await manager.fetch_identity(access_token)
    except (OAuthError, aiohttp.ClientError):
        # Includes transport failures (network down, Discord timeout) —
        # surface them as a failed login rather than a 500.
        raise web.HTTPFound(location=f"{dashboard_url}/?auth=error")

    if not user or user.get("id") is None:
        raise web.HTTPFound(location=f"{dashboard_url}/?auth=error")

    session_token = manager.create_session(
        {
            "user": {
                "id": str(user.get("id", "")),
                "username": user.get("username", ""),
                "discriminator": user.get("discriminator"),
                "avatar": user.get("avatar"),
            },
            "guilds": manager.manageable_guilds(guilds or []),
        }
    )

    response = web.HTTPFound(location=f"{dashboard_url}/?auth=success")
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="Lax",
        # Only send the session cookie over HTTPS when the dashboard is
        # served over HTTPS; plain http://localhost stays cookie-friendly.
        secure=manager.config.dashboard_url.startswith("https"),
        path="/",
    )
    raise response


async def auth_logout(request: web.Request) -> web.Response:
    """GET /auth/logout — invalidate the session and return to the dashboard."""
    manager = _oauth(request)
    manager.destroy_session(request.cookies.get(SESSION_COOKIE))
    response = web.HTTPFound(location=manager.config.dashboard_url)
    response.del_cookie(SESSION_COOKIE, path="/")
    raise response


async def api_me(request: web.Request) -> web.Response:
    """
    GET /api/v1/me — current session (user + manageable guilds).

    Authenticated by the kairo_session cookie rather than X-API-Key; returns
    401 when there is no valid session.
    """
    manager = _oauth(request)
    session = manager.get_session(request.cookies.get(SESSION_COOKIE))
    if session is None:
        return web.json_response({"error": "Not authenticated."}, status=401)
    payload = {
        "user": session["user"],
        "guilds": session["guilds"],
    }
    return web.json_response(payload)


# ------------------------------------------------------------------ #
# Registration                                                        #
# ------------------------------------------------------------------ #

def register_routes(app: web.Application) -> None:
    """Attach OAuth/session routes to the aiohttp application."""
    app.router.add_get("/auth/discord", auth_discord)
    app.router.add_get("/auth/callback", auth_callback)
    app.router.add_get("/auth/logout", auth_logout)
    app.router.add_get("/api/v1/me", api_me)
