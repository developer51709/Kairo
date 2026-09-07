# Dashboard

> ✅ The dashboard scaffold and landing page are built (Phase 6). This document
describes the design, the authentication flow, and the planned pages.

The Kairo web dashboard is a Vite-powered single-page application that provides
a graphical interface for managing servers and configuring Kairo.

---

## Technology Stack

| Technology          | Purpose                            |
|---------------------|------------------------------------|
| **Vite**            | Build tool and development server  |
| **TypeScript**      | Type-safe frontend code            |
| **Discord OAuth2**  | User authentication                |
| **REST API**        | Communication with the bot         |

---

## Architecture

The dashboard communicates **only through the REST API** — it never accesses
the database directly. The API mediates all data access and enforces permissions.

```
Browser → HTTPS → Reverse proxy → Kairo API → KairoBot → Database
```

---

## Authentication Flow

The OAuth2 handshake is handled **entirely by the API** (`src/api/oauth.py`)
using the root `.env` `CLIENT_ID`/`CLIENT_SECRET` — the secret never reaches
the browser. The dashboard simply points its "Login with Discord" button at
`/auth/discord`.

1. User clicks "Login with Discord" — the browser follows `/auth/discord`.
2. The API redirects to Discord's OAuth2 authorization URL (with a CSRF state).
3. User approves the request.
4. Discord redirects to `OAUTH_REDIRECT` (`DASHBOARD_URL/auth/callback`) with an authorization code.
5. The API exchanges the code for a Discord access token (**server-side**).
6. The API fetches the user's guilds from Discord.
7. The API keeps only guilds the user can manage:
   a. `MANAGE_GUILD` (or `ADMINISTRATOR`) permission in the guild.
   b. `bot_installed` is flagged when Kairo is in the guild.
8. The API sets an HttpOnly `kairo_session` cookie and redirects back to the dashboard,
   which loads `/api/v1/me` to show the signed-in user.

Register `DASHBOARD_URL/auth/callback` as an OAuth2 redirect URI on Discord
(Developer Portal → OAuth2 → Redirects) and grant the `identify` + `guilds` scopes.

---

## Planned Pages

### Login
- Discord OAuth2 login button
- Redirect to guild selector after authentication

### Guild Selector
- List of guilds the user manages where Kairo is installed
- "Invite Kairo" links for guilds where it's not installed

### Dashboard Home
- Bot status overview (uptime, latency, guild count)
- Recent moderation activity
- Quick access to configuration

### Moderation
- Recent moderation cases (paginated)
- Case details
- User lookup with warn/case history

### AutoMod Configuration
- Toggle individual rules
- Configure per-rule settings (thresholds, actions)
- Per-channel and per-role exemptions

### Logging Configuration
- Enable/disable event categories
- Set log channels per category

### Server Configuration
- Mod log channel
- Mod role
- Auto-role
- Locale

### Audit Log
- Full server event history

---

## Development

```bash
cd src/dashboard

# Install dependencies
bun install        # or: npm install

# Start dev server (with Vite HMR)
bun run dev

# Build for production
bun run build

# Preview production build
bun run preview
```

The dev server proxies `/api/*`, `/auth/*`, and `/health` to the Kairo API.
By default that is `http://127.0.0.1:8080`; when started via `python src/run.py`
the configured `API_HOST`/`API_PORT` from the root `.env` are passed through
so a custom API port works automatically.

---

## Security Notes

- The dashboard validates guild permissions on every page load — not just at login.
- The API key (`API_SECRET`) is never exposed to the browser.
- Discord access tokens are stored server-side in sessions (not in localStorage).
- `CLIENT_SECRET` lives only in the API process; the browser never sees it.
- The `kairo_session` cookie is HttpOnly and gets the `Secure` flag when the
dashboard is served over HTTPS.
