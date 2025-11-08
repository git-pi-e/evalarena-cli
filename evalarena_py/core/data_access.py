"""Data access layer for EvalArena API."""

from typing import Dict, List, Optional

from .http import cached_get
from ..data.model_schemas import FullModel, ChatModel


class ModelType:
    """Constants for model types."""
    ALL = "all"
    SMALL = "small"
    VLM = "vlm"
    CHAT = "chat"


# Map model types to API endpoints
ENDPOINT_MAP = {
    ModelType.ALL: "/api/models/",
    ModelType.SMALL: "/api/small-models/",
    ModelType.VLM: "/api/vlm-models/",
    ModelType.CHAT: "/api/chat/models/",
}


def _apply_client_side_pagination(models: List, page: Optional[int], limit: Optional[int]) -> List:
    """Apply client-side pagination and limiting to a list of models."""
    if page is not None or limit is not None:
        if limit is not None:
            if page is not None:
                start_idx = (page - 1) * limit
                end_idx = start_idx + limit
                return models[start_idx:end_idx]
            else:
                return models[:limit]
    return models


def _convert_chat_models_to_full_models(chat_models: List[ChatModel]) -> List[FullModel]:
    """Convert chat model objects to FullModel objects."""
    return [
        FullModel(
            name=cm.name,
            id=cm.id,
            creator=cm.creator,
            description=cm.description,
            categories=["chat"]
        )
        for cm in chat_models
    ]


def _parse_api_response_to_models(response_data) -> List[FullModel]:
    """Parse API response data into FullModel objects."""
    if isinstance(response_data, list):
        return [FullModel(**item) for item in response_data]
    elif isinstance(response_data, dict) and "data" in response_data:
        return [FullModel(**item) for item in response_data["data"]]
    else:
        return [FullModel(**item) for item in response_data]


async def fetch_models(
    model_type: str = ModelType.ALL,
    sort_by: str = "name",
    order: str = "asc",
    page: Optional[int] = None,
    limit: Optional[int] = None,
    bypass_cache: bool = False
) -> List[FullModel]:
    if model_type not in ENDPOINT_MAP:
        raise ValueError(f"Invalid model type: {model_type}. Must be one of: {list(ENDPOINT_MAP.keys())}")
    endpoint = ENDPOINT_MAP[model_type]
    params = {"sortBy": sort_by, "order": order}
    response_data = await cached_get(endpoint, params=params, bypass_cache=bypass_cache)
    if model_type == ModelType.CHAT:
        chat_models = [ChatModel(**item) for item in response_data]
        models = _convert_chat_models_to_full_models(chat_models)
    else:
        models = _parse_api_response_to_models(response_data)
    return _apply_client_side_pagination(models, page, limit)


async def fetch_model_by_id(model_id: str, model_type: str = ModelType.ALL) -> Optional[FullModel]:
    if model_type not in ENDPOINT_MAP:
        raise ValueError(f"Invalid model type: {model_type}")
    endpoint = f"{ENDPOINT_MAP[model_type]}{model_id}/"
    try:
        response_data = await cached_get(endpoint)
        return FullModel(**response_data)
    except Exception:
        return None


async def search_models_by_name(
    name_query: str,
    model_type: str = ModelType.ALL,
    fuzzy: bool = True
) -> List[FullModel]:
    all_models = await fetch_models(model_type)
    name_lower = name_query.lower()
    matches = []
    for model in all_models:
        model_name_lower = model.name.lower()
        if fuzzy:
            if (name_lower in model_name_lower or
                model_name_lower in name_lower or
                name_lower.replace("-", " ") in model_name_lower or
                name_lower.replace(" ", "-") in model_name_lower):
                matches.append(model)
        else:
            if name_lower == model_name_lower:
                matches.append(model)
    return matches


async def get_all_benchmark_keys(model_type: str = ModelType.ALL) -> List[str]:
    models = await fetch_models(model_type, limit=50)
    benchmark_keys = set()
    for model in models:
        benchmark_keys.update(model.get_all_benchmarks().keys())
    return sorted(list(benchmark_keys))


async def get_benchmark_statistics(
    benchmark_key: str,
    model_type: str = ModelType.ALL
) -> Dict[str, float]:
    models = await fetch_models(model_type)
    values = []
    for model in models:
        value = model.get_benchmark_value(benchmark_key)
        if value is not None:
            values.append(value)
    if not values:
        return {"min": 0, "max": 0, "mean": 0, "median": 0, "count": 0}
    values.sort()
    n = len(values)
    return {
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / n,
        "median": values[n // 2] if n % 2 == 1 else (values[n // 2 - 1] + values[n // 2]) / 2,
        "count": n,
    }


async def run_eval(prompt: str, models: List[str]) -> Dict[str, any]:
    raise NotImplementedError(
        "Prompt evaluation is not yet implemented. "
        "This feature is planned for a future release."
    )


