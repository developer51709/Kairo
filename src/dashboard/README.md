# Kairo Dashboard

> The web command center for Kairo — manage Discord servers, review
> moderation, and configure every module from the browser.

Scaffolded as a **Vite + React + TypeScript** single-page app (Tailwind CSS v4
for styling). The dashboard talks **only to the Kairo REST API** — it never
touches the SQLite database directly.

---

## Status

Phase 6 (Dashboard) of the project roadmap has begun:

- ✅ Vite application scaffold (React + TypeScript + Tailwind v4)
- ✅ Landing page — dark "ink & gold" theme, product preview, Discord login CTA
- ✅ Discord OAuth flow, server-side on the API (`/auth/*` + `/api/v1/me`)
- 📋 Guild selector, server overview, per-module configuration pages

The landing page is fully functional as a marketing/entry screen, and "Login
with Discord" starts the real OAuth flow: the API handles `/auth/discord` →
`/auth/callback` using the root `.env` `CLIENT_ID`/`CLIENT_SECRET` and issues
an HttpOnly `kairo_session` cookie. No secret ever reaches the browser.

---

## Getting started

```bash
# From this directory (src/dashboard)
bun install        # or: npm install
bun run dev        # http://localhost:5173 (proxies /api, /auth & /health to the Kairo API)
```

The Vite dev server proxies `/api/*`, `/auth/*` and `/health` to the Kairo
API (`python src/run.py`, default `http://127.0.0.1:8080`) so the browser
only ever talks to the dashboard origin.

### Scripts

| Script              | Purpose                                   |
|---------------------|-------------------------------------------|
| `bun run dev`       | Dev server with HMR + API proxy           |
| `bun run typecheck` | `tsc -b` project-wide type check          |
| `bun run build`     | Type check + production build to `dist/`  |
| `bun run preview`   | Serve the production build                |

### Ports & previews

- The dev server binds `0.0.0.0` and listens on **5173** by default.
- Setting the **`PORT`** environment variable overrides that (managed
  previews and isolated workspaces inject it). When `PORT` is set the server
  fails fast if the port is taken instead of silently moving elsewhere.
- `python src/run.py` starts the dashboard **before** the API so port probes
  find the web UI (5173/`PORT`) rather than the API (8080). The API port is
  only for bot↔dashboard traffic — it is not the web preview.

---

## Configuration

The dashboard itself needs **no environment variables**. Authentication uses
the credentials that already exist in the root `.env`:

| Variable       | Where it is used                                                       |
|----------------|------------------------------------------------------------------------|
| `CLIENT_ID`    | The API builds the Discord authorization URL with it (`/auth/discord`) |
| `CLIENT_SECRET`| The API exchanges the code for a token (`/auth/callback`)              |

Both stay inside the API process — `CLIENT_SECRET` must never reach the
browser, so it is never bundled into the frontend.

To enable login:

1. Make sure `CLIENT_ID` and `CLIENT_SECRET` are set in the root `.env`.
2. In the [Discord Developer Portal](https://discord.com/developers/applications)
   → OAuth2 → Redirects, register `http://localhost:5173/auth/callback`
   (or `DASHBOARD_URL/auth/callback` once deployed) and grant the
   `identify` + `guilds` scopes.
3. Run `python src/run.py` — bot, API, and dashboard all start; the login
   button opens the API's `/auth/discord` flow.

---

## Auth flow (handled by the API)

| Route            | Purpose                                                       |
|------------------|---------------------------------------------------------------|
| `/`              | Landing page: branding, feature overview, Login CTA           |
| `/auth/discord`  | API — 302 to Discord's consent screen                         |
| `/auth/callback` | API — exchanges the code, sets the `kairo_session` cookie     |
| `/auth/logout`   | API — clears the session cookie                               |
| `/api/v1/me`     | API — current user + manageable guilds (session cookie)       |

---

## Structure

```
src/dashboard/
├── index.html
├── vite.config.ts          # React + Tailwind plugins, :8080 API proxy
├── public/favicon.svg
└── src/
    ├── main.tsx            # entry
    ├── App.tsx             # routes
    ├── index.css           # Tailwind v4 + Kairo theme tokens ("ink & gold")
    ├── lib/auth.ts         # auth paths served by the API (/auth/*)
    ├── components/
    │   ├── icons.tsx       # inline SVG icon set
    │   ├── logo.tsx        # Kairo mark + wordmark
    │   └── login-discord.tsx
    └── pages/
        └── Landing.tsx
```

## Next steps (dashboard roadmap)

- Guild selector UI backed by `/api/v1/me` (with permission validation per
  `docs/dashboard.md`).
- Server overview + configuration pages for moderation, AutoMod, logging,
  roles/welcome, and community tools.
- Responsive mobile layout pass and light theme if ever desired.

See `docs/dashboard.md` (root docs) for the full design specification.
