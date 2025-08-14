# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-01-15

### Added
- Initial release of EvalArena CLI
- **Model Management**
  - `models list` - List and filter models with intelligent defaults
  - `models search` - Search models with fuzzy matching
  - `model show` - Display detailed model information
  - Support for multiple model types (all, small, VLM, chat)
  - Client-side pagination and limiting
  - Benchmark categories with `--evals` flag (math, coding, multimodal, etc.)

- **Model Comparison**
  - `compare` - Side-by-side model comparison with diff calculations
  - Support for multiple comparison modes (absolute, percentage, relative)
  - Intelligent metric alignment and missing value handling

- **Data Visualization**
  - `charts bar` - Horizontal ASCII bar charts with creator-based colors
  - `charts pareto` - Pareto frontier analysis with visual scatter plots
  - Default blended cost calculation (3:1 input:output token ratio)
  - Support for multiple benchmark metrics
  - Descending sort and filtering of zero/null values

- **Authentication & Configuration**
  - `auth login/logout` - Secure token storage using system keyring
  - `config show/set` - Configuration management with TOML files
  - Environment variable overrides for all settings
  - HTTP caching with ETag and Last-Modified support

- **Developer Experience**
  - Comprehensive shell tab completion for all commands and flags
  - Context-aware completion (e.g., `--evals` options change based on `--type`)
  - Rich terminal UI with colored tables and formatted output
  - Robust error handling and helpful error messages
  - Extensive test coverage with pytest

- **Technical Features**
  - Modern Python packaging with `pyproject.toml`
  - Type hints throughout codebase (`py.typed` marker)
  - Async HTTP client with retries and timeouts
  - Extensible architecture for future features
  - Support for Python 3.9+

### Technical Details
- Built with `typer` for CLI framework
- Uses `httpx` for HTTP requests with caching via `diskcache`
- Rich terminal formatting with `rich` library
- Pydantic models for data validation and serialization
- Keyring integration for secure credential storage
- Comprehensive testing with `pytest` and `respx` for HTTP mocking

[Unreleased]: https://github.com/evalarena/evalarena-cli/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/evalarena/evalarena-cli/releases/tag/v0.1.0
