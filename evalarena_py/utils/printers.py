"""Output formatting and printing utilities for EvalArena CLI."""

import json
from typing import Any, Dict, List, Optional, Set

import yaml
from rich.console import Console
from rich.table import Table
from rich.text import Text

from ..data.model_schemas import FullModel
from .utils import format_number, format_price, format_tokens, truncate_string

console = Console()

# Benchmark display names mapping (from frontend)
BENCHMARK_LABELS = {
    "aime_2024": "AIME (2024)",
    "aime_2025": "AIME (2025)",
    "codeforces": "Codeforces",
    "gpqa_diamond": "GPQA Diamond",
    "math": "MATH",
    "math500": "MATH-500",
    "mmlu": "MMLU",
    "mmlu_pro": "MMLU Pro",
    "mmmu_val": "MMMU (val)",
    "humaneval": "HumanEval",
    "swe_bench_verified": "SWE Bench Verified",
    "live_code_bench_v5": "LiveCodeBench v5",
    "simple_qa": "Simple QA",
    "hle": "HLE",
    "aider_polyglot_diff": "Aider Polyglot Diff",
    "mathvista_testmini": "MathVista",
    "tau_bench_airline": "Tau Bench (airline)",
    "tau_bench_retail": "Tau Bench (retail)",
    "arc_agi_v2": "ARC-AGI-2",
    "mmmu": "MMMU",
    "mmmu_pro": "MMMU Pro",
    "mathvista": "MathVista",
    "mmbench_v1_1_en": "MMBench (en)",
    "doc_vqa": "DocVQA",
    "chart_qa": "ChartQA",
    "blink": "Blink",
    "longvideobench": "LongVideoBench",
    "video_mme_wo_sub": "VideoMME (w/o sub)",
    "osworld": "OSWorld",
    "screenspot_pro": "ScreenSpot-Pro",
    "webvoyager": "WebVoyager",
    "mm_mt_bench": "MM-MT-Bench",
    "active_params_in_billion": "Params (B)",
    "input_price_per_1M_tokens_USD": "Input Price",
    "output_price_per_1M_tokens_USD": "Output Price",
    "max_input_tokens": "Context Window",
    "max_output_tokens": "Max Output",
}

# Default column sets for different views
DEFAULT_COLUMNS = {
    "all": ["name", "creator", "release_date", "max_input_tokens", "description"],
    "small": ["name", "creator", "release_date", "max_input_tokens", "description"],
    "vlm": ["name", "creator", "release_date", "max_input_tokens", "description"],
    "chat": ["name", "creator", "description"],
}

# Benchmark column sets for --evals mode
BENCHMARK_COLUMNS = {
    "all": {
        "math": ["aime_2024", "aime_2025", "math", "math500"],
        "coding": ["humaneval", "swe_bench_verified", "live_code_bench_v5", "codeforces", "aider_polyglot_diff"],
        "knowledge": ["mmlu", "mmlu_pro", "gpqa_diamond", "simple_qa", "hle"],
        "other": ["mmmu_val", "mathvista_testmini", "tau_bench_airline", "tau_bench_retail", "arc_agi_v2"],
        "all": ["mmlu", "mmlu_pro", "humaneval", "math", "gpqa_diamond", "swe_bench_verified"]
    },
    "small": {
        "math": ["aime_2024", "aime_2025", "math", "math500"],
        "coding": ["humaneval", "swe_bench_verified", "live_code_bench_v5", "codeforces", "aider_polyglot_diff"],
        "knowledge": ["mmlu", "mmlu_pro", "gpqa_diamond", "simple_qa", "hle"],
        "other": ["mmmu_val", "mathvista_testmini"],
        "all": ["mmlu", "mmlu_pro", "humaneval", "math", "gpqa_diamond", "swe_bench_verified"]
    },
    "vlm": {
        "multimodal": ["mmmu", "mmmu_pro", "mathvista", "mmbench_v1_1_en", "blink"],
        "document": ["doc_vqa", "chart_qa"],
        "video": ["longvideobench", "video_mme_wo_sub"],
        "agent": ["osworld", "screenspot_pro", "webvoyager"],
        "all": ["mmmu", "mathvista", "doc_vqa", "osworld", "blink"]
    },
    "chat": {
        "all": ["mmlu", "humaneval"]
    }
}


def get_column_label(column: str) -> str:
    return BENCHMARK_LABELS.get(column, column.replace("_", " ").title())


