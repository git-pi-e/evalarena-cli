"""Tab completion functions for the EvalArena CLI."""

import os
from typing import List

import typer

from ..core.data_access import ModelType
from .printers import BENCHMARK_COLUMNS


def complete_model_type() -> List[str]:
    return [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]


def complete_sort_order() -> List[str]:
    return ["asc", "desc"]


def complete_output_format() -> List[str]:
    return ["table", "json", "yaml"]


def complete_diff_mode() -> List[str]:
    return ["none", "absolute", "percent"]


def complete_normalize_mode() -> List[str]:
    return ["none", "zscore", "minmax"]


def complete_evals_category_smart() -> List[str]:
    complete_args = os.environ.get('_TYPER_COMPLETE_ARGS', '')
    model_type = "all"
    if '--type' in complete_args:
        parts = complete_args.split('--type')
        if len(parts) > 1:
            type_part = parts[1].strip().split()[0] if parts[1].strip() else ""
            if type_part in [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]:
                model_type = type_part
    categories = BENCHMARK_COLUMNS.get(model_type, {}).keys()
    return sorted(list(categories))


def complete_evals_category(model_type: str = "all") -> List[str]:
    categories = BENCHMARK_COLUMNS.get(model_type, {}).keys()
    return list(categories)


def complete_all_evals_categories() -> List[str]:
    all_categories = set()
    for model_categories in BENCHMARK_COLUMNS.values():
        all_categories.update(model_categories.keys())
    return sorted(list(all_categories))


def complete_common_benchmarks() -> List[str]:
    return [
        "mmlu", "mmlu_pro", "humaneval", "math", "gpqa_diamond",
        "swe_bench_verified", "aime_2024", "mmmu", "mathvista",
        "doc_vqa", "live_code_bench_v5", "aider_polyglot_diff"
    ]


def complete_config_keys() -> List[str]:
    return [
        "base_url", "output_format", "timeout_s", "default_columns",
        "chart.width", "chart.height", "chart.normalize", "cache.enabled",
        "chat.default_models"
    ]


def complete_boolean_values() -> List[str]:
    return ["true", "false", "yes", "no", "on", "off"]


def complete_chat_models(ctx, incomplete: str) -> List[str]:
    def _ids() -> List[str]:
        try:
            import asyncio
            from ..commands.chat_cmd import get_available_chat_models
            return [m.get("id", "") for m in asyncio.run(get_available_chat_models())]
        except Exception:
            return [
                "gpt-4o",
                "gpt-4o-mini",
                "claude-3-5-sonnet",
                "claude-3-5-haiku",
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "llama-3.1-405b",
                "llama-3.1-70b",
            ]
    full_token = incomplete or ""
    prefix = ""
    needle = full_token
    if "," in full_token:
        prefix, needle = full_token.rsplit(",", 1)
        prefix += ","
        needle = needle.lstrip()
    needle_low = needle.lower()
    suggestions: List[str] = []
    for mid in _ids():
        if mid.lower().startswith(needle_low):
            suggestions.append(prefix + mid)
            if len(suggestions) >= 10:
                break
    return suggestions


def complete_model_names(ctx, incomplete: str) -> List[str]:
    def _get_model_names(model_type: str = "all") -> List[str]:
        try:
            import asyncio
            from ..core.data_access import fetch_models
            models = asyncio.run(fetch_models(
                model_type=model_type,
                sort_by="name",
                order="asc",
                bypass_cache=False
            ))
            return [model.name for model in models]
        except Exception:
            return [
                "Claude 3.5 Haiku",
                "Claude 3.5 Sonnet (new)",
                "Claude 3.7 Sonnet",
                "GPT-4o",
                "GPT-4o mini",
                "Gemini 1.5 Pro",
                "Gemini 1.5 Flash",
                "Llama 3.1 405B",
                "Llama 3.1 70B",
                "DeepSeek-V3",
                "DeepSeek-R1"
            ]
    model_type = "all"
    if ctx and hasattr(ctx, 'params'):
        if 'type' in ctx.params:
            model_type = ctx.params['type']
    else:
        complete_args = os.environ.get('_TYPER_COMPLETE_ARGS', '')
        if '--type' in complete_args:
            parts = complete_args.split('--type')
            if len(parts) > 1:
                type_part = parts[1].strip().split()[0] if parts[1].strip() else ""
                if type_part in [ModelType.ALL, ModelType.SMALL, ModelType.VLM, ModelType.CHAT]:
                    model_type = type_part
    model_names = _get_model_names(model_type)
    if not incomplete:
        return model_names
    needle = incomplete.lower()
    suggestions = []
    for model_name in model_names:
        if needle in model_name.lower():
            suggestions.append(model_name)
            if len(suggestions) >= 50:
                break
    return suggestions


