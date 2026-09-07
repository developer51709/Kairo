# API Reference

The Kairo REST API is an optional HTTP server that allows the web dashboard
to communicate with the running bot. It runs in the same process as the bot.

> **Status: Phase 1 scaffold + OAuth2**
> `/health`, `/api/v1/status`, the Discord OAuth2 flow (`/auth/*`), and
> `/api/v1/me` are implemented. Guild/config/moderation endpoints land in Phase 4.

---

## Starting the API

The API is part of Kairo's default startup, so a plain `python src/run.py`
already starts it (alongside the bot and the dashboard). To run it on its
own, or without the web dashboard:

```bash
python src/run.py --only api         # API only
python src/run.py --no-dashboard    # bot + API
```

The API server starts at `http://<API_HOST>:<API_PORT>` (default: `http://127.0.0.1:8080`).

---

## Authentication

All endpoints except the following public routes require the `X-API-Key` header:

| Public route     | Why                                                        |
|------------------|-------------------------------------------------------------|
| `GET /health`    | Health check                                               |
| `GET /auth/*`    | Discord OAuth2 flow (start / callback / logout)            |
| `GET /api/v1/me` | Authenticated via the `kairo_session` cookie instead       |

```
X-API-Key: your_api_secret_here
```

The secret must match the `API_SECRET` environment variable.

If `API_SECRET` is not configured, all protected endpoints return HTTP 503.

---

## Endpoints

### `GET /health`

Public health check. No authentication required.

**Response:**
```json
{
  "status": "ok",
  "bot_ready": true
}
```

| Field       | Type    | Description                              |
|-------------|---------|------------------------------------------|
| `status`    | string  | Always `"ok"` if the server is running.  |
| `bot_ready` | boolean | Whether the Discord bot is connected.    |

---

### `GET /api/v1/status`

Bot operational status.

**Headers:** `X-API-Key: <secret>`

**Response:**
```json
{
  "guild_count": 42,
  "latency_ms": 45,
  "user": {
    "id": "123456789012345678",
    "name": "Kairo#1234"
  }
}
```

---

### Discord OAuth2 & sessions

The dashboard login flow is handled entirely server-side using the root
`.env` `CLIENT_ID` and `CLIENT_SECRET` — neither is ever exposed to the
browser. Implementation: `src/api/oauth.py`.

| Method | Path              | Description                                                            |
|--------|-------------------|------------------------------------------------------------------------|
| GET    | `/auth/discord`   | 302 to Discord's consent screen (state = CSRF token)                  |
| GET    | `/auth/callback`  | Exchange `?code=` for a token, set `kairo_session` cookie, redirect to dashboard |
| GET    | `/auth/logout`    | Clear the session cookie and redirect to the dashboard                |
| GET    | `/api/v1/me`      | Current session: user + guilds the user can manage (with `bot_installed`) |

`/auth/callback` must be registered as an OAuth2 redirect URI on Discord —
by default that is `DASHBOARD_URL/auth/callback`. Sessions are stored in
memory (single self-hosted instance); persisting them is future work.

---

## Planned Endpoints (Phase 4)

### Guilds

| Method | Path                              | Description                      |
|--------|-----------------------------------|----------------------------------|
| GET    | `/api/v1/guilds`                  | List guilds where bot is active  |
| GET    | `/api/v1/guilds/{guild_id}`       | Get guild configuration          |
| PATCH  | `/api/v1/guilds/{guild_id}`       | Update guild configuration       |

### Moderation

| Method | Path                                              | Description                        |
|--------|---------------------------------------------------|------------------------------------|
| GET    | `/api/v1/guilds/{guild_id}/cases`                 | List recent moderation cases       |
| GET    | `/api/v1/guilds/{guild_id}/cases/{case_id}`       | Get a specific case                |
| PATCH  | `/api/v1/guilds/{guild_id}/cases/{case_id}`       | Update a case (add note, resolve)  |
| GET    | `/api/v1/guilds/{guild_id}/users/{user_id}/warnings` | Get warnings for a user         |

### Configuration

| Method | Path                                                | Description                |
|--------|-----------------------------------------------------|----------------------------|
| GET    | `/api/v1/guilds/{guild_id}/config/moderation`       | Get moderation config      |
| PATCH  | `/api/v1/guilds/{guild_id}/config/moderation`       | Update moderation config   |
| GET    | `/api/v1/guilds/{guild_id}/config/automod`          | Get automod config         |
| PATCH  | `/api/v1/guilds/{guild_id}/config/automod`          | Update automod config      |
| GET    | `/api/v1/guilds/{guild_id}/config/logging`          | Get logging config         |
| PATCH  | `/api/v1/guilds/{guild_id}/config/logging`          | Update logging config      |

---

## Error Responses

All error responses follow this format:

```json
{
  "error": "Human-readable error message.",
  "detail": "Optional additional detail."
}
```

| HTTP Status | Meaning                                        |
|-------------|------------------------------------------------|
| 401         | Missing or invalid `X-API-Key` header.         |
| 404         | Resource not found.                            |
| 500         | Unhandled server error.                        |
| 503         | API not properly configured (no `API_SECRET`). |

---

## Adding Endpoints

To add a new endpoint in `src/api/app.py`:

```python
async def my_endpoint(request: web.Request) -> web.Response:
    bot: KairoBot = request.app["bot"]
    # ... handler logic ...
    return web.json_response({"result": "value"})

# Register in create_app():
app.router.add_get("/api/v1/my-endpoint", my_endpoint)
```

For complex endpoints, create separate route handler modules:

```
src/api/
├── __init__.py
├── app.py          ← Application factory + middleware
└── routes/
    ├── guilds.py   ← Guild endpoints
    ├── moderation.py
    └── config.py
```
