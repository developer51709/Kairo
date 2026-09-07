"""
src/run.py
----------
Kairo Entrypoint

This is the main entry point for the Kairo platform. It:
    1. Parses command-line arguments.
    2. Loads configuration from the environment (.env file).
    3. Starts the selected components — by default ALL of them:
         - Discord bot      (discord.py gateway + features)
         - REST API server  (aiohttp, serves the dashboard)
         - Web dashboard    (Vite dev server, launched as a subprocess)
    4. Runs until interrupted, then shuts every component down cleanly.

Usage:
    # Start everything (bot + API + dashboard):
    python src/run.py

    # Disable individual components:
    python src/run.py --no-bot
    python src/run.py --no-api
    python src/run.py --no-dashboard

    # Run exactly one component:
    python src/run.py --only bot
    python src/run.py --only api
    python src/run.py --only dashboard

    # Run in debug mode:
    python src/run.py --debug

Environment:
    Kairo reads configuration from a .env file in the project root.
    Copy .env.example to .env and fill in your values before running.

    Required:
        BOT_TOKEN      Discord bot token
        CLIENT_ID      Discord application client ID
        CLIENT_SECRET  Discord OAuth2 client secret

    Dashboard prerequisites (only when the dashboard component is enabled):
        - Node.js with bun or npm available on PATH
        - Dashboard dependencies installed:
              cd src/dashboard && bun install    # or: npm install

    See .env.example for the full list of options.
"""