def _get_model_value(model: FullModel, column: str) -> Any:
    if column == "description":
        desc_obj = getattr(model, column, None)
        if desc_obj and hasattr(desc_obj, 'additional_details'):
            return desc_obj
        elif isinstance(desc_obj, dict):
            from ..data.model_schemas import ModelDescription
            return ModelDescription(**desc_obj)
        else:
            return desc_obj if desc_obj else ""
    elif hasattr(model, column):
        return getattr(model, column)
    elif column in model.get_all_benchmarks():
        return model.get_benchmark_value(column)
    elif column == "input_price_per_1M_tokens_USD":
        return model.get_pricing_info().get("input_price_per_1M_tokens_USD")
    elif column == "output_price_per_1M_tokens_USD":
        return model.get_pricing_info().get("output_price_per_1M_tokens_USD")
    elif column == "max_input_tokens":
        return model.get_token_limits().get("max_input_tokens")
    elif column == "max_output_tokens":
        return model.get_token_limits().get("max_output_tokens")
    else:
        return None


def _find_max_values_for_columns(models: List[FullModel], columns: List[str]) -> Dict[str, float]:
    max_values = {}
    for column in columns:
        if column in ["name", "creator"]:
            continue
        values = []
        for model in models:
            value = _get_model_value(model, column)
            if isinstance(value, (int, float)) and value is not None:
                values.append(value)
        if values:
            max_values[column] = max(values)
    return max_values


def _format_structured_description(desc_obj) -> Text:
    from ..data.model_schemas import ModelDescription
    if not desc_obj or not isinstance(desc_obj, ModelDescription):
        return Text("—", style="dim")
    field_colors = {
        "architecture": "bright_cyan",
        "attention_embedding": "bright_blue",
        "pre_training": "blue3",
        "post_training": "blue1",
        "additional_details": "navy_blue"
    }
    field_order = ["architecture", "attention_embedding", "pre_training", "post_training", "additional_details"]
    parts = []
    for field_name in field_order:
        field_value = getattr(desc_obj, field_name, None)
        if field_value and field_value.lower() not in ["none", "null", ""]:
            field_text = Text(field_value, style=field_colors.get(field_name, "white"))
            parts.append(field_text)
    if not parts:
        return Text("—", style="dim")
    result = Text()
    for i, part in enumerate(parts):
        if i > 0:
            result.append("\n")
        result.append(part)
    return result


def _print_description_legend() -> None:
    field_colors = {
        "Architecture": "bright_cyan",
        "Attention/Embedding": "bright_blue",
        "Pre-training": "blue3",
        "Post-training": "blue1",
        "Additional Details": "navy_blue"
    }
    console.print("[dim]Description Color Legend:[/dim]")
    legend_parts = []
    for field_name, color in field_colors.items():
        legend_parts.append(Text(field_name, style=color))
    legend_text = Text("• ")
    for i, part in enumerate(legend_parts):
        if i > 0:
            legend_text.append("  • ")
        legend_text.append(part)
    console.print(legend_text)


def _create_diff_cell(val1: Any, val2: Any, diff_mode: str) -> Text:
    if val1 is not None and val2 is not None:
        if diff_mode == "absolute":
            diff = val2 - val1
            diff_text = f"{diff:+.2f}"
            if diff > 0:
                return Text(diff_text, style="green")
            elif diff < 0:
                return Text(diff_text, style="red")
            else:
                return Text(diff_text, style="yellow")
        elif diff_mode == "percent":
            if val1 != 0:
                diff_pct = ((val2 - val1) / val1) * 100
                diff_text = f"{diff_pct:+.1f}%"
                if diff_pct > 0:
                    return Text(diff_text, style="green")
                elif diff_pct < 0:
                    return Text(diff_text, style="red")
                else:
                    return Text(diff_text, style="yellow")
            else:
                return Text("∞", style="yellow")
    return Text("—", style="dim")


