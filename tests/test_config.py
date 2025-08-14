"""Tests for configuration management."""

import tempfile
from pathlib import Path

import pytest

from evalarena.config import EvalArenaSettings, ChartConfig, update_config, load_config


def test_default_config():
    """Test default configuration values."""
    config = EvalArenaSettings()
    
    assert config.base_url == "https://evalarena.ai"
    assert config.timeout_s == 15
    assert config.output_format == "table"
    assert config.no_color is False
    assert config.cache_enabled is True
    assert isinstance(config.chart, ChartConfig)
    assert config.chart.width == 100
    assert config.chart.height == 30
    assert config.chart.normalize == "none"


def test_chart_config_validation():
    """Test chart configuration validation."""
    # Valid config
    chart = ChartConfig(width=80, height=20, normalize="zscore")
    assert chart.width == 80
    assert chart.height == 20
    assert chart.normalize == "zscore"
    
    # Invalid normalize method
    with pytest.raises(ValueError):
        ChartConfig(normalize="invalid")
    
    # Width/height bounds
    with pytest.raises(ValueError):
        ChartConfig(width=10)  # Too small
    
    with pytest.raises(ValueError):
        ChartConfig(height=300)  # Too large


def test_environment_override():
    """Test environment variable overrides."""
    import os
    
    # Set environment variable
    os.environ["EVALARENA_BASE_URL"] = "https://test.example.com"
    os.environ["EVALARENA_TIMEOUT_S"] = "30"
    
    try:
        config = EvalArenaSettings()
        assert config.base_url == "https://test.example.com"
        assert config.timeout_s == 30
    finally:
        # Clean up
        os.environ.pop("EVALARENA_BASE_URL", None)
        os.environ.pop("EVALARENA_TIMEOUT_S", None)


def test_settings_validation():
    """Test settings validation."""
    # Valid settings
    config = EvalArenaSettings(
        timeout_s=10,
        output_format="json"
    )
    assert config.timeout_s == 10
    assert config.output_format == "json"
    
    # Invalid timeout
    with pytest.raises(ValueError):
        EvalArenaSettings(timeout_s=2)  # Too small
    
    # Invalid output format
    with pytest.raises(ValueError):
        EvalArenaSettings(output_format="invalid")
