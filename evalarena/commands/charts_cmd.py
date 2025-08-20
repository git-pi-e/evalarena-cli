"""Commands for generating terminal charts."""

import asyncio
from typing import List, Optional, Tuple

import plotext as plt
import typer
from rich.console import Console
from rich.table import Table

from ..core.config import get_config
from ..core.data_access import fetch_models, ModelType
from ..core.http import EvalArenaHTTPError
from ..utils.printers import print_error, print_info, format_number
from ..utils.utils import resolve_model_names, normalize_values, compute_pareto_frontier, clean_model_name
from ..utils.completions import complete_model_type, complete_normalize_mode, complete_common_benchmarks

console = Console()


# Creator color mapping based on frontend colors.js
# Using Rich color names that best match the original RGBA values
CREATOR_COLORS = {
    "OpenAI": "white",               # rgba(255, 255, 255, 0.8) - white
    "Google": "green",               # rgba(52, 168, 83, 0.8) - green
    "DeepSeek": "blue",              # rgba(77,107,255,0.8) - blue
    "Meta": "bright_blue",           # rgba(24, 119, 242, 0.8) - bright blue
    "Qwen": "magenta",               # rgba(101,73,243,0.8) - purple/magenta
    "Anthropic": "yellow",           # rgba(213,164,128,0.8) - tan/yellow
    "XAI": "bright_black",           # rgba(60, 57, 57, 0.8) - dark gray
    "Microsoft": "red",              # rgba(242,79,41,255) - orange/red
    "LG Research": "red",            # rgb(165 0 52) - dark red
    "MistralAI": "yellow",           # rgba(255,217,0,255) - yellow
    "Amazon": "bright_yellow",       # rgb(255 153 0) - orange
    "Tencent Hunyuan": "cyan",       # rgb(124 199 237) - light blue
    "Bytedance": "bright_cyan",      # rgba(0,200,210,255) - cyan
    "Moonshot AI": "bright_blue",    # rgb(2,122,255) - blue
    "OpenGVLab": "blue",             # rgb(60, 90, 155) - dark blue
    "Xiaomi": "bright_red",          # rgba(255,105,0,255) - orange
    "MiniMax": "bright_magenta",     # rgb(240 61 93) - pink/red
    "Baidu": "blue",                 # rgb(46,47,143) - dark blue
    "ZhipuAI": "bright_magenta",     # rgba(124,46,154,255) - purple
    "Huawei": "red",                 # rgba(207,10,44,255) - red
}


def get_creator_from_model_name(model_name: str) -> str:
    """Determine the creator from model name based on keywords (matches frontend colors.js)."""
    lower = model_name.lower()
    
    # Use regex pattern for OpenAI models (matches frontend exactly)
    import re
    if re.search(r'(o[134]|gpt|openai)', lower):
        return 'OpenAI'
    if 'gemini' in lower or 'gemma' in lower:
        return 'Google'
    if 'deepseek' in lower:
        return 'DeepSeek'
    if 'llama' in lower:
        return 'Meta'
    if 'qwen' in lower or 'qwq' in lower:
        return 'Qwen'
    if 'claude' in lower:
        return 'Anthropic'
    if 'grok' in lower:
        return 'XAI'
    if 'phi' in lower:
        return 'Microsoft'
    if 'exaone' in lower:
        return 'LG Research'
    if 'mistral' in lower or 'pixtral' in lower:
        return 'MistralAI'
    if 'nova' in lower:
        return 'Amazon'
    if 'hunyuan' in lower:
        return 'Tencent Hunyuan'
    if 'seed' in lower:
        return 'Bytedance'
    if 'kimi' in lower:
        return 'Moonshot AI'
    if 'intern' in lower:
        return 'OpenGVLab'
    if 'mimo' in lower:
        return 'Xiaomi'
    if 'minimax' in lower:
        return 'MiniMax'
    if 'ernie' in lower:
        return 'Baidu'
    if 'glm' in lower:
        return 'ZhipuAI'
    if 'pangu' in lower:
        return 'Huawei'
    
    return 'Unknown'


def get_color_for_model(model_name: str) -> str:
    """Get plotext color for a model based on its creator."""
    creator = get_creator_from_model_name(model_name)
    return CREATOR_COLORS.get(creator, 'white')


