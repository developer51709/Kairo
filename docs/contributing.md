# Contributing

Thank you for your interest in contributing to Kairo.

> **Note:** The project is in early development. The core architecture is
> being established. External contributions are welcome once the foundation
> has stabilised (Phase 2 onwards).

---

## Ways to Contribute

- **Bug reports** — Open a GitHub issue with a clear description and reproduction steps.
- **Feature suggestions** — Open a discussion with context on why the feature is valuable.
- **Code contributions** — Bug fixes, new features, tests, and documentation.
- **Documentation** — Improvements to guides and API docs.

---

## Development Setup

```bash
# Clone and enter the repo
git clone https://github.com/your-org/kairo.git
cd kairo

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your bot token, client ID, etc.
# Set DEV_GUILD_ID for instant slash command sync

# Run in debug mode
python src/run.py --debug
```

---

## Code Style

- **Python 3.11+** type hints throughout.
- Docstrings on all public classes and methods (NumPy/Google style is fine).
- `snake_case` for variables and functions, `PascalCase` for classes.
- Import order: stdlib → third-party → local (use `isort` if available).
- Keep lines under 100 characters.

---

## Architecture Guidelines

Before writing code, read [architecture.md](architecture.md).

Key rules:

- **Features are isolated.** Never import from `src.bot.features.X` in another feature.
  Use the event bus for cross-feature communication.
- **Repositories own SQL.** Never write raw SQL outside `src/bot/database/repositories/`.
- **Components for UI.** Use the abstractions in `src/bot/components/` rather than raw dicts.
- **Config through Config.** Never read `os.environ` directly. Add a property to `Config`.
- **Logging via get_logger.** `from src.bot.core.logging import get_logger; log = get_logger(__name__)`

---

## Adding a Feature

See [features.md](features.md) for a step-by-step guide.

---

## Adding a Database Table

1. Create a model in `src/bot/database/models/`.
2. Create a repository in `src/bot/database/repositories/`.
3. Create a migration file: `src/bot/database/migrations/NNN_description.sql`.
4. Update `src/bot/database/models/__init__.py` and `repositories/__init__.py`.

See [database.md](database.md) for details.

---

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR.
- Include a clear description of what changed and why.
- Test your changes manually before submitting.
- Update relevant documentation.
- Keep PR titles under 70 characters.

---

## Security

If you discover a security vulnerability, do not open a public issue.
Contact the maintainers privately. Security reporting instructions will
be formalised before the first stable release.