def format_cell_value(value: Any, column: str, highlight_max: bool = False, is_max: bool = False) -> Text:
    if value is None:
        return Text("—", style="dim")
    if "price" in column.lower():
        formatted = format_price(value)
    elif "tokens" in column.lower():
        formatted = format_tokens(value)
    elif "params" in column.lower():
        formatted = f"{value:.1f}" if isinstance(value, (int, float)) else str(value)
    elif column == "release_date":
        if isinstance(value, str):
            try:
                from datetime import datetime
                if "GMT" in value or "UTC" in value:
                    parts = value.split()
                    if len(parts) >= 4:
                        dt = datetime.strptime(f"{parts[1]} {parts[2]} {parts[3]}", "%d %b %Y")
                        formatted = dt.strftime("%b %Y")
                    else:
                        formatted = value[:10]
                else:
                    formatted = value[:7] if len(value) >= 7 else value
            except:
                formatted = str(value)[:10]
        else:
            formatted = str(value)[:10]
    elif column == "description":
        from ..data.model_schemas import ModelDescription
        if isinstance(value, ModelDescription):
            return _format_structured_description(value)
        elif isinstance(value, dict):
            desc_obj = ModelDescription(**value)
            return _format_structured_description(desc_obj)
        else:
            desc = str(value) if value else ""
            if desc.lower() in ["none", "null", ""] or "architecture=None" in desc:
                desc = "—"
            formatted = truncate_string(desc, 40)
    elif isinstance(value, (int, float)):
        formatted = format_number(value)
    else:
        formatted = str(value)
    style = ""
    if highlight_max and is_max and isinstance(value, (int, float)):
        style = "bold green"
    elif isinstance(value, (int, float)) and value > 0:
        style = "bright_white"
    else:
        style = "white"
    return Text(formatted, style=style)


