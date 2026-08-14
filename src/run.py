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

    # Run in debug mode:
    python src/run.py --debug

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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot.core.config import Config, ConfigError
from src.bot.core.bot import KairoBot


# ANSI Color codes for beautiful terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"


class Branding:
    KAIRO_VERSION = "0.1.0"
    
    @staticmethod
    def get_logo() -> str:
        logo = r"""
⠀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⣼⢀⣤⣶⡿⠀⠀⠀⠀⠀⠀⠀⠀⣠⣶⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢠⣿⠟⠉⠀⠀⠀⢀⣶⠿⢿⠀⠀⠀⢀⡀⠀⢠⡆⠀⣀⣤⠀⠀⢀⣤⣄⠀
⠀⣿⣦⠀⠀⠀⠀⣿⠀⠀⠀⣇⠀⠀⢸⠀⠀⠘⡇⣾⠋⠀⠀⢰⡏⠀⠈⣧
⠀⣿⠀⠙⢷⣄⠀⣿⠀⠀⣠⣿⡀⠀⢸⠀⠀⠀⣿⠁⠀⠀⠀⠸⣆⠀⢠⡿
⠀⠻⠀⠀⠀⠀⠀⠀⠙⠛⠉⠀⠉⠀⠈⠀⠀⠀⠉⠀⠀⠀⠀⠀⠈⠛⠋⠀
        """
        if sys.stdout.isatty():
            colors = [Colors.BRIGHT_BLUE, Colors.BRIGHT_CYAN, Colors.BRIGHT_MAGENTA]
            logo_lines = []
            for line in logo.strip().split('\n'):
                colored_line = ""
                for i, char in enumerate(line):
                    if char != ' ':
                        color = colors[i % len(colors)]
                        colored_line += f"{color}{char}{Colors.RESET}"
                    else:
                        colored_line += char
                logo_lines.append(colored_line)
            return '\n'.join(logo_lines)
        return logo
    
    @staticmethod
    def print_header() -> None:
        if sys.stdout.isatty():
            print("\n" + "=" * 70)
            print(f"{Colors.BRIGHT_CYAN}{Branding.get_logo()}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_BLUE}Kairo v{Branding.KAIRO_VERSION}{Colors.RESET} {Colors.DIM}- A modern, self-hostable Discord platform{Colors.RESET}")
            print("=" * 70)
        else:
            print("\n" + "=" * 60)
            print("  Kairo - A modern, self-hostable Discord platform")
            print(f"  v{Branding.KAIRO_VERSION}")
            print("=" * 60)
    
    @staticmethod
    def print_starting() -> None:
        if sys.stdout.isatty():
            print(f"\n{Colors.BRIGHT_WHITE}[{Colors.BRIGHT_GREEN}+{Colors.BRIGHT_WHITE}]{Colors.RESET} {Colors.BRIGHT_WHITE}Starting Kairo...{Colors.RESET}")
        else:
            print("\n[+] Starting Kairo...")
    
    @staticmethod
    def print_success(message: str) -> None:
        if sys.stdout.isatty():
            print(f"  {Colors.BRIGHT_GREEN}+{Colors.RESET}  {message}")
        else:
            print(f"  +  {message}")
    
    @staticmethod
    def print_info(message: str) -> None:
        if sys.stdout.isatty():
            print(f"  {Colors.BRIGHT_WHITE}i{Colors.RESET}  {message}")
        else:
            print(f"  i  {message}")
    
    @staticmethod
    def print_warning(message: str) -> None:
        if sys.stdout.isatty():
            print(f"  {Colors.BRIGHT_YELLOW}!{Colors.RESET}  {message}")
        else:
            print(f"  !  {message}")
    
    @staticmethod
    def print_error(message: str) -> None:
        if sys.stdout.isatty():
            print(f"  {Colors.BRIGHT_RED}x{Colors.RESET}  {message}")
        else:
            print(f"  x  {message}")


def parse_args() -> argparse.Namespace:
    description = f"{Colors.BRIGHT_BLUE if sys.stdout.isatty() else ''}Kairo{Colors.RESET if sys.stdout.isatty() else ''} - A modern, self-hostable Discord platform."
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/run.py              Start the bot (no API server)
  python src/run.py --with-api   Start the bot and the REST API server
  python src/run.py --debug      Start in debug mode (verbose logging)
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
    args = parse_args()

    if args.debug:
        os.environ["DEBUG"] = "true"

    Branding.print_header()
    Branding.print_starting()

    try:
        config = Config()
        Branding.print_success(f"Configuration loaded from {config.env_file}")
    except ConfigError as e:
        print(f"\n{Colors.BRIGHT_RED if sys.stdout.isatty() else ''}x{Colors.RESET if sys.stdout.isatty() else ''} Configuration error:\n{e}\n", file=sys.stderr)
        print("Run 'python src/setup.py' to configure Kairo interactively.", file=sys.stderr)
        sys.exit(1)

    Branding.print_info(f"Bot token: {'*' * len(config.bot_token) if config.bot_token else 'Not set'}")
    Branding.print_info(f"Client ID: {config.client_id}")
    Branding.print_info(f"Debug mode: {'Enabled' if config.debug else 'Disabled'}")
    Branding.print_info(f"Database: {config.db_path}")

    if args.with_api:
        Branding.print_info("API server: Enabled")
        Branding.print_info(f"API host: {config.api_host}:{config.api_port}")
    else:
        Branding.print_info("API server: Disabled")

    Branding.print_info("Creating bot instance...")
    bot = KairoBot(config=config)
    Branding.print_success("KairoBot instance created")

    api_runner = None
    if args.with_api:
        try:
            from src.api.app import create_app, start_api
            Branding.print_info("Starting API server...")
            app = create_app(bot=bot, config=config)
            api_runner = await start_api(app, host=config.api_host, port=config.api_port)
            Branding.print_success(f"API server running on {config.api_host}:{config.api_port}")
        except ImportError:
            Branding.print_warning("Could not start API server: aiohttp is not installed.")
            Branding.print_info("Run: pip install aiohttp")

    Branding.print_info("Starting Discord bot...")
    Branding.print_success("Kairo is ready!")

    try:
        await bot.start_kairo()
    finally:
        if api_runner:
            await api_runner.cleanup()


if __name__ == "__main__":
    try:
        Branding.print_header()
        asyncio.run(main())
    except KeyboardInterrupt:
        if sys.stdout.isatty():
            print(f"\n{Colors.BRIGHT_YELLOW}Received interrupt signal. Shutting down gracefully...{Colors.RESET}")
        else:
            print("\nReceived interrupt signal. Shutting down gracefully...")
        sys.exit(0)
