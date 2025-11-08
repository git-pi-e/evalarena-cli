"""Commands for listing and filtering models."""

import asyncio
from typing import List, Optional

import typer
from rich.console import Console

from ..core.config import get_config
from ..core.data_access import fetch_models, get_all_benchmark_keys, ModelType
from ..core.http import EvalArenaHTTPError
from ..utils.printers import print_output, print_error, print_info, DEFAULT_COLUMNS, BENCHMARK_COLUMNS
from ..utils.utils import validate_benchmark_key
from ..utils.completions import (
    complete_model_type, complete_sort_order, complete_output_format,
    complete_evals_category_smart
)

console = Console()


def _validate_model_type(model_type: str) -> None:
    """Validate that the model type is valid."""
    valid_types = [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]
    if model_type not in valid_types:
        print_error(f"Invalid model type '{model_type}'. Must be one of: {', '.join(valid_types)}")
        raise typer.Exit(1)


def _validate_sort_order(order: str) -> None:
    """Validate that the sort order is valid."""
    if order not in ["asc", "desc"]:
        print_error("Order must be 'asc' or 'desc'")
        raise typer.Exit(1)


def _parse_columns_from_options(columns: Optional[str], evals: Optional[str],
                               model_type: str, config) -> List[str]:
    """Parse column list from command options."""
    if columns:
        return [col.strip() for col in columns.split(",")]
    elif evals:
        return _get_benchmark_columns(evals, model_type)
    else:
        return DEFAULT_COLUMNS.get(model_type, config.default_columns)


def _get_benchmark_columns(evals: str, model_type: str) -> List[str]:
    """Get benchmark columns based on evals category."""
    benchmark_cols = BENCHMARK_COLUMNS.get(model_type, {})
    if evals == "all":
        return ["name", "creator"] + benchmark_cols.get("all", [])
    elif evals in benchmark_cols:
        return ["name", "creator"] + benchmark_cols[evals]
    else:
        valid_categories = list(benchmark_cols.keys())
        print_error(f"Invalid evals category '{evals}'. Valid categories for {model_type} models: {', '.join(valid_categories)}")
        raise typer.Exit(1)


def _get_available_keys_from_models(models: List) -> set:
    """Extract all available field keys from a list of models."""
    available_keys = set()
    for model in models:
        available_keys.update(model.get_all_benchmarks().keys())
        available_keys.update(["name", "creator", "active_params_in_billion", "release_date", "description"])

        # Add pricing and token fields
        pricing = model.get_pricing_info()
        for key, value in pricing.items():
            if value is not None:
                available_keys.add(key)

        token_limits = model.get_token_limits()
        for key, value in token_limits.items():
            if value is not None:
                available_keys.add(key)

    return available_keys


def _validate_columns_against_available(column_list: List[str], available_keys: set) -> List[str]:
    """Validate column list against available keys and return corrected list."""
    validated_columns = []
    for col in column_list:
        try:
            if col in available_keys or col in ["name", "creator"]:
                validated_columns.append(col)
            else:
                # Try to validate/correct the column name
                corrected = validate_benchmark_key(col, list(available_keys))
                validated_columns.append(corrected)
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)

    return validated_columns


def _fetch_models_with_status(model_type: str, sort_by: str, order: str,
                             page: Optional[int], limit: Optional[int],
                             no_cache: bool):
    """Fetch models with a loading status message."""
    with console.status(f"Fetching {model_type} models..."):
        return asyncio.run(fetch_models(
            model_type=model_type,
            sort_by=sort_by,
            order=order,
            page=page,
            limit=limit,
            bypass_cache=no_cache
        ))


def _create_output_title(model_type: str, limit: Optional[int]) -> str:
    """Create a descriptive title for the output."""
    title = f"{model_type.title()} Models"
    if limit:
        title += f" (limit: {limit})"
    return title