def print_models_table(
    models: List[FullModel],
    columns: Optional[List[str]] = None,
    title: Optional[str] = None,
    highlight_max: bool = True
) -> None:
    if not models:
        console.print("[yellow]No models found.")
        return
    if columns is None:
        columns = DEFAULT_COLUMNS["all"]
    table = Table(title=title, show_header=True, header_style="bold blue")
    for column in columns:
        label = get_column_label(column)
        if column == "name":
            table.add_column(label, style="cyan", no_wrap=False, min_width=20, max_width=35)
        elif column == "creator":
            table.add_column(label, style="blue", no_wrap=True)
        elif column == "description":
            terminal_width = console.size.width
            base_width = terminal_width - 80
            min_desc_width = max(60, base_width // 3)
            max_desc_width = max(min_desc_width, base_width)
            table.add_column(label, no_wrap=False, min_width=min_desc_width, max_width=max_width)
        elif "price" in column.lower():
            table.add_column(label, justify="right", style="green")
        elif isinstance(getattr(models[0], column, None), (int, float)) or column in BENCHMARK_LABELS:
            table.add_column(label, justify="right")
        else:
            table.add_column(label, no_wrap=True)
    max_values = {}
    if highlight_max:
        max_values = _find_max_values_for_columns(models, columns)
    for model in models:
        row = []
        for column in columns:
            value = _get_model_value(model, column)
            is_max = column in max_values and isinstance(value, (int, float)) and value == max_values[column]
            cell = format_cell_value(value, column, highlight_max, is_max)
            row.append(cell)
        table.add_row(*row)
    if "description" in columns:
        _print_description_legend()
        console.print()
    console.print(table)
    console.print(f"\n[dim]Showing {len(models)} models[/dim]")


def print_model_details(model: FullModel) -> None:
    console.print(f"\n[bold cyan]{model.name}[/bold cyan]")
    info_table = Table(show_header=False, box=None, padding=(0, 2))
    info_table.add_column("Field", style="blue")
    info_table.add_column("Value")
    if model.creator:
        info_table.add_row("Creator", model.creator)
    if model.release_date:
        info_table.add_row("Release Date", str(model.release_date))
    if model.active_params_in_billion:
        info_table.add_row("Parameters", f"{model.active_params_in_billion:.1f}B")
    token_limits = model.get_token_limits()
    if token_limits["max_input_tokens"]:
        info_table.add_row("Max Input Tokens", format_tokens(token_limits["max_input_tokens"]))
    if token_limits["max_output_tokens"]:
        info_table.add_row("Max Output Tokens", format_tokens(token_limits["max_output_tokens"]))
    pricing = model.get_pricing_info()
    if pricing["input_price_per_1M_tokens_USD"]:
        info_table.add_row("Input Price (1M tokens)", format_price(pricing["input_price_per_1M_tokens_USD"]))
    if pricing["output_price_per_1M_tokens_USD"]:
        info_table.add_row("Output Price (1M tokens)", format_price(pricing["output_price_per_1M_tokens_USD"]))
    if model.categories:
        info_table.add_row("Categories", ", ".join(model.categories))
    if model.modalities:
        info_table.add_row("Modalities", ", ".join(model.modalities))
    console.print(info_table)
    benchmarks = model.get_all_benchmarks()
    if benchmarks:
        console.print("\n[bold blue]Benchmark Results[/bold blue]")
        bench_table = Table(show_header=True, header_style="bold")
        bench_table.add_column("Benchmark", style="cyan")
        bench_table.add_column("Score", justify="right")
        for key, value in sorted(benchmarks.items()):
            label = get_column_label(key)
            bench_table.add_row(label, format_number(value))
        console.print(bench_table)
    if model.description:
        console.print("\n[bold blue]Description[/bold blue]")
        if isinstance(model.description, str):
            console.print(model.description)
        else:
            desc_table = Table(show_header=False, box=None, padding=(0, 2))
            desc_table.add_column("Field", style="blue")
            desc_table.add_column("Value")
            if model.description.architecture:
                desc_table.add_row("Architecture", model.description.architecture)
            if model.description.attention_embedding:
                desc_table.add_row("Attention/Embedding", model.description.attention_embedding)
            if model.description.pre_training:
                desc_table.add_row("Pre-training", model.description.pre_training)
            if model.description.post_training:
                desc_table.add_row("Post-training", model.description.post_training)
            if model.description.additional_details:
                desc_table.add_row("Additional Details", model.description.additional_details)
            console.print(desc_table)
    if model.link or model.references:
        console.print("\n[bold blue]Links[/bold blue]")
        if model.link:
            console.print(f"• Main: {model.link}")
        if model.references:
            for ref in model.references:
                console.print(f"• Reference: {ref}")


def print_comparison_table(
    models: List[FullModel],
    columns: Optional[List[str]] = None,
    diff_mode: str = "none"
) -> None:
    if len(models) < 2:
        console.print("[red]Need at least 2 models for comparison.")
        return
    if columns is None:
        all_benchmarks = set()
        for model in models:
            all_benchmarks.update(model.get_all_benchmarks().keys())
        columns = sorted(list(all_benchmarks))
    table = Table(title="Model Comparison", show_header=True, header_style="bold blue")
    table.add_column("Metric", style="cyan")
    for model in models:
        table.add_column(truncate_string(model.name, 15), justify="right")
    if diff_mode != "none" and len(models) == 2:
        table.add_column("Diff", justify="right", style="yellow")
    for column in columns:
        values = []
        for model in models:
            value = model.get_benchmark_value(column)
            values.append(value)
        if all(v is None for v in values):
            continue
        numeric_values = [v for v in values if v is not None and isinstance(v, (int, float))]
        max_value = max(numeric_values) if numeric_values else None
        row = [get_column_label(column)]
        for value in values:
            if value is not None:
                formatted_value = format_number(value)
                if (max_value is not None and isinstance(value, (int, float)) and value == max_value):
                    cell = Text(formatted_value, style="bold green")
                else:
                    cell = Text(formatted_value, style="white")
                row.append(cell)
            else:
                row.append(Text("—", style="dim"))
        if diff_mode != "none" and len(models) == 2:
            val1, val2 = values[0], values[1]
            diff_cell = _create_diff_cell(val1, val2, diff_mode)
            row.append(diff_cell)
        table.add_row(*row)
    console.print(table)
    console.print(f"\n[dim]Comparing {len(models)} models across {len([c for c in columns if not all(model.get_benchmark_value(c) is None for model in models)])} metrics[/dim]")
    console.print("[dim]• [bold green]Highest values[/bold green] are highlighted in each row[/dim]")


def print_json(data: Any) -> None:
    if hasattr(data, 'model_dump'):
        json_data = data.model_dump(exclude_none=True)
    elif isinstance(data, list) and data and hasattr(data[0], 'model_dump'):
        json_data = [item.model_dump(exclude_none=True) for item in data]
    else:
        json_data = data
    console.print(json.dumps(json_data, indent=2, default=str))


def print_yaml(data: Any) -> None:
    if hasattr(data, 'model_dump'):
        yaml_data = data.model_dump(exclude_none=True)
    elif isinstance(data, list) and data and hasattr(data[0], 'model_dump'):
        yaml_data = [item.model_dump(exclude_none=True) for item in data]
    else:
        yaml_data = data
    console.print(yaml.dump(yaml_data, default_flow_style=False, sort_keys=False))


def print_output(data: Any, format_type: str, **kwargs: Any) -> None:
    if format_type == "json":
        print_json(data)
    elif format_type == "yaml":
        print_yaml(data)
    elif format_type == "table":
        if isinstance(data, list) and data and hasattr(data[0], 'name'):
            print_models_table(data, **kwargs)
        else:
            print_json(data)
    else:
        console.print(f"[red]Unknown output format: {format_type}")


def print_error(message: str) -> None:
    console.print(f"[red]Error: {message}[/red]")


def print_warning(message: str) -> None:
    console.print(f"[yellow]Warning: {message}[/yellow]")


def print_success(message: str) -> None:
    console.print(f"[green]✓ {message}[/green]")


def print_info(message: str) -> None:
    console.print(f"[blue]ℹ {message}[/blue]")