def generate_horizontal_bar_chart(models, values, metric, normalize):
    """Generate a horizontal ASCII bar chart."""
    
    # Use consistent bar pattern - solid blocks for clean appearance
    BAR_PATTERN = '▬'
    
    # Calculate display parameters
    max_name_length = min(40, max(len(clean_model_name(m.name)) for m in models))  # Increased from 25 to 40
    max_bar_length = 50  # Maximum bar length in characters
    max_value = max(values) if values else 1
    
    # Title
    title = f"{metric.replace('_', ' ').title()} Scores"
    if normalize != "none":
        title += f" ({normalize} normalized)"
    
    console.print(f"\n[bold blue]{title}[/bold blue]\n")
    
    # Generate bars
    for i, (model, value) in enumerate(zip(models, values)):
        # Get model name and truncate if needed
        name = clean_model_name(model.name)
        if len(name) > max_name_length:
            name = name[:max_name_length-3] + "..."
        
        # Pad name to align bars
        padded_name = name.ljust(max_name_length)
        
        # Calculate bar length
        if max_value > 0:
            bar_length = int((value / max_value) * max_bar_length)
        else:
            bar_length = 0
        
        # Get creator and color
        creator = get_creator_from_model_name(model.name)
        color = CREATOR_COLORS.get(creator, 'white')
        
        # Create bar with color - consistent pattern for all
        bar = BAR_PATTERN * max(1, bar_length)  # Ensure at least 1 char for non-zero values
        colored_bar = f"[{color}]{bar}[/{color}]"
        
        # Format value
        if isinstance(value, float):
            value_str = f"{value:.1f}"
        else:
            value_str = str(value)
        
        # Print the bar line
        console.print(f"{padded_name} {colored_bar} {value_str}")
    
    console.print()  # Add spacing after chart


def print_creator_legend(models):
    """Print a legend showing the creator color coding."""
    # Get unique creators in the chart
    creators_in_chart = set()
    for model in models:
        creator = get_creator_from_model_name(model.name)
        if creator != 'Unknown':
            creators_in_chart.add(creator)
    
    if creators_in_chart:
        console.print("\n[bold]Model Creator Colors:[/bold]")
        for creator in sorted(creators_in_chart):
            color = CREATOR_COLORS.get(creator, 'white')
            console.print(f"  [{color}]▬[/{color}] {creator}")
        console.print()


def calculate_blended_cost(model) -> Optional[float]:
    """Calculate blended cost assuming 3:1 input:output token ratio."""
    try:
        input_price = model.input_price_per_1M_tokens_USD
        output_price = model.output_price_per_1M_tokens_USD
        
        if input_price is not None and output_price is not None:
            # Blended cost = (3 * input_price + 1 * output_price) / 4
            # This assumes 3 input tokens per 1 output token
            blended = (3 * input_price + output_price) / 4
            return blended
        elif input_price is not None:
            # If only input price available, use it
            return input_price
        elif output_price is not None:
            # If only output price available, use it (less ideal)
            return output_price
        else:
            return None
    except (TypeError, AttributeError):
        return None


