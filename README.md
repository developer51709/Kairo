![Banner Image](banner.jpeg)

# Kairo

> A modern, self-hostable Discord platform built for customization, automation, and beautiful interactive experiences.

**Kairo** is a feature-rich, open-source Discord bot and server management platform built with **Python**, **discord.py 2.7.1**, **Discord Components V2**, **SQLite**, and a modern **Vite-powered web dashboard**.

The goal of Kairo is to provide a complete, self-hostable alternative to traditional Discord bots — combining powerful server features, a modern web interface, persistent configuration, extensibility, and an exceptionally well-documented developer experience.

> 🚧 **Kairo is currently under active development.**
>
> Many features described below are planned and may not be implemented yet. This README serves as the project's initial vision and roadmap.

---

## ✨ Why Kairo?

Most Discord bots are designed around commands and traditional Discord embeds.

Kairo takes a different approach.

The project is being designed from the ground up around **Discord Components V2**, allowing Kairo to provide rich, interactive interfaces directly inside Discord while also providing a full web dashboard for configuration and management.

Kairo aims to be:

* 🧩 **Modular** — features are independently organized and auto-discovered
* 🎨 **Modern** — Components V2-first Discord interfaces
* 🌐 **Self-hostable** — run Kairo on your own hardware or server
* 💾 **Persistent** — configuration stored reliably in SQLite
* 🔐 **Secure** — proper Discord OAuth2 and permission validation
* 📊 **Manageable** — powerful web dashboard
* 📚 **Well documented** — extensive documentation for users and developers
* 🚀 **Easy to deploy** — local, Docker, VPS, and tunnel-based deployment
* 🛠️ **Developer friendly** — clean architecture and clear extension points
* 🎭 **Customizable** — application emojis, custom branding, per-server configuration
* 🤝 **Onboarding-ready** — interactive guild setup wizard on first install

---

## 🚀 Planned Features

### 🤖 Discord Bot

#### Moderation

* [x] Ban
* [x] Kick
* [x] Timeout
* [x] Warn system
* [x] Warning history
* [x] Moderation cases
* [x] Case management
* [ ] Bulk message deletion
* [ ] Moderation logs
* [ ] Configurable punishment actions
* [x] Moderator permission checks
* [ ] Moderation audit history
* [ ] Temporary bans (auto-unban)
* [ ] Slow mode management
* [ ] Note system (staff-only case notes)
* [ ] Appeal system

#### AutoMod

* [ ] Spam protection
* [ ] Mention spam protection
* [ ] Duplicate message detection
* [ ] Invite filtering
* [ ] Link filtering
* [ ] Word filtering
* [ ] Caps filtering
* [ ] Raid protection
* [ ] Configurable actions (warn / timeout / kick / ban)
* [ ] AutoMod logging
* [ ] Per-channel configuration
* [ ] Per-role exemptions
* [ ] Regex rule support
* [ ] Mass join detection
* [ ] Phishing link detection
* [ ] New account age filtering

#### Server Management

* [ ] Welcome messages (Components V2, configurable)
* [ ] Leave messages
* [ ] Auto roles on join
* [ ] Auto roles on verify
* [ ] Verification system (button, CAPTCHA, rules accept)
* [ ] Reaction roles
* [ ] Button roles
* [ ] Select menu roles
* [ ] Role menus (grouped role pickers)
* [ ] Server configuration panel
* [ ] Custom commands
* [ ] Custom command variables (user, server, time)
* [ ] Channel management utilities
* [ ] Role management utilities
* [ ] Server information

#### Onboarding

* [ ] Interactive guild setup wizard (Components V2 multi-step)
* [ ] First-run detection on guild join
* [ ] Setup progress tracking
* [ ] Channel creation assistant
* [ ] Role creation assistant
* [ ] Feature enable/disable during setup
* [ ] Setup summary and confirmation panel
* [ ] Re-run setup at any time via `/setup`
* [ ] Skip and configure later for any step

#### Community

