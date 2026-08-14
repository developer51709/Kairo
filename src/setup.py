"""
src/setup.py
-------------
Kairo Interactive Setup Wizard

An interactive command-line wizard that guides the user through initial
configuration. It collects required and optional values, validates them,
and writes a .env file to the project root.

Usage:
    python src/setup.py
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_ENV_FILE = _PROJECT_ROOT / ".env"

KAIR_VERSION = "0.1.0"
KAIRO_AUTHOR = "Built with love by Kairo Team"


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
    @staticmethod
    def get_kairo_logo() -> str:
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
            print(f"{Colors.BRIGHT_CYAN}{Branding.get_kairo_logo()}{Colors.RESET}")
            print(f"{Colors.BOLD}{Colors.BRIGHT_BLUE}Kairo v{KAIR_VERSION}{Colors.RESET} {Colors.DIM}- {KAIRO_AUTHOR}{Colors.RESET}")
            print(f"{Colors.BRIGHT_YELLOW}{'Setup Wizard':^68}{Colors.RESET}")
            print("=" * 70)
        else:
            print("\n" + "=" * 60)
            print("  Kairo Setup Wizard")
            print(f"  v{KAIR_VERSION} - {KAIRO_AUTHOR}")
            print("=" * 60)
        print()
    
    @staticmethod
    def print_section(title: str) -> None:
        if sys.stdout.isatty():
            print(f"{Colors.BRIGHT_MAGENTA}─{Colors.RESET} {Colors.BOLD}{Colors.BRIGHT_WHITE}{title}{Colors.RESET} {Colors.BRIGHT_MAGENTA}──────────────────────────────────{Colors.RESET}")
        else:
            print(f"── {title} ─────────────────────────────────────")
    
    @staticmethod
    def print_info(message: str) -> None:
        if sys.stdout.isatty():
            print(f"  {Colors.BRIGHT_WHITE}i{Colors.RESET}  {message}")
        else:
            print(f"  i  {message}")
    
    @staticmethod
    def print_success(message: str) -> None:
        if sys.stdout.isatty():
            print(f"  {Colors.BRIGHT_GREEN}+{Colors.RESET}  {message}")
        else:
            print(f"  +  {message}")
    
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


def _prompt(label: str, default: Optional[str] = None, secret: bool = False, required: bool = True) -> str:
    display_default = f" [{default}]" if default else ""
    display_required = " (required)" if required and not default else ""
    if sys.stdout.isatty():
        prompt_str = f"  {Colors.BRIGHT_WHITE}{label}{Colors.RESET}{display_required}{display_default}: "
    else:
        prompt_str = f"  {label}{display_required}{display_default}: "
    while True:
        if secret:
            import getpass
            value = getpass.getpass(prompt_str)
        else:
            value = input(prompt_str).strip()
        if not value:
            if default is not None:
                return default
            if not required:
                return ""
            Branding.print_error("This field is required. Please enter a value.")
            continue
        return value


def _confirm(label: str, default: bool = True) -> bool:
    yn = "Y/n" if default else "y/N"
    if sys.stdout.isatty():
        prompt = f"  {Colors.BRIGHT_WHITE}{label}{Colors.RESET} [{yn}]: "
    else:
        prompt = f"  {label} [{yn}]: "
    value = input(prompt).strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def _detect_termux() -> bool:
    return os.path.exists("/data/data/com.termux") or "com.termux" in os.environ.get("PREFIX", "")


def _check_existing_env() -> bool:
    if not _ENV_FILE.exists():
        return True
    Branding.print_warning(f"A .env file already exists at: {_ENV_FILE}")
    return _confirm("Do you want to overwrite it?", default=False)


def _write_env(values: dict) -> None:
    lines = [
        "# Kairo Configuration",
        f"# {'=' * 50}",
        "# Generated by Kairo Setup Wizard",
        f"# Version: {KAIR_VERSION}",
        "# Edit as needed or re-run python src/setup.py",
        "# See docs/configuration.md for full documentation.",
        "",
        "# --- Discord ---",
        f"BOT_TOKEN={values.get('BOT_TOKEN', '')}",
        f"CLIENT_ID={values.get('CLIENT_ID', '')}",
        f"CLIENT_SECRET={values.get('CLIENT_SECRET', '')}",
        f"BOT_PREFIX={values.get('BOT_PREFIX', '!')}",
        "",
        "# Dev Guild ID for instant slash command sync (leave empty for production)",
        f"DEV_GUILD_ID={values.get('DEV_GUILD_ID', '')}",
        "",
        "# --- Database ---",
        f"DB_PATH={values.get('DB_PATH', 'data/kairo.db')}",
        "",
        "# --- Logging ---",
        "# Levels: DEBUG, INFO, WARNING, ERROR",
        f"LOG_LEVEL={values.get('LOG_LEVEL', 'INFO')}",
        "",
        "# --- API Server ---",
        f"API_HOST={values.get('API_HOST', '127.0.0.1')}",
        f"API_PORT={values.get('API_PORT', '8080')}",
        f"API_SECRET={values.get('API_SECRET', '')}",
        "",
        "# --- Dashboard / OAuth2 ---",
        f"DASHBOARD_URL={values.get('DASHBOARD_URL', 'http://localhost:5173')}",
        "# OAUTH_REDIRECT=  # Defaults to DASHBOARD_URL/auth/callback",
        "",
        "# --- Runtime ---",
        f"DEBUG={values.get('DEBUG', 'false')}",
    ]
    _ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    Branding.print_success(f".env file written to: {_ENV_FILE}")


def _install_dependencies() -> None:
    req_file = _PROJECT_ROOT / "requirements.txt"
    if not req_file.exists():
        Branding.print_warning("requirements.txt not found. Skipping dependency installation.")
        return
    print()
    if not _confirm("Install Python dependencies from requirements.txt?", default=True):
        Branding.print_info("Skipping. Run 'pip install -r requirements.txt' manually.")
        return
    is_termux = _detect_termux()
    pip_cmd = [sys.executable, "-m", "pip", "install", "-r", str(req_file)]
    if is_termux:
        Branding.print_info("Termux detected. Note: some packages may need additional setup.")
        termux_req = _PROJECT_ROOT / "requirements-termux.txt"
        if termux_req.exists() and _confirm("Also install Termux-specific requirements?"):
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(termux_req)], check=False)
    Branding.print_info(f"Running: {' '.join(pip_cmd)}")
    result = subprocess.run(pip_cmd)
    if result.returncode == 0:
        Branding.print_success("Dependencies installed successfully.")
    else:
        Branding.print_error("Dependency installation failed. Check the output above.")


def run_wizard() -> None:
    Branding.print_header()
    Branding.print_info("This wizard will create a .env configuration file for Kairo.")
    Branding.print_info("You will need:")
    Branding.print_info("  - A Discord bot token (discord.com/developers/applications)")
    Branding.print_info("  - Your Discord application's Client ID and Client Secret")
    print()
    if not _check_existing_env():
        print("\n  Setup cancelled.")
        return
    values: dict = {}
    print()
    Branding.print_section("Discord Credentials")
    Branding.print_info("Get these from: https://discord.com/developers/applications")
    print()
    values["BOT_TOKEN"] = _prompt("Bot Token", secret=True)
    values["CLIENT_ID"] = _prompt("Client ID")
    values["CLIENT_SECRET"] = _prompt("Client Secret", secret=True)
    values["BOT_PREFIX"] = _prompt("Command prefix", default="!")
    print()
    Branding.print_section("Development Settings")
    Branding.print_info("Optional: enter your development server's ID for instant slash command sync.")
    Branding.print_info("Leave empty for global sync (use in production).")
    values["DEV_GUILD_ID"] = _prompt("Dev Guild ID", default="", required=False)
    print()
    Branding.print_section("Database")
    values["DB_PATH"] = _prompt("Database file path", default="data/kairo.db")
    print()
    Branding.print_section("Logging")
    Branding.print_info("Levels: DEBUG, INFO, WARNING, ERROR")
    values["LOG_LEVEL"] = _prompt("Log level", default="INFO")
    print()
    Branding.print_section("API Server")
    Branding.print_info("The API server allows the web dashboard to communicate with the bot.")
    if _confirm("Configure API server?", default=False):
        values["API_HOST"] = _prompt("API host", default="127.0.0.1")
        values["API_PORT"] = _prompt("API port", default="8080")
        values["API_SECRET"] = _prompt("API secret key", secret=True)
    else:
        values["API_HOST"] = "127.0.0.1"
        values["API_PORT"] = "8080"
        values["API_SECRET"] = ""
    print()
    Branding.print_section("Dashboard")
    values["DASHBOARD_URL"] = _prompt("Dashboard public URL", default="http://localhost:5173")
    print()
    Branding.print_section("Runtime")
    enable_debug = _confirm("Enable debug mode? (Recommended: No for production)", default=False)
    values["DEBUG"] = "true" if enable_debug else "false"
    print()
    Branding.print_section("Writing Configuration")
    _write_env(values)
    print()
    Branding.print_section("Dependencies")
    _install_dependencies()
    print()
    if sys.stdout.isatty():
        print("=" * 70)
        print(f"{Colors.BOLD}{Colors.BRIGHT_GREEN}  + Setup complete!{Colors.RESET}")
        print()
        print(f"{Colors.BRIGHT_WHITE}  Start Kairo:{Colors.RESET}")
        print(f"    {Colors.CYAN}python src/run.py{Colors.RESET}")
        print()
        print(f"{Colors.BRIGHT_WHITE}  Start with the API server:{Colors.RESET}")
        print(f"    {Colors.CYAN}python src/run.py --with-api{Colors.RESET}")
        print()
        print(f"{Colors.BRIGHT_WHITE}  Documentation:{Colors.RESET}")
        print(f"    {Colors.CYAN}docs/getting-started.md{Colors.RESET}")
        print("=" * 70)
    else:
        print("=" * 60)
        print("  + Setup complete!")
        print()
        print("  Start Kairo:")
        print("    python src/run.py")
        print()
        print("  Start with the API server:")
        print("    python src/run.py --with-api")
        print()
        print("  Documentation:")
        print("    docs/getting-started.md")
        print("=" * 60)
    print()


if __name__ == "__main__":
    try:
        run_wizard()
    except KeyboardInterrupt:
        print("\n\n  Setup cancelled.")
        sys.exit(0)