def setup_charts_commands(app: typer.Typer) -> None:
    """Setup chart command handlers."""
    
    @app.command("bar")
    def bar_chart(
        metric: str = typer.Argument(
            "mmlu",
            help="Benchmark metric to chart (e.g., mmlu, humaneval)",
            autocompletion=complete_common_benchmarks
        ),
        models: Optional[str] = typer.Option(
            None,
            "--models",
            help="Comma-separated list of model names to include"
        ),
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to analyze (all, small, vlm, chat)",
            autocompletion=complete_model_type
        ),
        normalize: str = typer.Option(
            "none",
            "--normalize",
            help="Normalization method (none, zscore, minmax)",
            autocompletion=complete_normalize_mode
        ),
        top: Optional[int] = typer.Option(
            None,
            "--top",
            help="Show only top N models by first metric"
        ),
        width: Optional[int] = typer.Option(
            80,
            "--width",
            help="Chart width in characters"
        ),
        height: Optional[int] = typer.Option(
            15,
            "--height",
            help="Chart height in characters"
        ),
    ) -> None:
        """Generate bar chart comparing models on a single benchmark metric."""
        
        # Validate inputs
        valid_types = [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]
        if model_type not in valid_types:
            print_error(f"Invalid model type '{model_type}'. Must be one of: {', '.join(valid_types)}")
            raise typer.Exit(1)
        
        valid_normalize = ["none", "zscore", "minmax"]
        if normalize not in valid_normalize:
            print_error(f"Invalid normalize method '{normalize}'. Must be one of: {', '.join(valid_normalize)}")
            raise typer.Exit(1)
        
        config = get_config()
        chart_width = width or config.chart.width
        chart_height = height or config.chart.height
        
        try:
            # Get models to chart
            if models:
                # Use specific models
                model_names = [m.strip() for m in models.split(",")]
                with console.status("Resolving model names..."):
                    model_list = asyncio.run(resolve_model_names(model_names, model_type))
            else:
                # Use all models of the specified type
                with console.status(f"Fetching {model_type} models..."):
                    model_list = asyncio.run(fetch_models(model_type))
                
                # Filter to top N if specified
                if top:
                    # Sort by the specified metric (descending)
                    model_list = sorted(
                        model_list,
                        key=lambda m: m.get_benchmark_value(metric) or 0,
                        reverse=True
                    )[:top]
            
            if not model_list:
                print_error("No models found for charting.")
                raise typer.Exit(1)
            
            # Generate chart
            generate_bar_chart(
                model_list,
                [metric],  # Pass as single-item list for compatibility
                normalize,
                chart_width,
                chart_height
            )
        
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Chart generation failed: {e}")
            raise typer.Exit(1)
    
    @app.command("pareto")
    def pareto_chart(
        metric: str = typer.Argument(
            help="Quality metric to maximize (e.g., mmlu, humaneval)",
            autocompletion=complete_common_benchmarks
        ),
        cost: Optional[str] = typer.Argument(
            None,
            help="Cost metric to minimize. If not specified, uses blended cost (3:1 input:output ratio)"
        ),
        model_type: str = typer.Option(
            "all",
            "--type",
            help="Type of models to analyze (all, small, vlm, chat)",
            autocompletion=complete_model_type
        ),
        width: Optional[int] = typer.Option(
            None,
            "--width",
            help="Chart width in characters"
        ),
        height: Optional[int] = typer.Option(
            None,
            "--height",
            help="Chart height in characters"
        ),
        table: bool = typer.Option(
            False,
            "--table",
            help="Also show Pareto frontier table"
        ),
    ) -> None:
        """Generate Pareto frontier chart showing cost vs quality trade-offs."""
        
        # Validate inputs
        valid_types = [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]
        if model_type not in valid_types:
            print_error(f"Invalid model type '{model_type}'. Must be one of: {', '.join(valid_types)}")
            raise typer.Exit(1)
        
        config = get_config()
        chart_width = width or config.chart.width
        chart_height = height or config.chart.height
        
        try:
            # Fetch models
            with console.status(f"Fetching {model_type} models..."):
                model_list = asyncio.run(fetch_models(model_type))
            
            if not model_list:
                print_error("No models found for analysis.")
                raise typer.Exit(1)
            
            # Determine cost metric
            cost_metric = cost
            cost_label = cost
            use_blended_cost = False
            
            if cost is None:
                # Use blended cost as default
                cost_metric = "blended_cost"
                cost_label = "Blended Cost (3:1 Input:Output)"
                use_blended_cost = True
                print_info("Using default blended cost metric (3:1 input:output ratio)")
            
            # Generate Pareto chart
            generate_pareto_chart(
                model_list,
                metric,
                cost_metric,
                chart_width,
                chart_height,
                show_table=table,
                cost_label=cost_label,
                use_blended_cost=use_blended_cost
            )
        
        except ValueError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except EvalArenaHTTPError as e:
            print_error(str(e))
            raise typer.Exit(1)
        except Exception as e:
            print_error(f"Chart generation failed: {e}")
            raise typer.Exit(1)


def generate_bar_chart(
    models: List,
    columns: List[str],
    normalize: str,
    width: int,
    height: int
) -> None:
    """Generate and display bar chart for a single metric."""
    
    # Since we now only support single metrics, extract the metric
    metric = columns[0]
    
    # Create list of (model, value) pairs and filter out None/0 values
    model_value_pairs = []
    for model in models:
        value = model.get_benchmark_value(metric)
        if value is not None and value > 0:
            model_value_pairs.append((model, value))
    
    # Sort by value in descending order
    model_value_pairs.sort(key=lambda x: x[1], reverse=True)
    
    if not model_value_pairs:
        print_error(f"No models found with valid data for metric '{metric}'")
        return
    
    # Extract sorted models and values
    sorted_models = [pair[0] for pair in model_value_pairs]
    sorted_values = [pair[1] for pair in model_value_pairs]
    
    # Normalize if requested
    if normalize != "none":
        sorted_values = normalize_values(sorted_values, normalize)
    
    # Create horizontal ASCII bar chart
    generate_horizontal_bar_chart(
        models=sorted_models,
        values=sorted_values,
        metric=metric,
        normalize=normalize
    )
    
    # Show creator legend
    print_creator_legend(sorted_models)


