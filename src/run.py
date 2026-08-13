"""
src/run.py
----------
Kairo Entrypoint

This is the main entry point for the Kairo platform. It:
    1. Parses command-line arguments.
    2. Loads configuration from the environment (.env file).
    3. Creates the KairoBot instance.
    4. Optionally starts the REST API server alongside the bot.
    5. Runs the bot's asyncio event loop.

Usage:
    # Run the bot only:
    python src/run.py

    # Run the bot + API server:
    python src/run.py --with-api

    # Run setup wizard first:
    python src/setup.py

Environment:
    Kairo reads configuration from a .env file in the project root.
    Copy .env.example to .env and fill in your values before running.

    Required:
        BOT_TOKEN      Discord bot token
        CLIENT_ID      Discord application client ID
        CLIENT_SECRET  Discord OAuth2 client secret

    See .env.example for the full list of options.
"""

import argparse
import asyncio
import sys
import os

# Ensure the project root is on the Python path so imports work regardless
# of where the script is run from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot.core.config import Config, ConfigError
from src.bot.core.bot import KairoBot


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Kairo — A modern, self-hostable Discord platform.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/run.py               Start the bot (no API server)
  python src/run.py --with-api    Start the bot and the REST API server
  python src/run.py --debug       Start in debug mode (verbose logging)
        """,
    )
    parser.add_argument(
        "--with-api",
        action="store_true",
        help="Also start the REST API server for the dashboard.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode (verbose logging, dev guild sync).",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        metavar="PATH",
        help="Path to the .env file (default: .env in project root).",
    )
    return parser.parse_args()


async def main() -> None:
    """
    Async main function.

    Initialises all Kairo subsystems and runs the bot.
    If --with-api is passed, the API server is started concurrently.
    """
    args = parse_args()

    # Override DEBUG in environment if --debug flag was passed
    if args.debug:
        os.environ["DEBUG"] = "true"

    # Load configuration
    try:
        config = Config()
    except ConfigError as e:
        print(f"\n❌ Configuration error:\n{e}\n", file=sys.stderr)
        print("Run 'python src/setup.py' to configure Kairo interactively.", file=sys.stderr)
        sys.exit(1)

    # Create the bot
    bot = KairoBot(config=config)

    # Start the API server if requested
    api_runner = None
    if args.with_api:
        try:
            from src.api.app import create_app, start_api
            app = create_app(bot=bot, config=config)
            api_runner = await start_api(app, host=config.api_host, port=config.api_port)
        except ImportError:
            print(
                "⚠️  Could not start API server: aiohttp is not installed.\n"
                "   Run: pip install aiohttp",
                file=sys.stderr,
            )

    # Run the bot (blocks until shutdown)
    try:
        await bot.start_kairo()
    finally:
        if api_runner:
            await api_runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