* [ ] Tickets (thread-based, button to open)
* [ ] Ticket transcripts
* [ ] Ticket categories and routing
* [ ] Suggestions (vote panel, status updates)
* [ ] Giveaways (enter/leave, re-roll, winners)
* [ ] Polls (multi-choice, timed, results panel)
* [ ] Starboard
* [ ] Leveling (XP, rank card, leaderboard)
* [ ] Level roles
* [ ] Reminders (personal, channel)
* [ ] Custom responses (trigger → reply)
* [ ] Community statistics dashboard
* [ ] Server milestones
* [ ] Reaction menus

#### Utility

* [x] Help command (Components V2, category filter)
* [x] User information
* [x] Server information
* [x] Avatar viewer
* [x] Bot information
* [x] Ping / latency
* [ ] Role information
* [ ] Channel information
* [ ] Permissions viewer
* [ ] Server statistics
* [ ] Embed builder
* [ ] Message utilities
* [ ] Snowflake decoder
* [ ] Colour preview
* [ ] Timestamp generator
* [ ] User banner viewer

#### Logging

* [ ] Message edit logs
* [ ] Message delete logs
* [ ] Member join / leave logs
* [ ] Member ban / unban logs
* [ ] Member role change logs
* [ ] Channel create / edit / delete logs
* [ ] Role create / edit / delete logs
* [ ] Voice channel join / leave / move logs
* [ ] Invite create / delete logs
* [ ] Server update logs
* [ ] Per-event channel routing
* [ ] Log ignore rules (channels, roles, users)
* [ ] Log formatting templates

#### Fun

* [ ] 8-ball
* [ ] Coinflip
* [ ] Dice roller
* [ ] Random quote
* [ ] Would you rather
* [ ] Trivia
* [ ] Mini-games

---

# 🎨 Customization

Kairo is designed to be deeply customizable per server.

### Application Emojis

* [ ] Application emoji registry — Kairo registers its own emoji set with Discord on startup
* [ ] Auto-registration of missing emojis at boot
* [ ] Emoji fallback to Unicode when application emojis are unavailable
* [ ] Per-guild custom emoji overrides
* [ ] Emoji configuration via dashboard

### Branding

* [ ] Custom bot name per guild (nickname)
* [ ] Custom embed accent colour per guild
* [ ] Custom footer text
* [ ] Custom status messages (rotating or static)
* [ ] Custom command prefix per guild

### Per-Server Configuration

* [ ] Feature enable/disable per guild
* [ ] Language / locale selection
* [ ] Timezone setting (for timed features)
* [ ] Command cooldowns per guild
* [ ] Per-channel command restrictions
* [ ] Per-role command restrictions

---

# 🧱 Discord Components V2

Components V2 is a core part of Kairo's Discord interface layer.

Kairo uses **discord.py's native CV2 system** (`discord.ui.LayoutView`) directly rather than building a custom abstraction on top of it. All interactive and layout components are provided by discord.py 2.6+ out of the box.

Implemented components:

* [x] Containers (`discord.ui.Container`)
* [x] Sections (`discord.ui.Section`)
* [x] Text displays (`discord.ui.TextDisplay`)
* [x] Separators (`discord.ui.Separator`)
* [x] Buttons (`discord.ui.Button`)
* [x] Select menus (`discord.ui.Select` and variants)
* [x] Action rows (`discord.ui.ActionRow`)
* [x] Thumbnails (`discord.ui.Thumbnail`)
* [x] Modals (`discord.ui.Modal`)
* [x] Pagination (`Paginator` — Kairo helper built on `LayoutView`)
* [ ] Media galleries
* [ ] Confirmation dialogs
* [ ] Interactive configuration panels
* [ ] Stateful multi-step flows

Views are sent via `view=` to `interaction.response.send_message()`, which is the correct discord.py CV2 API. The `src/bot/components/` package re-exports all discord.ui CV2 types and provides thin send helpers (`send_layout`, `edit_layout`, `followup_layout`, `send_layout_to_channel`).

Example:

