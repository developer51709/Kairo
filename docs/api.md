# API Reference

The Kairo REST API is an optional HTTP server that allows the web dashboard
to communicate with the running bot. It runs in the same process as the bot.

> **Status: Phase 1 scaffold**
> Only `/health` and `/api/v1/status` are implemented. Full endpoint
> documentation will be added in Phase 4.

---

## Starting the API

```bash
python src/run.py --with-api
```

The API server starts at `http://<API_HOST>:<API_PORT>` (default: `http://127.0.0.1:8080`).

---

## Authentication

All endpoints except `/health` require the `X-API-Key` header:

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
