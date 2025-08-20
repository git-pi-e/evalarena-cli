"""Core functionality for EvalArena CLI."""

from .auth import login, logout
from .config import get_config, update_config, reload_config
from .data_access import fetch_models, fetch_model_by_id
from .http import health_check, clear_cache, get_cache_stats

__all__ = [
    "login",
    "logout", 
    "get_config",
    "update_config",
    "reload_config",
    "fetch_models",
    "fetch_model_by_id",
    "health_check",
    "clear_cache",
    "get_cache_stats",
]