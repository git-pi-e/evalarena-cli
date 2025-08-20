# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EvalArena CLI is a Python command-line tool for comparing and analyzing AI model benchmarks. It uses Typer for CLI framework, Rich for terminal UI, httpx for async HTTP requests, and Pydantic for data validation.

## Development Commands

### Setup
- `make install-dev` - Install package for development with all dependencies
- `make install` - Install package for production use

### Testing
- `pytest -v` - Run tests with verbose output
- `pytest --cov=evalarena --cov-report=html --cov-report=term` - Run tests with coverage

### Code Quality
- `make check-all` - Run all checks (lint, format-check, type-check, test)
- `make lint` - Run linting with ruff
- `make format` - Format code with black
- `make format-check` - Check code formatting without changes
- `make type-check` - Run mypy type checking
- `make fix` - Auto-format and fix linting issues

### Build & Package
- `make build` - Build package for distribution
- `make clean` - Remove build artifacts and cache files
- `make publish` - Publish to PyPI (requires twine setup)

### Running Single Tests
- `pytest tests/test_config.py` - Run specific test file
- `pytest tests/test_config.py::TestClass::test_method` - Run specific test method

## Architecture

### Core Components
- `cli.py` - Main CLI application with Typer commands and global options
- `config.py` - Configuration management using Pydantic settings and TOML files
- `http.py` - HTTP client with caching, authentication, and error handling
- `data_access.py` - API data access layer with model type endpoints
- `auth.py` - Authentication using keyring for secure token storage

### Command Modules
- `models_cmd.py` - List, search, and filter models
- `model_cmd.py` - Show individual model details
- `compare_cmd.py` - Compare multiple models side-by-side
- `chat_cmd.py` - Multi-model chat functionality
- `charts_cmd.py` - Generate terminal charts (bar charts and Pareto frontiers)

### Data Layer
- `model_schemas.py` - Pydantic models for API response validation
- `printers.py` - Formatted output utilities with Rich
- `utils.py` - Common utility functions
- `completions.py` - Tab completion support

### Model Types
The API supports different model endpoints:
- `/api/models/` - All models
- `/api/small-models/` - Small models
- `/api/vlm-models/` - Vision-language models  
- `/api/chat/models/` - Chat models

### Configuration
- Configuration stored in `~/.config/evalarena/config.toml`
- Environment variables prefixed with `EVALARENA_`
- Settings include API endpoints, cache configuration, chart settings, and default columns
- Uses platformdirs for cross-platform config directory detection

### HTTP Client
- Uses httpx with async support
- Implements ETags and conditional requests for caching
- Uses diskcache for persistent HTTP caching
- Includes authentication headers and error handling
- Configurable timeout and base URL override

### Testing
- Uses pytest with pytest-asyncio for async testing
- respx for HTTP request mocking
- Coverage reporting available
- Test files follow `test_*.py` naming pattern

## Key Development Patterns

### CLI Command Structure
All commands use Typer with typed parameters and rich help text. Commands are organized into sub-apps (auth, config, models, etc.) and registered with the main app.

### Error Handling
Uses custom printer functions (`print_error`, `print_success`, `print_info`) with Rich formatting. Exceptions are caught and displayed with helpful error messages.

### Data Validation
All API responses are validated through Pydantic models in `model_schemas.py`. This ensures type safety and proper error handling for malformed data.

### Async Patterns
HTTP requests use async/await with httpx. The CLI handles async operations through `asyncio.run()` for synchronous command interfaces.

### Configuration Management
Uses Pydantic BaseSettings for configuration with environment variable override support. Config can be updated programmatically and persisted to TOML files.