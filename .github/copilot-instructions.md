# Copilot Instructions for Kairo

## Project Overview

**Kairo** is a self-hostable Discord platform combining a Python bot backend, a modern Vite-powered web dashboard, and an extensible component system. The project is currently in **early development (Phase 1)** and provides a foundation for building modular Discord features.

## Technology Stack

- **Bot Backend**: Python, discord.py 2.7.1
- **Persistence**: SQLite with repository pattern
- **Dashboard**: Vite (web frontend)
- **Authentication**: Discord OAuth2
- **UI Framework**: Discord Components V2 (custom abstraction layer)

## Directory Structure

```
Kairo/
├── src/
│   ├── bot/              # Discord bot implementation (currently empty structure)
│   ├── dashboard/        # Vite web dashboard (currently empty structure)
│   ├── run.py            # Main entrypoint for bot and dashboard
│   └── setup.py          # Interactive setup wizard
├── README.md             # Project vision and roadmap
└── DONATE.md             # Donation information
```

## Architecture Principles

### Planned Multi-Layer Architecture

The project follows a modular structure (not yet fully implemented):

1. **Core** — Configuration, logging, events, lifecycle management
2. **Database** — SQLite models, repository pattern, migrations
3. **Components** — Reusable Discord UI abstractions (V2)
4. **Features** — Moderation, AutoMod, tickets, etc. (independent modules)
5. **API** — Backend endpoints for dashboard communication
6. **Dashboard** — Vite frontend for server management

### Key Design Patterns

- **Repositories over Raw SQL**: Database access should go through repository classes, not direct SQL queries
- **Modular Features**: Each feature (moderation, tickets, etc.) is an independent module
- **Components Abstraction**: Discord interactions use high-level components (Panel, Container, Section, etc.) rather than raw embeds
- **Permission Validation**: Authentication doesn't equal authorization — dashboard always validates server permissions

Example Component API (from README, subject to change):
```python
panel = Panel(
    Container(
        Text("# Server Configuration"),
        Separator(),
        ActionRow(
            Button(label="Moderation", custom_id="config:moderation"),
            Button(label="Logging", custom_id="config:logging"),
        ),
    )
)
```

## Development Workflow

### Startup
1. The bot is initialized via `src/run.py`
2. Configuration is managed through environment variables and setup.py
3. SQLite database is initialized with the migrations system

### Before Starting Work
- Review the README's Architecture section and Roadmap to understand the intended design
- Check Phase 1 (Foundation) requirements — core config, logging, events, lifecycle, database
- Note: Many entrypoint files are currently placeholders

### Adding Features
- Create a new module under `src/bot/<feature_name>/`
- Use the repository pattern for database access
- Export interfaces through clear module entry points
- Avoid direct SQL — create repository classes in `src/bot/database/repositories/`

### Database Changes
- Add models to `src/bot/database/models/`
- Create migrations in `src/bot/database/migrations/`
- Implement repository methods, not raw queries

## Current Project Status

**Phase 1 (Foundation)** - Building core infrastructure:
- Repository structure established ✓
- Setup wizard structure defined
- Main entry points defined
- Architecture documented

**Not yet implemented:**
- Build/test/lint commands (add when first tests/linting is introduced)
- Actual Discord bot logic
- Dashboard API and frontend
- Component V2 system implementation
- Database models and repositories

## Dependencies

Not yet specified. When added, will likely include:
- discord.py 2.7.1+
- SQLite driver (built-in to Python)
- Vite + frontend framework (for dashboard)

## Contributing Notes

- The project welcomes contributions after the core architecture stabilizes
- Follow the planned modular structure — avoid adding features directly to the main bot file
- Implement database access through repositories
- Document new features and their configuration

For more information, see README.md's "Roadmap" and "Planned Features" sections.
