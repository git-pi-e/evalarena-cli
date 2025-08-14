"""Authentication management for EvalArena CLI."""

import getpass
from typing import Optional

import keyring
from rich.console import Console

from .config import get_config, save_config

console = Console()

# Keyring service name
SERVICE_NAME = "evalarena-cli"
USERNAME = "default"


def get_stored_token() -> Optional[str]:
    """Get stored authentication token from keyring or config."""
    config = get_config()
    
    # First try environment variable (highest priority)
    if config.token:
        return config.token
    
    # Then try keyring
    try:
        token = keyring.get_password(SERVICE_NAME, USERNAME)
        if token:
            return token
    except Exception:
        # Keyring might not be available
        pass
    
    return None


def store_token(token: str) -> bool:
    """Store authentication token in keyring."""
    try:
        keyring.set_password(SERVICE_NAME, USERNAME, token)
        return True
    except Exception as e:
        console.print(f"[yellow]Warning: Could not store token in keyring: {e}")
        console.print("[yellow]Token will only be available for this session.")
        return False


def remove_stored_token() -> bool:
    """Remove stored authentication token."""
    try:
        keyring.delete_password(SERVICE_NAME, USERNAME)
        return True
    except Exception:
        # Token might not exist or keyring not available
        return False


def prompt_for_token() -> Optional[str]:
    """Prompt user for authentication token."""
    console.print("\n[bold blue]EvalArena CLI Authentication[/bold blue]")
    console.print("Please enter your EvalArena API token.")
    console.print("You can get one from: https://evalarena.ai/account/api-keys")
    console.print()
    
    try:
        token = getpass.getpass("API Token (hidden): ").strip()
        if not token:
            console.print("[red]No token provided.")
            return None
        return token
    except KeyboardInterrupt:
        console.print("\n[yellow]Authentication cancelled.")
        return None


async def validate_token(token: str) -> tuple[bool, Optional[str]]:
    """Validate token by making a test API call."""
    from .http import create_client
    
    client = create_client()
    
    # Test with a simple API call
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = await client.get("/api/models/?limit=1", headers=headers)
        
        if response.status_code == 200:
            return True, None
        elif response.status_code == 401:
            return False, "Invalid or expired token"
        elif response.status_code == 403:
            return False, "Token does not have required permissions"
        else:
            return False, f"API returned {response.status_code}: {response.text}"
    
    except Exception as e:
        return False, f"Failed to validate token: {str(e)}"


def login() -> bool:
    """Interactive login flow."""
    console.print("[bold green]EvalArena CLI Login[/bold green]")
    
    # Check if token already exists
    existing_token = get_stored_token()
    if existing_token:
        console.print("[yellow]You are already logged in.")
        console.print("Use 'evalarena auth logout' to remove stored credentials.")
        return True
    
    # Prompt for new token
    token = prompt_for_token()
    if not token:
        return False
    
    # Validate token
    console.print("[dim]Validating token...")
    
    import asyncio
    is_valid, error_msg = asyncio.run(validate_token(token))
    
    if not is_valid:
        console.print(f"[red]Authentication failed: {error_msg}")
        return False
    
    # Store token
    if store_token(token):
        console.print("[green]✓ Token stored successfully in keyring.")
    else:
        console.print("[yellow]⚠ Token validated but could not be stored in keyring.")
        console.print("[yellow]You'll need to re-authenticate in future sessions.")
    
    console.print("[green]✓ Authentication successful!")
    return True


def logout() -> bool:
    """Logout and remove stored credentials."""
    console.print("[bold yellow]EvalArena CLI Logout[/bold yellow]")
    
    # Check if token exists
    existing_token = get_stored_token()
    if not existing_token:
        console.print("[yellow]You are not currently logged in.")
        return True
    
    # Remove token
    if remove_stored_token():
        console.print("[green]✓ Logged out successfully.")
    else:
        console.print("[yellow]⚠ Could not remove stored token from keyring.")
        console.print("[yellow]You may need to clear it manually.")
    
    return True


def get_auth_headers() -> dict[str, str]:
    """Get authentication headers for API requests."""
    token = get_stored_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}
