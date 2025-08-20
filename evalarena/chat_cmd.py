"""Commands for chatting with models and comparing responses."""

import asyncio
import json
import time
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

import httpx
import typer
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_config, update_config, reload_config
from .http import create_client, EvalArenaHTTPError
from .printers import print_error, print_info, print_success
from .completions import complete_model_type, complete_output_format, complete_chat_models
from .data_access import fetch_models

console = Console()


async def get_available_chat_models():
    """Get available chat models from the backend."""
    try:
        async with create_client() as client:
            response = await client.get("/api/chat/models/")
            response.raise_for_status()
            models_data = response.json()
            
            # Filter to get model names and IDs
            available_models = []
            for model in models_data:
                if isinstance(model, dict):
                    model_id = model.get('id', '')
                    model_name = model.get('name', model_id)
                    available_models.append({
                        'id': model_id,
                        'name': model_name,
                        'creator': model.get('creator', 'Unknown')
                    })
            
            return available_models
    except Exception as e:
        print_error(f"Failed to fetch available chat models: {e}")
        return []


async def stream_chat_response(
    client: httpx.AsyncClient,
    prompt: str,
    model_id: str,
    response_dict: Dict[str, str],
    progress_dict: Dict[str, str]
) -> None:
    """Stream chat response from a single model."""
    try:
        # Update progress
        progress_dict[model_id] = "⏳ Connecting..."
        
        payload = {
            "messages": [{"role": "user", "content": prompt}],
            "selectedModel": model_id
        }
        
        async with client.stream(
            "POST",
            "/api/chat/chat/",
            json=payload,
            timeout=httpx.Timeout(60.0)
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                error_msg = f"HTTP {response.status_code}: {error_text.decode('utf-8', errors='ignore')}"
                response_dict[model_id] = f"❌ Error: {error_msg}"
                progress_dict[model_id] = "❌ Failed"
                return
            
            # Update progress to streaming
            progress_dict[model_id] = "📡 Streaming..."
            response_dict[model_id] = ""
            
            # Process the stream
            accumulated_text = ""
            async for chunk in response.aiter_bytes():
                if chunk:
                    chunk_text = chunk.decode('utf-8', errors='ignore')
                    accumulated_text += chunk_text
                    response_dict[model_id] = accumulated_text
            
            # Mark as complete
            progress_dict[model_id] = "✅ Complete"
            
    except asyncio.TimeoutError:
        response_dict[model_id] = "❌ Timeout: Response took too long"
        progress_dict[model_id] = "⏰ Timeout"
    except Exception as e:
        response_dict[model_id] = f"❌ Error: {str(e)}"
        progress_dict[model_id] = "❌ Failed"


def create_live_display(
    models: List[Dict[str, str]], 
    responses: Dict[str, str], 
    progress: Dict[str, str]
) -> Table:
    """Create a live-updating display for multi-model responses."""
    
    # Create main table
    table = Table(
        title="🤖 Multi-Model Chat Comparison",
        show_header=True,
        header_style="bold blue",
        border_style="blue",
        expand=True
    )
    
    # Add columns for each model
    for model in models:
        model_name = model['name'][:20] + "..." if len(model['name']) > 20 else model['name']
        table.add_column(
            f"{model_name}\n({model['creator']})",
            style="white",
            no_wrap=False,
            vertical="top"
        )
    
    # Add progress row
    progress_row = []
    for model in models:
        status = progress.get(model['id'], "⏳ Waiting...")
        progress_row.append(Text(status, style="yellow" if "⏳" in status else "green" if "✅" in status else "red"))
    
    table.add_row(*progress_row)
    
    # Add separator
    separator_row = ["━" * 50 for _ in models]
    table.add_row(*separator_row)
    
    # Add response content
    response_row = []
    for model in models:
        response_text = responses.get(model['id'], "")
        
        if not response_text:
            content = Text("Waiting for response...", style="dim")
        elif response_text.startswith("❌"):
            content = Text(response_text, style="red")
        else:
            # Truncate very long responses for display
            display_text = response_text
            if len(display_text) > 500:
                display_text = display_text[:500] + "\n\n[... response truncated ...]"
            content = Text(display_text, style="white")
        
        response_row.append(content)
    
    table.add_row(*response_row)
    
    return table


def print_final_results(models: List[Dict[str, str]], responses: Dict[str, str]):
    """Print the final results in a clean format."""
    console.print("\n" + "="*80)
    console.print("[bold blue]🏁 Final Results[/bold blue]", style="bold")
    console.print("="*80)
    
    for i, model in enumerate(models, 1):
        model_name = model['name']
        creator = model['creator']
        response = responses.get(model['id'], "No response")
        
        # Create panel for each model's response
        panel = Panel(
            response,
            title=f"[bold]{i}. {model_name}[/bold] ([blue]{creator}[/blue])",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(panel)
        console.print()


async def chat_with_multiple_models(
    prompt: str,
    model_ids: List[str],
    show_progress: bool = True
) -> None:
    """Chat with multiple models simultaneously and display results."""
    
    # Get available models to map IDs to names
    available_models = await get_available_chat_models()
    if not available_models:
        print_error("Could not fetch available models")
        return
    
    # Create model lookup
    model_lookup = {m['id']: m for m in available_models}
    
    # Validate model IDs
    selected_models = []
    for model_id in model_ids:
        if model_id in model_lookup:
            selected_models.append(model_lookup[model_id])
        else:
            print_error(f"Model '{model_id}' not found in available models")
            return
    
    if not selected_models:
        print_error("No valid models selected")
        return
    
    print_info(f"Starting chat with {len(selected_models)} models:")
    for model in selected_models:
        console.print(f"  • {model['name']} ({model['creator']})")
    console.print()
    
    # Initialize response and progress tracking
    responses = {}
    progress_status = {}
    
    # Create HTTP client
    async with create_client() as client:
        
        # Create tasks for all models
        tasks = []
        for model in selected_models:
            task = stream_chat_response(
                client, prompt, model['id'], responses, progress_status
            )
            tasks.append(task)
        
        if show_progress:
            # Show live updates
            with Live(
                create_live_display(selected_models, responses, progress_status),
                refresh_per_second=2,
                console=console
            ) as live:
                
                # Start all requests concurrently
                await asyncio.gather(*tasks, return_exceptions=True)
                
                # Final update
                live.update(create_live_display(selected_models, responses, progress_status))
        else:
            # Just run without live display
            await asyncio.gather(*tasks, return_exceptions=True)
    
    # Print final results
    print_final_results(selected_models, responses)


def chat_command(
    prompt: Optional[str] = typer.Option(None, "--prompt", "-p", help="Prompt to send to the chat models"),
    models: Optional[str] = typer.Option(
        None,
        "--models", "-m",
        help="Comma-separated list of model IDs to compare (e.g., 'gpt-4o,claude-3-5-sonnet')",
        autocompletion=complete_chat_models,
    ),
    set_models: Optional[str] = typer.Option(
        None,
        "--set-models",
        help="Persist default chat models (comma-separated). Use --clear-models to remove.",
        autocompletion=complete_chat_models,
    ),
    clear_models: bool = typer.Option(
        False,
        "--clear-models",
        help="Clear default chat models from config"
    ),
    list_models: bool = typer.Option(
        False,
        "--list",
        help="List available chat models"
    ),
    no_progress: bool = typer.Option(
        False,
        "--no-progress",
        help="Disable live progress display"
    )
) -> None:
    """Chat with one or multiple models and compare their responses.
    
    Examples:
        evalarena chat "Explain quantum computing" --models "gpt-4o,claude-3-5-sonnet"
        evalarena chat "Write a Python function to sort a list" --models "gpt-4o"
        evalarena chat --list  # Show available models
    """
    
    if list_models:
        models_list = asyncio.run(get_available_chat_models())
        if not models_list:
            return
        
        table = Table(title="Available Chat Models", show_header=True, header_style="bold blue")
        table.add_column("Model ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Creator", style="blue")
        
        for model in models_list:
            table.add_row(model['id'], model['name'], model['creator'])
        
        console.print(table)
        return
    
    # Manage saved default chat models
    if set_models is not None:
        try:
            # Validate provided model IDs before saving
            if set_models.strip():
                requested_ids = [m.strip() for m in set_models.split(",") if m.strip()]
                available_models = asyncio.run(get_available_chat_models())
                available_ids = {m['id'] for m in available_models}
                invalid = [mid for mid in requested_ids if mid not in available_ids]
                
                if invalid:
                    print_error(f"Some model IDs are not available: {', '.join(invalid)}")
                    # Provide suggestions for nearby IDs (prefix match)
                    for bad in invalid:
                        prefix_matches = [mid for mid in available_ids if mid.startswith(bad[:4]) and mid != bad][:3]
                        if prefix_matches:
                            console.print(f"  Similar to '{bad}': [cyan]{', '.join(prefix_matches)}[/cyan]")
                    
                    print_info("Use 'evalarena chat --list' to see all available models")
                    raise typer.Exit(1)
            
            update_config("chat.default_models", set_models)
            reload_config()
            if set_models.strip():
                print_success(f"Set default chat models: {set_models}")
            else:
                print_success("Set default chat models to empty list")
        except typer.Exit:
            raise
        except Exception as e:
            print_error(f"Failed to set default chat models: {e}")
            raise typer.Exit(1)
        return
    if clear_models:
        try:
            update_config("chat.default_models", "")
            reload_config()
            print_success("Cleared default chat models")
        except Exception as e:
            print_error(f"Failed to clear default chat models: {e}")
            raise typer.Exit(1)
        return

    if list_models:
        models_list = asyncio.run(get_available_chat_models())
        if not models_list:
            return
        table = Table(title="Available Chat Models", show_header=True, header_style="bold blue")
        table.add_column("Model ID", style="cyan")
        table.add_column("Name", style="white")
        table.add_column("Creator", style="blue")
        for model in models_list:
            table.add_row(model['id'], model['name'], model['creator'])
        console.print(table)
        return

    if not prompt:
        print_error("Please provide a prompt using --prompt/-p")
        print_info("Example: evalarena chat --prompt 'Explain quantum computing'")
        return
    
    # Resolve models: CLI --models takes precedence over saved defaults
    config = get_config()
    resolved_models_csv = models if models else ",".join(config.chat.default_models) if config.chat.default_models else None
    if not resolved_models_csv:
        print_error("No chat models specified. Use --models or set defaults with --set-models.")
        print_info("Use 'evalarena chat --list' to see available models")
        return
    
    # Parse model IDs
    model_ids = [m.strip() for m in resolved_models_csv.split(",") if m.strip()]
    
    if not model_ids:
        print_error("No valid model IDs provided")
        return
    
    if len(model_ids) > 4:
        print_error("Maximum 4 models supported for comparison")
        return
    
    try:
        asyncio.run(chat_with_multiple_models(prompt, model_ids, not no_progress))
    except KeyboardInterrupt:
        print_info("\nChat interrupted by user")
    except Exception as e:
        print_error(f"Chat failed: {e}")
