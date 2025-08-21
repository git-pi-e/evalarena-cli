"""Commands for comparing models client-side."""

import asyncio
from typing import List, Optional

import typer
from rich.console import Console

from ..core.config import get_config
from ..core.data_access import ModelType
from ..core.http import EvalArenaHTTPError
from ..data.model_schemas import FullModel
from ..utils.printers import print_comparison_table, print_output, print_error, print_info
from ..utils.utils import resolve_model_names
from ..utils.completions import complete_model_type, complete_output_format, complete_diff_mode, complete_model_names

console = Console()


def compare_models(
        model_a: str = typer.Argument(help="First model to compare", autocompletion=complete_model_names),
        model_b: str = typer.Argument(help="Second model to compare", autocompletion=complete_model_names),
        additional_models: Optional[List[str]] = typer.Argument(
            None,
            help="Additional models to compare",
            autocompletion=complete_model_names
        ),
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to search in (all, small, vlm, chat)",
            autocompletion=complete_model_type
        ),
        columns: Optional[str] = typer.Option(
            None,
            "--columns",
            help="Comma-separated list of benchmarks to compare"
        ),
        diff: str = typer.Option(
            "none",
            "--diff",
            help="Show difference calculation (none, absolute, percent)",
            autocompletion=complete_diff_mode
        ),
        format_type: str = typer.Option(
            None,
            "--format",
            help="Output format (table, json, yaml)",
            autocompletion=complete_output_format
        ),
    ) -> None:
        """Compare multiple models side-by-side."""
        
        # Validate model type
        valid_types = [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]
        if model_type not in valid_types:
            print_error(f"Invalid model type '{model_type}'. Must be one of: {', '.join(valid_types)}")
            raise typer.Exit(1)
        
        # Validate diff mode
        valid_diff_modes = ["none", "absolute", "percent"]
        if diff not in valid_diff_modes:
            print_error(f"Invalid diff mode '{diff}'. Must be one of: {', '.join(valid_diff_modes)}")
            raise typer.Exit(1)
        
        config = get_config()
        output_format = format_type or config.output_format
        
        # Collect all model names
        all_model_names = [model_a, model_b]
        if additional_models:
            all_model_names.extend(additional_models)
        
        # Parse columns if specified
        column_list = None
        if columns:
            column_list = [col.strip() for col in columns.split(",")]
        
        try:
            # Resolve model names to model objects
            with console.status("Resolving model names..."):
                models = asyncio.run(resolve_model_names(all_model_names, model_type))
            
            if len(models) < 2:
                print_error("Need at least 2 models for comparison.")
                raise typer.Exit(1)
            
            print_info(f"Comparing {len(models)} models:")
            for model in models:
                console.print(f"  • {model.name}")
            console.print()
            
            # Perform comparison
            if output_format == "table":
                print_comparison_table(
                    models=models,
                    columns=column_list,
                    diff_mode=diff
                )
            else:
                # For JSON/YAML, output structured comparison data
                comparison_data = create_comparison_data(models, column_list, diff)
                print_output(comparison_data, output_format)
        
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Comparison failed: {e}")
            raise typer.Exit(1)


def create_comparison_data(
    models: List[FullModel],
    columns: Optional[List[str]] = None,
    diff_mode: str = "none"
) -> dict:
    """Create structured comparison data for JSON/YAML output."""
    
    # Get all available benchmarks if columns not specified
    if columns is None:
        all_benchmarks = set()
        for model in models:
            all_benchmarks.update(model.get_all_benchmarks().keys())
        columns = sorted(list(all_benchmarks))
    
    comparison = {
        "models": [],
        "metrics": {},
        "summary": {
            "model_count": len(models),
            "metrics_compared": len(columns),
            "diff_mode": diff_mode
        }
    }
    
    # Add model info
    for model in models:
        model_info = {
            "name": model.name,
            "creator": model.creator,
            "id": model.id,
            "benchmarks": {}
        }
        
        # Add benchmark scores
        for column in columns:
            value = model.get_benchmark_value(column)
            model_info["benchmarks"][column] = value
        
        comparison["models"].append(model_info)
    
    # Add metric comparisons
    for column in columns:
        values = []
        for model in models:
            value = model.get_benchmark_value(column)
            values.append(value)
        
        # Calculate statistics
        numeric_values = [v for v in values if v is not None]
        if numeric_values:
            metric_stats = {
                "values": dict(zip([m.name for m in models], values)),
                "statistics": {
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "mean": sum(numeric_values) / len(numeric_values),
                    "range": max(numeric_values) - min(numeric_values)
                }
            }
            
            # Add diff calculation for 2-model comparison
            if len(models) == 2 and diff_mode != "none" and len(numeric_values) == 2:
                val1, val2 = numeric_values[0], numeric_values[1]
                if diff_mode == "absolute":
                    metric_stats["diff"] = {
                        "absolute": val2 - val1,
                        "description": f"{models[1].name} vs {models[0].name}"
                    }
                elif diff_mode == "percent":
                    if val1 != 0:
                        metric_stats["diff"] = {
                            "percent": ((val2 - val1) / val1) * 100,
                            "description": f"{models[1].name} vs {models[0].name}"
                        }
            
            comparison["metrics"][column] = metric_stats
    
    return comparison