import argparse
import asyncio
import os
import shutil
import signal
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot.core.config import Config, ConfigError
from src.bot.core.bot import KairoBot

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DASHBOARD_DIR = os.path.join(PROJECT_ROOT, "src", "dashboard")
COMPONENTS = ("bot", "api", "dashboard")


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
    BRIGHT_WHITE = "\033[97m"


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
        epilog="""\
Examples:
  python src/run.py                     Start everything (bot + API + dashboard)
  python src/run.py --no-bot            Start API + dashboard without the bot
  python src/run.py --no-api            Start bot + dashboard without the API
  python src/run.py --no-dashboard      Start bot + API without the dashboard
  python src/run.py --only bot          Start only the bot
  python src/run.py --only dashboard    Start only the web dashboard
  python src/run.py --debug             Start everything in debug mode
        """,
    )
    parser.add_argument(
        "--only",
        choices=COMPONENTS,
        metavar="{bot,api,dashboard}",
        help="Run only this component instead of everything.",
    )
    for component in COMPONENTS:
        parser.add_argument(
            f"--no-{component}",
            action="store_true",
            help=f"Do not start the {component} component.",
        )
    parser.add_argument(
        "--with-api",
        action="store_true",
        help="(Legacy) API server now starts by default — use --no-api to disable it.",
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


def resolve_components(args: argparse.Namespace) -> list[str]:
    """
    Decide which components run based on the CLI flags.

    Default: all three. --only runs a single component. --no-<component>
    removes individual components from the default set.
    """
    disabled = [name for name in COMPONENTS if getattr(args, f"no_{name}")]

    if args.only:
        if args.only in disabled:
            parser_error = (
                f"--only {args.only} conflicts with --no-{args.only}: "
                "use one or the other."
            )
            print(parser_error, file=sys.stderr)
            sys.exit(2)
        return [args.only]

    return [name for name in COMPONENTS if name not in disabled]


# ------------------------------------------------------------------ #
# Dashboard subprocess                                                 #
# ------------------------------------------------------------------ #

def dashboard_is_ready() -> bool:
    """
    True when the dashboard source tree is present and scaffolded
    (src/dashboard/package.json exists).
    """
    return bool(
        os.path.isdir(DASHBOARD_DIR)
        and os.path.isfile(os.path.join(DASHBOARD_DIR, "package.json"))
    )


def start_dashboard_process() -> subprocess.Popen | None:
    """
    Launch the Vite dev server (src/dashboard) as a child process.

    Uses bun when available and falls back to npm. Returns the process
    handle, or None when the dashboard cannot be started (missing
    tooling or uninstalled dependencies).
    """
    if not dashboard_is_ready():
        Branding.print_warning(
            "Dashboard source not found (expected src/dashboard/package.json). Skipping."
        )
        return None

    if not os.path.isdir(os.path.join(DASHBOARD_DIR, "node_modules")):
        Branding.print_warning(
            "Dashboard dependencies are not installed. Skipping dashboard."
        )
        Branding.print_info(
            "Install them with:  cd src/dashboard && bun install   (or: npm install)"
        )
        Branding.print_info("Or run with --no-dashboard to skip this component.")
        return None

    package_manager = shutil.which("bun") or shutil.which("npm")
    if not package_manager:
        Branding.print_warning(
            "Neither 'bun' nor 'npm' was found on PATH. Skipping dashboard."
        )
        return None

    command = [package_manager, "run", "dev"]
    try:
        if os.name == "posix":
            # Own process group so the whole Vite tree can be stopped later.
            proc = subprocess.Popen(
                command,
                cwd=DASHBOARD_DIR,
                start_new_session=True,
            )
        else:
            proc = subprocess.Popen(command, cwd=DASHBOARD_DIR)
    except OSError as exc:
        Branding.print_warning(f"Could not launch dashboard: {exc}")
        return None

    return proc


def stop_dashboard_process(proc: subprocess.Popen | None) -> None:
    """Terminate the dashboard dev server (and its process group)."""
    if proc is None or proc.poll() is not None:
        return

    try:
        if os.name == "posix":
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        else:
            proc.terminate()
        proc.wait(timeout=5)
    except (ProcessLookupError, subprocess.TimeoutExpired):
        try:
            if os.name == "posix":
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            else:
                proc.kill()
            proc.wait(timeout=5)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            pass


async def main() -> None:
    args = parse_args()

    if args.debug:
        os.environ["DEBUG"] = "true"

    components = resolve_components(args)

    Branding.print_header()
    Branding.print_starting()

    # Relative --env-file paths are interpreted from the project root
    # (where .env.example lives), regardless of the working directory.
    env_file = args.env_file
    if env_file and not os.path.isabs(env_file):
        env_file = os.path.join(PROJECT_ROOT, env_file)

    try:
        config = Config(env_file=env_file)
        Branding.print_success("Configuration loaded")
    except ConfigError as e:
        print(f"\n{Colors.BRIGHT_RED if sys.stdout.isatty() else ''}x{Colors.RESET if sys.stdout.isatty() else ''} Configuration error:\n{e}\n", file=sys.stderr)
        print("Run 'python src/setup.py' to configure Kairo interactively.", file=sys.stderr)
        sys.exit(1)

    if config.env_file_used:
        Branding.print_info(f"Env file: {config.env_file_used}")
    else:
        Branding.print_info("Env file: (none — using process environment)")

    token = config.bot_token
    if token:
        masked = token[:5] + "*" * (len(token) - 5)
    else:
        masked = "Not set"

    Branding.print_info(f"Bot token: {masked}")
    Branding.print_info(f"Client ID: {config.client_id}")
    Branding.print_info(f"Debug mode: {'Enabled' if config.debug else 'Disabled'}")
    Branding.print_info(f"Database: {config.db_path}")

    Branding.print_info(
        "Components: " + ", ".join(f"[{name}]" for name in components)
    )

    # The API borrows the bot instance for its handlers, so create the bot
    # whenever either component is requested. The bot is not started unless
    # its component is enabled.
    bot: KairoBot | None = None
    if "bot" in components or "api" in components:
        Branding.print_info("Creating bot instance...")
        bot = KairoBot(config=config)
        Branding.print_success("KairoBot instance created")

    api_runner = None
    dashboard_proc: subprocess.Popen | None = None
    bot_started = False

    try:
        # --- Web dashboard (Vite dev server) -------------------------- #
        # Started before the API so port probes latch onto the web UI
        # (0.0.0.0:5173, or $PORT when injected) instead of the API port.
        if "dashboard" in components:
            Branding.print_info("Starting dashboard (Vite dev server)...")
            dashboard_proc = start_dashboard_process()
            if dashboard_proc is not None:
                bound_port = os.environ.get("PORT") or "5173"
                Branding.print_success(
                    f"Dashboard (web UI) starting at {config.dashboard_url} "
                    f"— Vite binds 0.0.0.0:{bound_port} (logs stream below once booted)"
                )

        # --- REST API server ------------------------------------------ #
        if "api" in components:
            try:
                from src.api.app import create_app, start_api
                Branding.print_info("Starting API server...")
                app = create_app(bot=bot, config=config)
                api_runner = await start_api(
                    app, host=config.api_host, port=config.api_port
                )
                Branding.print_success(
                    f"API server running on http://{config.api_host}:{config.api_port}"
                )
                if not config.api_secret:
                    Branding.print_warning(
                        "API_SECRET is not set — the API will reject all "
                        "non-health requests (HTTP 503)."
                    )
            except ImportError:
                Branding.print_warning("Could not start API server: aiohttp is not installed.")
                Branding.print_info("Run: pip install aiohttp")

        # --- Discord bot ---------------------------------------------- #
        if "bot" in components and bot is not None:
            Branding.print_info("Starting Discord bot...")
            bot_started = True
            await bot.start_kairo()
        else:
            Branding.print_info(
                "Discord bot disabled — running without it. "
                "Press Ctrl-C to stop everything."
            )
            await asyncio.Event().wait()

    finally:
        if api_runner:
            await api_runner.cleanup()
        if dashboard_proc is not None:
            Branding.print_info("Stopping dashboard dev server...")
            stop_dashboard_process(dashboard_proc)
        if bot_started:
            Branding.print_info("Bot shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if sys.stdout.isatty():
            print(f"\n{Colors.BRIGHT_YELLOW}Received interrupt signal. Shutting down gracefully...{Colors.RESET}")
        else:
            print("\nReceived interrupt signal. Shutting down gracefully...")
        sys.exit(0)