```python
import discord
from src.bot.components import send_layout

view = discord.ui.LayoutView()
view.add_item(discord.ui.Container(
    discord.ui.TextDisplay("# Server Configuration"),
    discord.ui.Separator(visible=True),
    discord.ui.TextDisplay("Manage your server settings below."),
    discord.ui.ActionRow(
        discord.ui.Button(label="Moderation", custom_id="config:moderation"),
        discord.ui.Button(label="Logging", custom_id="config:logging"),
    ),
))
await send_layout(interaction, view, ephemeral=True)
```

---

# 🌐 Web Dashboard

Kairo will include a complete web dashboard built using **Vite**.

The dashboard will provide a centralized interface for managing Kairo installations and Discord servers.

### Planned Dashboard Features

* [ ] Discord OAuth2 login
* [ ] Discord account information
* [ ] Guild selector
* [ ] Guild permission validation
* [ ] Bot installation flow
* [ ] Interactive onboarding wizard
* [ ] Server overview (member count, activity, health)
* [ ] Server configuration
* [ ] Moderation configuration
* [ ] AutoMod configuration
* [ ] Logging configuration
* [ ] Welcome / leave configuration
* [ ] Ticket configuration
* [ ] Giveaway management
* [ ] Reaction / button roles editor
* [ ] Role menu builder
* [ ] Custom commands editor
* [ ] Custom responses editor
* [ ] Leveling configuration
* [ ] Application emoji management
* [ ] Branding configuration
* [ ] Audit logs viewer
* [ ] Moderation case browser
* [ ] Bot status
* [ ] System status
* [ ] Database status
* [ ] Responsive mobile interface
* [ ] Dark theme

The dashboard will communicate with the bot through a dedicated API rather than directly manipulating the database.

---

# 🔐 Discord OAuth2

Kairo's dashboard will support proper Discord OAuth2 authentication.

Planned functionality includes:

* [ ] OAuth2 authorization
* [ ] Secure callback handling
* [ ] Session management
* [ ] User authentication
* [ ] Guild membership verification
* [ ] Guild permission verification
* [ ] Bot presence verification
* [ ] Secure API authorization
* [ ] Logout / session invalidation

Kairo will never assume that a user has permission to manage a server simply because they can authenticate with Discord.

---

# 💾 Persistent Storage

Kairo will use **SQLite** as its default persistent database.

The database layer will be designed around repositories and services rather than allowing individual features to freely execute SQL.

Planned capabilities include:

* [ ] Guild configuration
* [ ] User profiles
* [ ] Moderation cases
* [ ] Warnings
* [ ] AutoMod configuration
* [ ] Ticket data and transcripts
* [ ] Giveaway data
* [ ] Logging configuration
* [ ] Leveling / XP data
* [ ] Custom commands
* [ ] Custom responses
* [ ] Application emoji registry
* [ ] Onboarding state
* [ ] Migration system
* [ ] Database backups
* [ ] Database health checks

The architecture will also aim to make migration to another database backend easier for larger deployments in the future.

---

# 🧩 Modular Architecture

Kairo is designed as a modular platform. Features are auto-discovered at startup — adding a new feature only requires creating a directory with `__init__.py` and `cog.py`.

```text
Kairo
│
├── Core
│   ├── Configuration
│   ├── Logging
│   ├── Events (internal pub/sub bus)
│   └── Lifecycle
│
├── Database
│   ├── Models
│   ├── Repositories
│   └── Migrations
│
├── Components
│   ├── LayoutView send helpers
│   ├── Paginator
│   └── discord.ui re-exports
│
├── Features (auto-discovered)
│   ├── Moderation
│   ├── AutoMod
│   ├── Logging
│   ├── Utility
│   ├── Onboarding
│   ├── Tickets
│   ├── Giveaways
│   ├── Leveling
│   ├── Roles
│   ├── Welcome
│   ├── Fun
│   └── ...
│
├── API
│
└── Dashboard
```

---

# 🔌 Plugin System

One of Kairo's long-term goals is to provide an extensible plugin architecture.

A future plugin could add:

* Commands
* Components
* Database models
* Dashboard pages
* API endpoints
* Background tasks
* Event listeners
* Application emojis
* Configuration options

The intended result is that developers can extend Kairo without modifying its core.

---

# 🌍 Deployment

