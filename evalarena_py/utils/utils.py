"""Utility functions for EvalArena CLI."""

import math
from typing import Any, Dict, List, Optional, Tuple

from ..core.data_access import search_models_by_name, ModelType
from ..data.model_schemas import FullModel


def is_numeric(value: Any) -> bool:
    if value is None:
        return False
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def normalize_values(values: List[float], method: str = "none") -> List[float]:
    if not values or method == "none":
        return values
    if method == "zscore":
        mean_val = sum(values) / len(values)
        variance = sum((x - mean_val) ** 2 for x in values) / len(values)
        std_val = math.sqrt(variance)
        if std_val == 0:
            return [0.0] * len(values)
        return [(x - mean_val) / std_val for x in values]
    elif method == "minmax":
        min_val = min(values)
        max_val = max(values)
        if min_val == max_val:
            return [0.0] * len(values)
        return [(x - min_val) / (max_val - min_val) for x in values]
    else:
        raise ValueError(f"Unknown normalization method: {method}")


async def resolve_model_names(
    model_names: List[str],
    model_type: str = ModelType.ALL
) -> List[FullModel]:
    resolved_models = []
    for name in model_names:
        matches = await search_models_by_name(name, model_type, fuzzy=False)
        if not matches:
            matches = await search_models_by_name(name, model_type, fuzzy=True)
        if not matches:
            raise ValueError(f"Could not find model: {name}")
        if len(matches) == 1:
            resolved_models.append(matches[0])
        else:
            exact_match = None
            for match in matches:
                if match.name.lower() == name.lower():
                    exact_match = match
                    break
            if exact_match:
                resolved_models.append(exact_match)
            else:
                match_names = [m.name for m in matches[:5]]
                raise ValueError(
                    f"Ambiguous model name '{name}'. Did you mean one of: {', '.join(match_names)}"
                )
    return resolved_models


def compute_pareto_frontier(
    points: List[Tuple[float, float]],
    minimize_x: bool = True,
    minimize_y: bool = False
) -> List[int]:
    if not points:
        return []
    indexed_points = [(i, x, y) for i, (x, y) in enumerate(points)]
    if minimize_x:
        indexed_points.sort(key=lambda p: p[1])
    else:
        indexed_points.sort(key=lambda p: p[1], reverse=True)
    frontier = []
    best_y = None
    for i, x, y in indexed_points:
        if best_y is None:
            frontier.append(i)
            best_y = y
        else:
            if minimize_y:
                if y < best_y:
                    frontier.append(i)
                    best_y = y
            else:
                if y > best_y:
                    frontier.append(i)
                    best_y = y
    return frontier


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_number(value: float, precision: int = 2) -> str:
    if value == 0:
        return "0"
    if abs(value) >= 1000:
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:.1f}M"
        else:
            return f"{value / 1000:.1f}K"
    if abs(value) < 0.01:
        return f"{value:.2e}"
    return f"{value:.{precision}f}"


def format_price(price: Optional[float]) -> str:
    if price is None:
        return "—"
    if price == 0:
        return "Free"
    if price >= 1:
        return f"${price:.2f}"
    else:
        return f"${price:.3f}"


def format_tokens(tokens: Optional[int]) -> str:
    if tokens is None:
        return "—"
    if tokens >= 1_000_000:
        return f"{tokens // 1_000_000}M"
    elif tokens >= 1_000:
        return f"{tokens // 1_000}K"
    else:
        return str(tokens)


def extract_numeric_fields(models: List[FullModel]) -> List[str]:
    numeric_fields = set()
    for model in models:
        all_benchmarks = model.get_all_benchmarks()
        numeric_fields.update(all_benchmarks.keys())
        if model.active_params_in_billion is not None:
            numeric_fields.add("active_params_in_billion")
        pricing = model.get_pricing_info()
        for key, value in pricing.items():
            if value is not None:
                numeric_fields.add(key)
    return sorted(list(numeric_fields))


def validate_benchmark_key(key: str, available_keys: List[str]) -> str:
    if key in available_keys:
        return key
    key_lower = key.lower()
    for available_key in available_keys:
        if available_key.lower() == key_lower:
            return available_key
    matches = [k for k in available_keys if key_lower in k.lower()]
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise ValueError(f"Ambiguous benchmark key '{key}'. Did you mean: {', '.join(matches[:5])}")
    else:
        close_matches = [k for k in available_keys if any(part in k.lower() for part in key_lower.split('_'))]
        if close_matches:
            raise ValueError(f"Unknown benchmark key '{key}'. Similar keys: {', '.join(close_matches[:5])}")
        else:
            raise ValueError(f"Unknown benchmark key '{key}'. Use 'evalarena models list --columns' to see available keys.")


def clean_model_name(name: str, max_length: int = 35) -> str:
    cleaned = name.strip()
    return truncate_string(cleaned, max_length)