def generate_pareto_chart(
    models: List,
    quality_metric: str,
    cost_metric: str,
    width: int,
    height: int,
    show_table: bool = False,
    cost_label: str = None,
    use_blended_cost: bool = False
) -> None:
    """Generate and display Pareto frontier chart."""
    
    # Extract data points
    points = []
    valid_models = []
    
    for model in models:
        quality = model.get_benchmark_value(quality_metric)
        
        # Handle cost metric
        if use_blended_cost or cost_metric == "blended_cost":
            cost = calculate_blended_cost(model)
        elif cost_metric in ["input_price_per_1M_tokens_USD", "output_price_per_1M_tokens_USD"]:
            pricing = model.get_pricing_info()
            cost = pricing.get(cost_metric)
        else:
            cost = model.get_benchmark_value(cost_metric)
        
        if quality is not None and cost is not None and cost > 0:
            points.append((cost, quality))
            valid_models.append(model)
    
    if len(points) < 2:
        print_error(f"Not enough models with both {quality_metric} and {cost_metric} data.")
        return
    
    # Compute Pareto frontier
    frontier_indices = compute_pareto_frontier(
        points,
        minimize_x=True,  # Minimize cost
        minimize_y=False  # Maximize quality
    )
    
    # Extract coordinates
    costs = [p[0] for p in points]
    qualities = [p[1] for p in points]
    
    # Create scatter plot
    plt.clear_data()
    plt.scatter(costs, qualities, marker="o")
    
    # Add frontier line
    if frontier_indices:
        frontier_costs = [points[i][0] for i in frontier_indices]
        frontier_qualities = [points[i][1] for i in frontier_indices]
        plt.plot(frontier_costs, frontier_qualities, marker="o", color="red")
    
    # Use custom labels if provided
    display_cost_label = cost_label or cost_metric.replace('_', ' ').title()
    display_quality_label = quality_metric.replace('_', ' ').title()
    
    plt.title(f"Pareto Frontier: {display_quality_label} vs {display_cost_label}")
    plt.xlabel(f"{display_cost_label} (minimize)")
    plt.ylabel(f"{display_quality_label} (maximize)")
    
    plt.plotsize(width, height)
    plt.show()
    
    # Always show frontier table (it's useful!)
    print_pareto_table(valid_models, points, frontier_indices, quality_metric, cost_metric, cost_label)


def print_bar_chart_table(
    models: List,
    metrics: List[str],
    values_list: List[List[float]],
    normalize: str
) -> None:
    """Print data table for bar chart."""
    
    table = Table(title="Chart Data", show_header=True, header_style="bold blue")
    table.add_column("Model", style="cyan")
    
    for metric in metrics:
        label = metric.replace("_", " ").title()
        if normalize != "none":
            label += f" ({normalize})"
        table.add_column(label, justify="right")
    
    for i, model in enumerate(models):
        row = [clean_model_name(model.name)]
        
        for values in values_list:
            value = values[i]
            if value is None:
                row.append("—")  # Em dash for missing data
            else:
                row.append(format_number(value, 3))
        
        table.add_row(*row)
    
    console.print("\n")
    console.print(table)


def print_pareto_table(
    models: List,
    points: List[Tuple[float, float]],
    frontier_indices: List[int],
    quality_metric: str,
    cost_metric: str,
    cost_label: str = None
) -> None:
    """Print Pareto frontier table."""
    
    # Use custom labels if provided
    display_cost_label = cost_label or cost_metric.replace('_', ' ').title()
    display_quality_label = quality_metric.replace('_', ' ').title()
    
    console.print(f"\n[bold blue]Pareto Frontier Analysis[/bold blue]")
    console.print(f"Quality metric: {quality_metric} (higher is better)")
    console.print(f"Cost metric: {display_cost_label} (lower is better)")
    console.print()
    
    # Sort frontier points by cost
    frontier_data = [(i, points[i][0], points[i][1]) for i in frontier_indices]
    frontier_data.sort(key=lambda x: x[1])  # Sort by cost
    
    # Create table
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Model", style="cyan")
    table.add_column(display_cost_label, justify="right", style="red")
    table.add_column(display_quality_label, justify="right", style="green")
    table.add_column("Efficiency", justify="right", style="yellow")
    table.add_column("Status", style="blue")
    
    frontier_set = set(frontier_indices)
    
    for i, (model, point) in enumerate(zip(models, points)):
        cost, quality = point
        efficiency = quality / cost if cost > 0 else 0
        
        status = "🏆 Frontier" if i in frontier_set else "Dominated"
        
        table.add_row(
            clean_model_name(model.name, 35),
            format_number(cost, 3),
            format_number(quality, 2),
            format_number(efficiency, 3),
            status
        )
    
    console.print(table)
    console.print(f"\n[dim]Found {len(frontier_indices)} models on the Pareto frontier out of {len(models)} total.[/dim]")
