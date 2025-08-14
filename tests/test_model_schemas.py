"""Tests for model schemas."""

import pytest

from evalarena.model_schemas import FullModel, ModelDescription, BenchmarkResults


def test_full_model_basic():
    """Test basic FullModel functionality."""
    model_data = {
        "name": "Test Model",
        "creator": "Test Creator",
        "mmlu": 85.5,
        "humaneval": 90.2,
        "active_params_in_billion": 7.0,
        "input_price_per_1M_tokens_USD": "2.50",
        "max_input_tokens": "128,000"
    }
    
    model = FullModel(**model_data)
    
    assert model.name == "Test Model"
    assert model.creator == "Test Creator"
    assert model.mmlu == 85.5
    assert model.humaneval == 90.2
    assert model.active_params_in_billion == 7.0


def test_benchmark_value_retrieval():
    """Test benchmark value retrieval methods."""
    model_data = {
        "name": "Test Model",
        "mmlu": 85.5,
        "humaneval": 90.2,
        "benchmarks": {
            "math_benchmarks": {"aime_2024": 75.0},
            "coding_benchmarks": {"codeforces": 1200}
        }
    }
    
    model = FullModel(**model_data)
    
    # Test direct field access
    assert model.get_benchmark_value("mmlu") == 85.5
    assert model.get_benchmark_value("humaneval") == 90.2
    
    # Test nested benchmark access
    assert model.get_benchmark_value("aime_2024") == 75.0
    assert model.get_benchmark_value("codeforces") == 1200
    
    # Test missing values
    assert model.get_benchmark_value("nonexistent") is None


def test_all_benchmarks():
    """Test get_all_benchmarks method."""
    model_data = {
        "name": "Test Model",
        "mmlu": 85.5,
        "humaneval": 90.2,
        "benchmarks": {
            "math_benchmarks": {"aime_2024": 75.0},
            "coding_benchmarks": {"codeforces": 1200}
        }
    }
    
    model = FullModel(**model_data)
    all_benchmarks = model.get_all_benchmarks()
    
    assert "mmlu" in all_benchmarks
    assert "humaneval" in all_benchmarks
    assert "aime_2024" in all_benchmarks
    assert "codeforces" in all_benchmarks
    
    assert all_benchmarks["mmlu"] == 85.5
    assert all_benchmarks["aime_2024"] == 75.0


def test_pricing_info():
    """Test pricing information parsing."""
    model_data = {
        "name": "Test Model",
        "input_price_per_1M_tokens_USD": "2.50",
        "output_price_per_1M_tokens_USD": 10.0
    }
    
    model = FullModel(**model_data)
    pricing = model.get_pricing_info()
    
    assert pricing["input_price_per_1M_tokens_USD"] == 2.5
    assert pricing["output_price_per_1M_tokens_USD"] == 10.0


def test_token_limits():
    """Test token limit parsing."""
    model_data = {
        "name": "Test Model",
        "max_input_tokens": "128,000",
        "max_output_tokens": 16384
    }
    
    model = FullModel(**model_data)
    limits = model.get_token_limits()
    
    assert limits["max_input_tokens"] == 128000
    assert limits["max_output_tokens"] == 16384


def test_structured_description():
    """Test structured description handling."""
    model_data = {
        "name": "Test Model",
        "description": {
            "architecture": "Transformer",
            "pre_training": "Large corpus",
            "additional_details": "Special features"
        }
    }
    
    model = FullModel(**model_data)
    
    assert isinstance(model.description, ModelDescription)
    assert model.description.architecture == "Transformer"
    assert model.description.pre_training == "Large corpus"
    assert model.description.additional_details == "Special features"


def test_string_description():
    """Test string description handling."""
    model_data = {
        "name": "Test Model",
        "description": "Simple string description"
    }
    
    model = FullModel(**model_data)
    
    # String description should be preserved
    assert model.description == "Simple string description"


def test_benchmark_results():
    """Test BenchmarkResults structure."""
    results = BenchmarkResults(
        math_benchmarks={"math": 75.0, "aime_2024": 50.0},
        coding_benchmarks={"humaneval": 85.0}
    )
    
    assert results.math_benchmarks["math"] == 75.0
    assert results.coding_benchmarks["humaneval"] == 85.0
    assert results.language_understanding == {}  # Default empty dict


def test_model_with_id_alias():
    """Test model ID field with _id alias."""
    model_data = {
        "_id": "507f1f77bcf86cd799439011",
        "name": "Test Model"
    }
    
    model = FullModel(**model_data)
    assert model.id == "507f1f77bcf86cd799439011"
