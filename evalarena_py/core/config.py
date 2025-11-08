"""Configuration management for EvalArena CLI."""

import os
from pathlib import Path
from typing import List, Optional

import tomlkit
from platformdirs import user_config_dir
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChartConfig(BaseModel):
    """Chart display configuration."""

    width: int = Field(default=100, ge=40, le=200)
    height: int = Field(default=30, ge=10, le=100)
    normalize: str = Field(default="none", pattern=r"^(none|zscore|minmax)$")


class ChatConfig(BaseModel):
    """Chat configuration settings."""

    default_models: List[str] = Field(default_factory=list, description="Default chat model IDs to use")


class EvalArenaSettings(BaseSettings):
    """EvalArena CLI configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="EVALARENA_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # Core settings
    base_url: str = Field(
        default="https://evalarena-backend-89846023945.us-central1.run.app",
        description="Base URL for EvalArena API"
    )
    timeout_s: int = Field(
        default=15,
        ge=5,
        le=120,
        description="HTTP request timeout in seconds"
    )
    token: Optional[str] = Field(
        default=None,
        description="Authentication token for API access"
    )

    # Output settings
    output_format: str = Field(
        default="table",
        pattern=r"^(table|json|yaml)$",
        description="Default output format"
    )
    no_color: bool = Field(
        default=False,
        description="Disable colored output"
    )

    # Model display settings
    default_columns: List[str] = Field(
        default_factory=lambda: [
            "name", "creator", "mmlu", "mmlu_pro", "humaneval",
            "active_params_in_billion", "input_price_per_1M_tokens_USD"
        ],
        description="Default columns to display in model tables"
    )

    # Chart settings
    chart: ChartConfig = Field(default_factory=ChartConfig)

    # Chat settings
    chat: ChatConfig = Field(default_factory=ChatConfig)

    # Cache settings
    cache_enabled: bool = Field(default=True, description="Enable HTTP caching")
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        description="Cache TTL in seconds"
    )


def get_config_dir() -> Path:
    """Get the configuration directory path."""
    return Path(user_config_dir("evalarena"))


def get_config_file() -> Path:
    """Get the configuration file path."""
    return get_config_dir() / "config.toml"


def load_config() -> EvalArenaSettings:
    """Load configuration from file and environment variables."""
    config_file = get_config_file()

    # Start with defaults
    config_data = {}

    # Load from config file if it exists
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = tomlkit.load(f)
        except Exception:
            # If config file is corrupted, start fresh
            config_data = {}

    # Create settings (env vars will override file settings)
    return EvalArenaSettings(**config_data)


def save_config(settings: EvalArenaSettings) -> None:
    """Save configuration to file."""
    config_file = get_config_file()
    config_dir = config_file.parent

    # Create config directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)

    # Convert settings to dict, excluding None values and env-only fields
    config_data = {}
    for field_name, field_info in settings.model_fields.items():
        value = getattr(settings, field_name)
        if value is not None and field_name != "token":  # Don't save token to file
            if isinstance(value, BaseModel):
                config_data[field_name] = value.model_dump(exclude_none=True)
            else:
                config_data[field_name] = value

    # Write to file
    with open(config_file, "w", encoding="utf-8") as f:
        tomlkit.dump(config_data, f)


def update_config(key: str, value: str) -> None:
    """Update a configuration key with a new value."""
    settings = load_config()

    # Handle nested keys like "chart.width"
    if "." in key:
        parts = key.split(".", 1)
        if parts[0] == "chart":
            chart_config = settings.chart.model_copy()
            if hasattr(chart_config, parts[1]):
                # Type conversion based on field type
                field_info = chart_config.model_fields[parts[1]]
                if field_info.annotation == int:
                    value = int(value)
                elif field_info.annotation == bool:
                    value = value.lower() in ("true", "1", "yes", "on")
                setattr(chart_config, parts[1], value)
                settings.chart = chart_config
            else:
                raise ValueError(f"Unknown chart config key: {parts[1]}")
        elif parts[0] == "chat":
            chat_config = settings.chat.model_copy()
            if hasattr(chat_config, parts[1]):
                field_info = chat_config.model_fields[parts[1]]
                if field_info.annotation == List[str]:
                    if value.strip() == "":
                        parsed_value = []
                    else:
                        parsed_value = [s.strip() for s in value.split(",") if s.strip()]
                    setattr(chat_config, parts[1], parsed_value)
                elif field_info.annotation == bool:
                    parsed_bool = value.lower() in ("true", "1", "yes", "on")
                    setattr(chat_config, parts[1], parsed_bool)
                else:
                    setattr(chat_config, parts[1], value)
                settings.chat = chat_config
            else:
                raise ValueError(f"Unknown chat config key: {parts[1]}")
        else:
            raise ValueError(f"Unknown nested config key: {key}")
    else:
        # Handle top-level keys
        if hasattr(settings, key):
            field_info = settings.model_fields[key]
            # Type conversion based on field type
            if field_info.annotation == int:
                value = int(value)
            elif field_info.annotation == bool:
                value = value.lower() in ("true", "1", "yes", "on")
            elif field_info.annotation == List[str]:
                value = [s.strip() for s in value.split(",")]
            setattr(settings, key, value)
        else:
            raise ValueError(f"Unknown config key: {key}")

    save_config(settings)


# Global config instance
_config: Optional[EvalArenaSettings] = None


def get_config() -> EvalArenaSettings:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config() -> EvalArenaSettings:
    """Reload configuration from file and environment."""
    global _config
    _config = load_config()
    return _config


