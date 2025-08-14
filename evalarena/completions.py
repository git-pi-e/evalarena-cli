"""Tab completion functions for the EvalArena CLI."""

import os
from typing import List

from .data_access import ModelType
from .printers import BENCHMARK_COLUMNS


def complete_model_type() -> List[str]:
    """Complete model type values."""
    return [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]


def complete_sort_order() -> List[str]:
    """Complete sort order values."""
    return ["asc", "desc"]


def complete_output_format() -> List[str]:
    """Complete output format values."""
    return ["table", "json", "yaml"]


def complete_diff_mode() -> List[str]:
    """Complete diff mode values."""
    return ["none", "absolute", "percent"]


def complete_normalize_mode() -> List[str]:
    """Complete normalization mode values."""
    return ["none", "zscore", "minmax"]


def complete_evals_category_smart() -> List[str]:
    """Smart completion for evals categories based on the model type in the command line."""
    # Get the current command line from Typer's completion context
    complete_args = os.environ.get('_TYPER_COMPLETE_ARGS', '')
    
    # Extract model type from the command line
    model_type = "all"  # default
    if '--type' in complete_args:
        parts = complete_args.split('--type')
        if len(parts) > 1:
            # Get the next word after --type
            type_part = parts[1].strip().split()[0] if parts[1].strip() else ""
            if type_part in [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]:
                model_type = type_part
    
    # Return categories specific to the model type
    categories = BENCHMARK_COLUMNS.get(model_type, {}).keys()
    return sorted(list(categories))


def complete_evals_category(model_type: str = "all") -> List[str]:
    """Complete evaluation category values based on model type."""
    categories = BENCHMARK_COLUMNS.get(model_type, {}).keys()
    return list(categories)


def complete_all_evals_categories() -> List[str]:
    """Complete all possible evaluation categories across all model types."""
    all_categories = set()
    for model_categories in BENCHMARK_COLUMNS.values():
        all_categories.update(model_categories.keys())
    return sorted(list(all_categories))


def complete_common_benchmarks() -> List[str]:
    """Complete common benchmark names."""
    return [
        "mmlu", "mmlu_pro", "humaneval", "math", "gpqa_diamond", 
        "swe_bench_verified", "aime_2024", "mmmu", "mathvista",
        "doc_vqa", "live_code_bench_v5", "aider_polyglot_diff"
    ]


def complete_config_keys() -> List[str]:
    """Complete configuration keys."""
    return [
        "base_url", "output_format", "timeout_s", "default_columns",
        "chart.width", "chart.height", "chart.normalize", "cache.enabled"
    ]


def complete_boolean_values() -> List[str]:
    """Complete boolean values."""
    return ["true", "false", "yes", "no", "on", "off"]