Kairo is being designed with self-hosting as a first-class feature.

### Local

Run Kairo directly on your computer for development or small installations.

### Docker

Planned Docker support will make it possible to deploy Kairo using containers.

### VPS

Kairo will include documentation for common VPS deployments.

### Tunnel Integrations

For users who need to expose the dashboard or API without configuring traditional port forwarding, optional integrations are planned for:

* [ ] Cloudflare Tunnel
* [ ] ngrok
* [ ] Localtonet

These integrations will be optional. Kairo will not require a tunnel provider to operate.

---

# 📚 Documentation

Documentation is intended to be a major part of the Kairo project.

Rather than only documenting commands, Kairo will provide guides for the entire system.

Planned documentation includes:

### Getting Started

* [x] Installation
* [x] Discord application setup
* [x] Bot token configuration
* [x] Environment variables
* [ ] Database initialization
* [x] First launch

### Self Hosting

* [ ] Windows
* [ ] Linux
* [ ] macOS
* [ ] Docker
* [ ] VPS
* [ ] Reverse proxy
* [ ] Cloudflare Tunnel
* [ ] ngrok
* [ ] Localtonet
* [ ] Backups
* [ ] Updates
* [ ] Troubleshooting

### Administration

* [ ] Dashboard guide
* [ ] Guild onboarding wizard
* [ ] Server configuration
* [ ] Permissions
* [ ] Security
* [ ] Database management
* [ ] Logging

### Developers

* [x] Architecture
* [x] Components V2
* [x] Creating features (auto-discovery)
* [ ] Creating plugins
* [x] Database repositories
* [ ] API development
* [ ] Dashboard development
* [ ] Application emojis
* [ ] Testing
* [ ] Contributing

---

# 🛠️ Technology

| Technology            | Purpose                          |
| --------------------- | -------------------------------- |
| **Python**            | Discord bot backend              |
| **discord.py 2.7.1**  | Discord API library              |
| **SQLite**            | Persistent storage               |
| **Vite**              | Dashboard tooling                |
| **Discord OAuth2**    | Dashboard authentication         |
| **Docker**            | Containerized deployment         |
| **Cloudflare Tunnel** | Optional tunneling               |
| **ngrok**             | Optional tunneling               |
| **Localtonet**        | Optional tunneling               |

Additional technologies may be introduced as development progresses.

---

# 🗺️ Roadmap

Kairo will be developed incrementally.

## Phase 1 — Foundation

* [x] Repository structure
* [x] Configuration system
* [x] Logging system
* [x] Discord bot initialization
* [x] Auto-discovery cog loader
* [x] SQLite database
* [x] Database migrations
* [x] Basic error handling
* [x] Development environment

## Phase 2 — Components V2

* [x] Native discord.ui CV2 integration (LayoutView)
* [x] Send helpers (send_layout, edit_layout, followup_layout)
* [x] Reusable UI components (Container, Section, TextDisplay, Separator, Thumbnail)
* [x] Interaction handling
* [x] Pagination (Paginator built on LayoutView)
* [x] Modals (discord.ui.Modal)
* [x] Confirmation dialog helper
* [x] Interactive multi-step flow helper
* [x] Configuration panel helper

## Phase 3 — Core Features

* [x] Moderation (ban, kick, timeout, warn, history, case)
* [x] AutoMod (scaffold — rule engine Phase 3)
* [x] Logging (scaffold — channel output Phase 3)
* [x] Utility commands (/help, /ping, /botinfo, /userinfo, /serverinfo, /avatar)
* [x] Full moderation logging to channels
* [x] AutoMod rule engine (spam, links, words, mentions)
* [x] Welcome / leave messages
* [x] Auto roles
* [x] Button / select menu roles
* [x] Server configuration system

## Phase 4 — Onboarding & Customization

* [ ] Interactive guild setup wizard (/setup — multi-step CV2 flow)
* [ ] First-run detection on guild join
* [ ] Application emoji registry and auto-registration at startup
* [ ] Emoji fallback system (Unicode when application emojis unavailable)
* [ ] Per-guild branding (accent colour, footer, status)
* [ ] Per-guild feature enable/disable
* [ ] Per-guild language / timezone
* [ ] Custom command prefix per guild

