"""Tests for utility functions."""

import pytest

from evalarena.utils import (
    is_numeric,
    safe_float,
    normalize_values,
    compute_pareto_frontier,
    truncate_string,
    format_number,
    format_price,
    format_tokens,
    clean_model_name,
)


def test_is_numeric():
    """Test numeric detection."""
    assert is_numeric(42) is True
    assert is_numeric(3.14) is True
    assert is_numeric("42") is True
    assert is_numeric("3.14") is True
    assert is_numeric(None) is False
    assert is_numeric("hello") is False
    assert is_numeric("") is False


def test_safe_float():
    """Test safe float conversion."""
    assert safe_float(42) == 42.0
    assert safe_float("3.14") == 3.14
    assert safe_float(None) == 0.0
    assert safe_float(None, 5.0) == 5.0
    assert safe_float("invalid") == 0.0
    assert safe_float("invalid", -1.0) == -1.0


def test_normalize_values():
    """Test value normalization."""
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    
    # No normalization
    result = normalize_values(values, "none")
    assert result == values
    
    # Min-max normalization
    result = normalize_values(values, "minmax")
    assert result == [0.0, 0.25, 0.5, 0.75, 1.0]
    
    # Z-score normalization
    result = normalize_values(values, "zscore")
    # Mean = 3, std ≈ 1.58
    assert len(result) == 5
    assert abs(sum(result)) < 1e-10  # Mean should be ~0
    
    # Invalid method
    with pytest.raises(ValueError):
        normalize_values(values, "invalid")
    
    # Edge cases
    assert normalize_values([], "minmax") == []
    assert normalize_values([5.0, 5.0, 5.0], "minmax") == [0.0, 0.0, 0.0]


def test_compute_pareto_frontier():
    """Test Pareto frontier computation."""
    # Simple case: minimize x, maximize y
    points = [(1, 1), (2, 3), (3, 2), (4, 4), (5, 1)]
    frontier = compute_pareto_frontier(points, minimize_x=True, minimize_y=False)
    
    # Expected frontier: (1,1), (2,3), (4,4)
    assert len(frontier) == 3
    assert 0 in frontier  # (1,1)
    assert 1 in frontier  # (2,3)
    assert 3 in frontier  # (4,4)
    
    # Empty case
    assert compute_pareto_frontier([]) == []
    
    # Single point
    assert compute_pareto_frontier([(1, 2)]) == [0]


def test_truncate_string():
    """Test string truncation."""
    assert truncate_string("hello", 10) == "hello"
    assert truncate_string("hello world", 8) == "hello..."
    assert truncate_string("hello world", 8, "!!") == "hello !!"
    assert truncate_string("", 5) == ""


def test_format_number():
    """Test number formatting."""
    assert format_number(0) == "0"
    assert format_number(42.123) == "42.12"
    assert format_number(1234) == "1.2K"
    assert format_number(1234567) == "1.2M"
    assert format_number(0.001) == "1.00e-03"
    assert format_number(0.123, 3) == "0.123"


def test_format_price():
    """Test price formatting."""
    assert format_price(None) == "—"
    assert format_price(0) == "Free"
    assert format_price(1.50) == "$1.50"
    assert format_price(0.001) == "$0.001"
    assert format_price(10.0) == "$10.00"


def test_format_tokens():
    """Test token formatting."""
    assert format_tokens(None) == "—"
    assert format_tokens(500) == "500"
    assert format_tokens(1500) == "1K"
    assert format_tokens(2000000) == "2M"
    assert format_tokens(128000) == "128K"


def test_clean_model_name():
    """Test model name cleaning."""
    assert clean_model_name("gpt-4o") == "4o"
    assert clean_model_name("Claude-3.5-Sonnet") == "3.5-Sonnet"
    assert clean_model_name("llama-3-instruct") == "3"
    assert clean_model_name("very-long-model-name-that-exceeds-limit", 10) == "very-lo..."
