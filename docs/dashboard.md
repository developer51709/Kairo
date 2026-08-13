# Dashboard

> 🚧 The dashboard is planned for **Phase 4**. This document describes the design.

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

1. User clicks "Login with Discord".
2. Browser redirects to Discord's OAuth2 authorization URL.
3. User approves the request.
4. Discord redirects to `OAUTH_REDIRECT` with an authorization code.
5. The dashboard exchanges the code for a Discord access token.
6. The dashboard fetches the user's guilds from Discord.
7. For each guild, the dashboard checks:
   a. Is the bot installed in this guild?
   b. Does the user have `MANAGE_GUILD` permission in this guild?
8. Only guilds passing both checks are shown in the guild selector.

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

Once scaffolded in Phase 4:

```bash
cd src/dashboard

# Install dependencies
npm install

# Start dev server (with Vite HMR)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The dev server proxies API requests to `http://127.0.0.1:8080`.

---

## Security Notes

- The dashboard validates guild permissions on every page load — not just at login.
- The API key (`API_SECRET`) is never exposed to the browser.
- Discord access tokens are stored server-side in sessions (not in localStorage).
- All API requests from the dashboard are server-side (next.js-style SSR or BFF pattern).
