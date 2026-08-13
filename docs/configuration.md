# Configuration Reference

Kairo is configured entirely through environment variables. In development,
these are typically loaded from a `.env` file in the project root. In
production, set them directly in your process environment or service manager.

Copy `.env.example` to `.env` and fill in the required values before starting.

---

## Required Variables

These must be set for Kairo to start. If any are missing, startup will fail
immediately with a clear error message.

| Variable        | Description                                                |
|-----------------|------------------------------------------------------------|
| `BOT_TOKEN`     | Your Discord bot's secret token. Never share this.         |
| `CLIENT_ID`     | Your Discord application's Client ID.                      |
| `CLIENT_SECRET` | Your Discord application's OAuth2 Client Secret.           |

---

## Discord

| Variable      | Default | Description                                                      |
|---------------|---------|------------------------------------------------------------------|
| `BOT_PREFIX`  | `!`     | Prefix for legacy text commands. Most commands are slash commands. |
| `DEV_GUILD_ID`| (empty) | Guild ID for instant slash command sync during development.      |

### DEV_GUILD_ID

When set, slash commands are synced **only to this guild** (takes effect instantly).
Leave empty for global sync (changes take up to 1 hour to propagate on Discord's servers).

Use `DEV_GUILD_ID` during development; leave it empty for production deployments.

---

## Database

| Variable  | Default         | Description                                      |
|-----------|-----------------|--------------------------------------------------|
| `DB_PATH` | `data/kairo.db` | Path to the SQLite database file.                |

The parent directory is created automatically at startup if it does not exist.

For production, consider placing the database in a backed-up location:
```
DB_PATH=/var/lib/kairo/kairo.db
```

---

## Logging

| Variable    | Default | Description                                              |
|-------------|---------|----------------------------------------------------------|
| `LOG_LEVEL` | `INFO`  | Minimum log level. Options: DEBUG, INFO, WARNING, ERROR. |

Logging levels:

| Level     | When to use                                            |
|-----------|--------------------------------------------------------|
| `DEBUG`   | Development — shows every event, database query, etc. |
| `INFO`    | Production — normal operational messages.              |
| `WARNING` | Only unexpected but non-fatal situations.              |
| `ERROR`   | Only errors.                                           |

---

## API Server

The API server allows the web dashboard to communicate with the bot. It is
optional unless you are running the dashboard.

| Variable     | Default       | Description                                           |
|--------------|---------------|-------------------------------------------------------|
| `API_HOST`   | `127.0.0.1`   | Host to bind the API server to.                       |
| `API_PORT`   | `8080`        | Port the API server listens on.                       |
| `API_SECRET` | (empty)       | Shared secret for API authentication. See below.      |

### API_HOST

Use `127.0.0.1` (localhost) if you are using a reverse proxy (Nginx, Caddy)
or a tunnel (Cloudflare, ngrok) to expose the API. This prevents direct
external access to the API port.

Use `0.0.0.0` only if you need direct external access (not recommended).

### API_SECRET

A long, random string used to authenticate dashboard requests to the API.
Generate one with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

The dashboard includes this in the `X-API-Key` request header. If not set,
the API will reject all non-health-check requests with HTTP 503.

---

## Dashboard / OAuth2

| Variable        | Default                        | Description                                     |
|-----------------|--------------------------------|-------------------------------------------------|
| `DASHBOARD_URL` | `http://localhost:5173`        | Public base URL of the web dashboard.           |
| `OAUTH_REDIRECT`| `<DASHBOARD_URL>/auth/callback`| Full OAuth2 redirect URI registered on Discord. |

### OAUTH_REDIRECT

If you do not set `OAUTH_REDIRECT` explicitly, Kairo constructs it as
`{DASHBOARD_URL}/auth/callback`.

The redirect URI must **exactly match** one of the URIs registered in your
Discord application's OAuth2 settings (Discord Developer Portal → OAuth2 → Redirects).

---

## Runtime

| Variable | Default | Description                                                       |
|----------|---------|-------------------------------------------------------------------|
| `DEBUG`  | `false` | Enables debug mode (verbose logging, dev guild sync).             |

### DEBUG

In debug mode:
- `LOG_LEVEL` is overridden to `DEBUG`.
- discord.py's own logger is set to `DEBUG`.
- Slash commands are synced to `DEV_GUILD_ID` on every startup.

Always set `DEBUG=false` in production.

---

## Complete Example

```env
# .env — Kairo Configuration

BOT_TOKEN=your_bot_token_here
CLIENT_ID=123456789012345678
CLIENT_SECRET=your_client_secret_here
BOT_PREFIX=!
DEV_GUILD_ID=987654321098765432

DB_PATH=data/kairo.db

LOG_LEVEL=INFO

API_HOST=127.0.0.1
API_PORT=8080
API_SECRET=a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6

DASHBOARD_URL=https://kairo.example.com

DEBUG=false
```
