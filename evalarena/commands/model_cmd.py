"""Commands for showing individual model details."""

import asyncio
from typing import Optional

import typer
from rich.console import Console

from ..core.config import get_config
from ..core.data_access import fetch_model_by_id, search_models_by_name, ModelType
from ..core.http import EvalArenaHTTPError
from ..utils.printers import print_model_details, print_output, print_error, print_info
from ..utils.completions import complete_model_type, complete_output_format

console = Console()


def setup_model_commands(app: typer.Typer) -> None:
    """Setup model command handlers."""
    
    @app.command("show")
    def show_model(
        model_identifier: str = typer.Argument(
            help="Model ID, name, or search term"
        ),
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to search in (all, small, vlm, chat)",
            autocompletion=complete_model_type
        ),
        format_type: str = typer.Option(
            None,
            "--format",
            help="Output format (table, json, yaml)",
            autocompletion=complete_output_format
        ),
    ) -> None:
        """Show detailed information about a specific model."""
        
        # Validate model type
        valid_types = [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]
        if model_type not in valid_types:
            print_error(f"Invalid model type '{model_type}'. Must be one of: {', '.join(valid_types)}")
            raise typer.Exit(1)
        
        config = get_config()
        output_format = format_type or config.output_format
        
        try:
            model = None
            
            # First try to fetch by ID if it looks like an ObjectId
            if len(model_identifier) == 24 and all(c in '0123456789abcdef' for c in model_identifier):
                with console.status(f"Fetching model by ID..."):
                    model = asyncio.run(fetch_model_by_id(model_identifier, model_type))
            
            # If not found by ID, search by name
            if model is None:
                with console.status(f"Searching for model '{model_identifier}'..."):
                    matches = asyncio.run(search_models_by_name(
                        model_identifier,
                        model_type=model_type,
                        fuzzy=False
                    ))
                
                if matches:
                    if len(matches) == 1:
                        model = matches[0]
                    else:
                        # Multiple exact matches, show them
                        print_error(f"Multiple models match '{model_identifier}':")
                        for match in matches:
                            console.print(f"  • {match.name} (ID: {match.id})")
                        raise typer.Exit(1)
                else:
                    # Try fuzzy search
                    matches = asyncio.run(search_models_by_name(
                        model_identifier,
                        model_type=model_type,
                        fuzzy=True
                    ))
                    
                    if matches:
                        if len(matches) == 1:
                            model = matches[0]
                            print_info(f"Found similar model: {model.name}")
                        else:
                            print_error(f"No exact match found for '{model_identifier}'. Similar models:")
                            for match in matches[:5]:
                                console.print(f"  • {match.name}")
                            raise typer.Exit(1)
            
            if model is None:
                print_error(f"Model not found: {model_identifier}")
                raise typer.Exit(1)
            
            # Output the model details
            if output_format == "table":
                print_model_details(model)
            else:
                print_output(model, output_format)
        
        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to fetch model: {e}")
            raise typer.Exit(1)
    
    @app.command("info")
    def model_info(
        model_identifier: str = typer.Argument(
            help="Model ID, name, or search term"
        ),
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to search in (all, small, vlm, chat)"
        ),
    ) -> None:
        """Show quick model information (alias for 'show')."""
        # This is just an alias for show with table format
        show_model(model_identifier, model_type, "table")
