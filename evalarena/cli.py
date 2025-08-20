"""Main CLI application for EvalArena."""

import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.traceback import install

from . import __version__
from .core.auth import login, logout
from .core.config import get_config, update_config, reload_config
from .core.http import health_check, clear_cache, get_cache_stats
from .utils.printers import print_error, print_success, print_info

# Install rich traceback handler
install(show_locals=True)

# Create console
console = Console()

# Create main app
app = typer.Typer(
    name="evalarena",
    help="EvalArena CLI - Compare and analyze AI model benchmarks",
    add_completion=True,
)

# Create subcommands
auth_app = typer.Typer(name="auth", help="Authentication commands")
config_app = typer.Typer(name="config", help="Configuration management")
models_app = typer.Typer(name="models", help="List and search models")
model_app = typer.Typer(name="model", help="Show model details")
charts_app = typer.Typer(name="charts", help="Generate charts")

# Add subcommands to main app
app.add_typer(auth_app)
app.add_typer(config_app)
app.add_typer(models_app)
app.add_typer(model_app)
app.add_typer(charts_app)


# Global options
def version_callback(value: bool) -> None:
    """Show version and exit."""
    if value:
        console.print(f"evalarena {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit"
    ),
    base_url: Optional[str] = typer.Option(
        None,
        "--base-url",
        help="Override base URL for API requests"
    ),
    timeout: Optional[int] = typer.Option(
        None,
        "--timeout",
        help="Override request timeout in seconds"
    ),
    no_cache: bool = typer.Option(
        False,
        "--no-cache",
        help="Disable HTTP caching"
    ),
    no_color: bool = typer.Option(
        False,
        "--no-color",
        help="Disable colored output"
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Enable verbose output"
    ),
) -> None:
    """EvalArena CLI - Compare and analyze AI model benchmarks."""
    # Apply global options
    config = get_config()
    
    if base_url:
        config.base_url = base_url
    if timeout:
        config.timeout_s = timeout
    if no_cache:
        config.cache_enabled = False
    if no_color:
        config.no_color = True
        console.no_color = True


# Auth commands
@auth_app.command()
def auth_login() -> None:
    """Login with API token."""
    try:
        success = login()
        if not success:
            raise typer.Exit(1)
    except KeyboardInterrupt:
        print_info("Authentication cancelled.")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Login failed: {e}")
        raise typer.Exit(1)


@auth_app.command()
def auth_logout() -> None:
    """Logout and remove stored credentials."""
    try:
        success = logout()
        if not success:
            raise typer.Exit(1)
    except Exception as e:
        print_error(f"Logout failed: {e}")
        raise typer.Exit(1)


# Config commands
@config_app.command()
def config_show() -> None:
    """Show current configuration."""
    config = reload_config()
    
    console.print("[bold blue]EvalArena CLI Configuration[/bold blue]")
    console.print()
    console.print(f"Base URL: [cyan]{config.base_url}[/cyan]")
    console.print(f"Timeout: [cyan]{config.timeout_s}s[/cyan]")
    console.print(f"Output Format: [cyan]{config.output_format}[/cyan]")
    console.print(f"No Color: [cyan]{config.no_color}[/cyan]")
    console.print(f"Cache Enabled: [cyan]{config.cache_enabled}[/cyan]")
    console.print(f"Cache TTL: [cyan]{config.cache_ttl_seconds}s[/cyan]")
    console.print()
    console.print(f"Default Columns: [cyan]{', '.join(config.default_columns)}[/cyan]")
    console.print()
    console.print("[bold blue]Chart Settings[/bold blue]")
    console.print(f"Width: [cyan]{config.chart.width}[/cyan]")
    console.print(f"Height: [cyan]{config.chart.height}[/cyan]")
    console.print(f"Normalize: [cyan]{config.chart.normalize}[/cyan]")
    console.print()
    console.print("[bold blue]Chat Settings[/bold blue]")
    default_chat_models = config.chat.default_models or []
    console.print(f"Default Models: [cyan]{', '.join(default_chat_models) if default_chat_models else '(none)'}[/cyan]")
    
    # Show cache stats
    try:
        cache_stats = get_cache_stats()
        console.print()
        console.print("[bold blue]Cache Statistics[/bold blue]")
        console.print(f"Entries: [cyan]{cache_stats['size']}[/cyan]")
        console.print(f"Directory: [cyan]{cache_stats['cache_dir']}[/cyan]")
    except Exception:
        pass


@config_app.command()
def config_set(
    key: str = typer.Argument(help="Configuration key to set"),
    value: str = typer.Argument(help="Value to set"),
) -> None:
    """Set configuration value."""
    try:
        update_config(key, value)
        print_success(f"Set {key} = {value}")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Failed to update config: {e}")
        raise typer.Exit(1)


# Health check command
@app.command()
def ping() -> None:
    """Check API connectivity."""
    console.print("[dim]Checking API connectivity...[/dim]")
    
    try:
        is_healthy, message = asyncio.run(health_check())
        if is_healthy:
            print_success(message)
        else:
            print_error(message)
            raise typer.Exit(1)
    except Exception as e:
        print_error(f"Health check failed: {e}")
        raise typer.Exit(1)


# Cache management commands
@app.command()
def clear_cache_cmd() -> None:
    """Clear HTTP cache."""
    try:
        count = clear_cache()
        print_success(f"Cleared {count} cache entries")
    except Exception as e:
        print_error(f"Failed to clear cache: {e}")
        raise typer.Exit(1)


# Import command modules
try:
    from .commands.models_cmd import setup_models_commands
    from .commands.model_cmd import setup_model_commands
    from .commands.compare_cmd import compare_models
    from .commands.charts_cmd import setup_charts_commands
    from .commands.chat_cmd import chat_command
    
    # Setup command handlers
    setup_models_commands(models_app)
    setup_model_commands(model_app)
    app.command(name="compare")(compare_models)
    app.command(name="chat")(chat_command)
    setup_charts_commands(charts_app)
    
except ImportError as e:
    # Commands not yet implemented
    console.print(f"[yellow]Warning: Some commands not available: {e}[/yellow]")


if __name__ == "__main__":
    app()
