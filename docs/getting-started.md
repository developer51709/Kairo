# Getting Started

This guide walks you through installing and running Kairo for the first time.

---

## Prerequisites

- **Python 3.11 or higher** — [python.org](https://python.org)
- **Git** — to clone the repository
- **A Discord application** — [discord.com/developers/applications](https://discord.com/developers/applications)

---

## 1. Clone the Repository

```bash
git clone https://github.com/your-org/kairo.git
cd kairo
```

---

## 2. Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click **New Application** and give it a name (e.g. "Kairo").
3. Go to the **Bot** tab and click **Add Bot**.
4. Under **Privileged Gateway Intents**, enable:
   - **Server Members Intent**
   - **Message Content Intent**
5. Copy your **Bot Token** — you will need it in the next step.
6. Go to **General Information** and copy the **Application ID** (Client ID) and **Client Secret**.
7. Go to **OAuth2 → Redirects** and register the dashboard's OAuth callback:
   `http://localhost:5173/auth/callback` (or `DASHBOARD_URL/auth/callback`
   once deployed — it must match exactly). Grant the `identify` and `guilds`
   scopes for the dashboard login.

> ⚠️ Keep your bot token secret. Never share it or commit it to a repository.

---

## 3. Configure Kairo

**Option A — Interactive wizard (recommended):**

```bash
python src/setup.py
```

The wizard will ask for your bot token, client ID, and client secret, then
write a `.env` file for you.

**Option B — Manual configuration:**

```bash
cp .env.example .env
```

Open `.env` in a text editor and fill in the required values:

```
BOT_TOKEN=your_bot_token_here
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
```

See [configuration.md](configuration.md) for all available options.

---

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

Or if you used the setup wizard and chose to install dependencies, skip this step.

To run the **web dashboard** too, install its dependencies as well (requires Node.js):

```bash
cd src/dashboard
bun install      # or: npm install
cd ../..
```

---

## 5. Invite Kairo to a Server

Generate an invite URL by replacing `YOUR_CLIENT_ID` with your application's Client ID:

```
https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot+applications.commands
```

Open the URL in a browser and select the server to invite Kairo to.

> The permissions value `8` requests Administrator — adjust for your needs in production.

---

## 6. Run Kairo

One command starts **all three components** — the Discord bot, the REST API,
and the web dashboard (Vite dev server):

```bash
python src/run.py
```

You should see output like:

```
[2026-01-01 12:00:00] [INFO    ] kairo.core.bot: KairoBot initialised.
[2026-01-01 12:00:00] [INFO    ] kairo.core.bot: Starting Kairo...
[2026-01-01 12:00:00] [INFO    ] kairo.core.bot: Kairo is ready! Logged in as Kairo#1234 (ID: 123456789). Serving 1 guild(s).
```

- The API listens on `http://127.0.0.1:8080` by default.
- The dashboard is served at `http://localhost:5173` (set `DASHBOARD_URL` in `.env` to override).
- Press **Ctrl-C** to stop everything cleanly.

> If the dashboard is skipped with a warning, install its dependencies first
> (step 4) or pass `--no-dashboard` to run without it.

---

## 7. (Optional) Choose Which Components Run

By default every component starts. Disable individual ones with `--no-*`, or
run exactly one with `--only`:

```bash
python src/run.py --no-dashboard   # bot + API only (headless server)
python src/run.py --no-api         # bot + dashboard, no API
python src/run.py --only bot       # bot only
python src/run.py --only api       # API only
python src/run.py --only dashboard # dashboard only
```

---

## Development Mode

For development, enable debug mode to get verbose logging and instant slash command sync:

1. Add your development server's ID to `.env`:
   ```
   DEV_GUILD_ID=your_guild_id
   DEBUG=true
   ```

2. Run:
   ```bash
   python src/run.py --debug
   ```

---

## Troubleshooting

**"Missing required environment variables"**
→ Ensure `.env` exists and contains `BOT_TOKEN`, `CLIENT_ID`, and `CLIENT_SECRET`.

**"Invalid Token" on startup**
→ Your `BOT_TOKEN` is incorrect. Regenerate it in the Discord Developer Portal.

**Slash commands not appearing**
→ In development, set `DEV_GUILD_ID` for instant sync. Global sync takes up to 1 hour.

**Privilege Intent errors**
→ Enable Server Members Intent and Message Content Intent in the Discord Developer Portal (Bot tab).

---

## Next Steps

- Read [configuration.md](configuration.md) to understand all available settings.
- Read [architecture.md](architecture.md) to understand how Kairo is structured.
- Read [features.md](features.md) to learn how to add new features.