## Phase 5 — Community Features

* [ ] Tickets (thread-based, CV2 open panel)
* [ ] Ticket transcripts and routing
* [ ] Suggestions (CV2 vote panel, status workflow)
* [ ] Giveaways (enter / leave / re-roll)
* [ ] Polls (timed, multi-choice, live results)
* [ ] Starboard
* [ ] Leveling (XP, rank cards, leaderboard)
* [ ] Level roles
* [ ] Reminders
* [ ] Custom responses
* [ ] Fun commands

## Phase 6 — Dashboard

* [ ] Vite application scaffold
* [ ] Dark theme UI
* [ ] Discord OAuth2 login
* [ ] Guild selector
* [ ] Guild permission validation
* [ ] API (aiohttp, auth middleware)
* [ ] Server overview page
* [ ] Onboarding wizard in dashboard
* [ ] Configuration pages for all features
* [ ] Moderation case browser
* [ ] Responsive mobile layout

## Phase 7 — Deployment

* [ ] Docker and docker-compose
* [ ] Local deployment guide
* [ ] VPS documentation
* [ ] Cloudflare Tunnel integration
* [ ] ngrok integration
* [ ] Localtonet integration
* [ ] Reverse proxy configuration (Nginx, Caddy)

## Phase 8 — Extensibility

* [ ] Plugin architecture
* [ ] Plugin API
* [ ] Plugin lifecycle (load / unload / reload)
* [ ] Plugin database model registration
* [ ] Plugin dashboard page registration
* [ ] Developer documentation
* [ ] Plugin examples
* [ ] Plugin registry / discovery

## Phase 9 — Production Readiness

* [ ] Automated test suite
* [ ] Security audit
* [ ] Performance profiling and improvements
* [ ] Database backup tooling
* [ ] Migration tooling
* [ ] Rate limit handling and backoff
* [ ] Health check endpoints
* [ ] Comprehensive documentation
* [ ] Stable release (v1.0)

---

# 📊 Project Status

> 🚧 **Early Development** — Phases 1–3 in progress

| Phase                        | Status         |
|------------------------------|----------------|
| Phase 1 — Foundation         | ✅ Complete     |
| Phase 2 — Components V2      | ✅ Complete     |
| Phase 3 — Core Features      | ✅ Complete     |
| Phase 4 — Onboarding         | 📋 Planned      |
| Phase 5 — Community Features | 📋 Planned      |
| Phase 6 — Dashboard          | 📋 Planned      |
| Phase 7 — Deployment         | 📋 Planned      |
| Phase 8 — Extensibility      | 📋 Planned      |
| Phase 9 — Production Ready   | 📋 Planned      |

Expect breaking changes, incomplete features, and unfinished documentation during early development.

The roadmap represents the **current direction of the project**, not a guarantee that every feature will be implemented exactly as described.

---

# 🤝 Contributing

Contributions will be welcome once the core architecture has stabilized.

Potential contribution areas include:

* Discord features
* Components V2 interfaces
* Dashboard development
* Documentation
* Testing
* Plugins
* Bug fixes
* Performance improvements
* Translations

Before contributing, please read the project's contribution guidelines and development documentation.

---

# 🔒 Security

If you discover a security vulnerability, please do not publicly disclose it in a GitHub issue.

Security reporting instructions will be provided once the project reaches a stage where external contributions are enabled.

---

# 📜 License

Kairo's license has not yet been finalized.

The repository will contain the applicable license before the first stable release.

---

# ⭐ Project Goals

Kairo isn't intended to simply become another Discord bot with hundreds of commands.

The long-term goal is to build a **complete open-source Discord platform** that is:

> **Powerful enough for large servers.**
> **Simple enough for beginners.**
> **Flexible enough for developers.**
> **Easy enough to self-host.**

If Kairo succeeds, installing the project should feel less like assembling a collection of unrelated services and more like installing a complete Discord platform.

---

## 💙 Kairo

Built with Python, Discord Components V2, and a lot of ambition.

**More coming soon.**