def setup_models_commands(app: typer.Typer) -> None:
    """Setup models command handlers."""

    @app.command("list")
    def list_models(
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to list (all, small, vlm, chat)",
            autocompletion=complete_model_type
        ),
        sort_by: str = typer.Option(
            "name",
            "--sort-by",
            help="Field to sort by"
        ),
        order: str = typer.Option(
            "asc",
            "--order",
            help="Sort order (asc, desc)",
            autocompletion=complete_sort_order
        ),
        page: Optional[int] = typer.Option(
            None,
            "--page",
            help="Page number for pagination"
        ),
        limit: Optional[int] = typer.Option(
            None,
            "--limit",
            help="Number of models to show"
        ),
        columns: Optional[str] = typer.Option(
            None,
            "--columns",
            help="Comma-separated list of columns to display"
        ),
        evals: Optional[str] = typer.Option(
            None,
            "--evals",
            help="Show evaluation benchmarks. Use 'all' or specify category: math, coding, knowledge, multimodal, document, video, agent",
            autocompletion=complete_evals_category_smart
        ),
        format_type: str = typer.Option(
            None,
            "--format",
            help="Output format (table, json, yaml)",
            autocompletion=complete_output_format
        ),
        no_cache: bool = typer.Option(
            False,
            "--no-cache",
            help="Bypass cache and fetch fresh data"
        ),
    ) -> None:
        """List models with filtering and sorting options."""

        # Validate inputs
        _validate_model_type(model_type)
        _validate_sort_order(order)

        config = get_config()

        # Determine output format
        output_format = format_type or config.output_format

        # Parse columns
        column_list = _parse_columns_from_options(columns, evals, model_type, config)

        try:
            # Fetch models
            models = _fetch_models_with_status(
                model_type, sort_by, order, page, limit, no_cache
            )

            if not models:
                print_info("No models found.")
                return

            # Validate columns against available data (skip validation for --evals since they're pre-validated)
            if output_format == "table" and not evals:
                available_keys = _get_available_keys_from_models(models)
                column_list = _validate_columns_against_available(column_list, available_keys)

            # Print results
            title = _create_output_title(model_type, limit)
            print_output(models, output_format, columns=column_list, title=title)

        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to fetch models: {e}")
            raise typer.Exit(1)

    @app.command("columns")
    def list_columns(
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to analyze (all, small, vlm, chat)",
            autocompletion=complete_model_type
        ),
    ) -> None:
        """List available columns for the specified model type."""

        _validate_model_type(model_type)

        try:
            with console.status(f"Analyzing {model_type} models..."):
                benchmark_keys = asyncio.run(get_all_benchmark_keys(model_type))

            # Add standard fields
            standard_fields = [
                "name",
                "creator",
                "active_params_in_billion",
                "input_price_per_1M_tokens_USD",
                "output_price_per_1M_tokens_USD",
                "max_input_tokens",
                "max_output_tokens"
            ]

            all_columns = standard_fields + benchmark_keys

            console.print(f"[bold blue]Available columns for {model_type} models:[/bold blue]")
            console.print()

            console.print("[bold]Standard Fields:[/bold]")
            for field in standard_fields:
                console.print(f"  • {field}")

            console.print()
            console.print("[bold]Benchmark Categories (use with --evals):[/bold]")
            benchmark_categories = BENCHMARK_COLUMNS.get(model_type, {})
            for category, fields in benchmark_categories.items():
                console.print(f"  • [cyan]{category}[/cyan]: {', '.join(fields[:3])}{'...' if len(fields) > 3 else ''}")

            console.print()
            console.print(f"[bold]Usage Examples:[/bold]")
            console.print(f"  evalarena models list --type {model_type}  # Model info")
            console.print(f"  evalarena models list --type {model_type} --evals all  # All benchmarks")
            for category in list(benchmark_categories.keys())[:2]:  # Show first 2 categories
                console.print(f"  evalarena models list --type {model_type} --evals {category}  # {category.title()} benchmarks")

            console.print()
            console.print(f"[dim]Total: {len(all_columns)} columns available[/dim]")

        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Failed to analyze columns: {e}")
            raise typer.Exit(1)

    @app.command("search")
    def search_models(
        query: str = typer.Argument(help="Search query (model name)"),
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to search (all, small, vlm, chat)"
        ),
        fuzzy: bool = typer.Option(
            True,
            "--fuzzy/--exact",
            help="Enable fuzzy matching"
        ),
        columns: Optional[str] = typer.Option(
            None,
            "--columns",
            help="Comma-separated list of columns to display"
        ),
        format_type: str = typer.Option(
            None,
            "--format",
            help="Output format (table, json, yaml)"
        ),
    ) -> None:
        """Search for models by name."""

        from ..core.data_access import search_models_by_name

        _validate_model_type(model_type)

        config = get_config()

        # Determine output format
        output_format = format_type or config.output_format

        # Parse columns
        if columns:
            column_list = [col.strip() for col in columns.split(",")]
        else:
            column_list = DEFAULT_COLUMNS.get(model_type, config.default_columns)

        try:
            with console.status(f"Searching for '{query}' in {model_type} models..."):
                models = asyncio.run(search_models_by_name(
                    query,
                    model_type=model_type,
                    fuzzy=fuzzy
                ))

            if not models:
                print_info(f"No models found matching '{query}'.")
                return

            # Print results
            title = f"Search Results for '{query}'"
            print_output(
                models,
                output_format,
                columns=column_list,
                title=title
            )

        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Search failed: {e}")
            raise typer.Exit(1)


