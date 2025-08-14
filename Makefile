.PHONY: help install install-dev test lint format type-check build clean publish docs

# Default target
help:
	@echo "EvalArena CLI Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  install     Install package for production"
	@echo "  install-dev Install package for development"
	@echo ""
	@echo "Development:"
	@echo "  test        Run tests"
	@echo "  lint        Run linting (ruff)"
	@echo "  format      Format code (black)"
	@echo "  type-check  Run type checking (mypy)"
	@echo "  check-all   Run all checks (lint, format, type-check, test)"
	@echo ""
	@echo "Build & Release:"
	@echo "  build       Build package"
	@echo "  clean       Clean build artifacts"
	@echo "  publish     Publish to PyPI"
	@echo ""
	@echo "Documentation:"
	@echo "  docs        Generate documentation"

# Installation
install:
	pip install .

install-dev:
	pip install -e ".[dev]"

# Testing
test:
	pytest -v
	@echo "✅ Tests passed"

test-cov:
	pytest --cov=evalarena --cov-report=html --cov-report=term
	@echo "✅ Tests with coverage completed"

# Code quality
lint:
	ruff check evalarena tests
	@echo "✅ Linting passed"

format:
	black evalarena tests
	@echo "✅ Code formatted"

format-check:
	black --check evalarena tests
	@echo "✅ Code format is correct"

type-check:
	mypy evalarena
	@echo "✅ Type checking passed"

# Combined checks
check-all: lint format-check type-check test
	@echo "✅ All checks passed"

# Build and packaging
build: clean
	python -m build
	@echo "✅ Package built"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleaned build artifacts"

publish: build
	twine upload dist/*
	@echo "✅ Published to PyPI"

publish-test: build
	twine upload --repository testpypi dist/*
	@echo "✅ Published to Test PyPI"

# Development helpers
fix:
	black evalarena tests
	ruff check --fix evalarena tests
	@echo "✅ Code fixed and formatted"

install-tools:
	pip install black ruff mypy pytest pytest-cov build twine
	@echo "✅ Development tools installed"

# Quick development workflow
dev-setup: install-dev install-tools
	@echo "✅ Development environment ready"

quick-check: format lint type-check
	@echo "✅ Quick checks passed"

# Documentation
docs:
	@echo "📖 Documentation is in README.md"
	@echo "   Run 'evalarena --help' for CLI help"

# Version info
version:
	@python -c "from evalarena import __version__; print(f'EvalArena CLI v{__version__}')"

# Demo commands (for testing CLI functionality)
demo-basic:
	@echo "🎬 Running basic demo commands..."
	evalarena ping
	evalarena config show
	evalarena models columns --type small

demo-list:
	@echo "🎬 Demo: Listing models..."
	evalarena models list --type small --limit 5
	evalarena models search "phi"

demo-charts:
	@echo "🎬 Demo: Generating charts..."
	evalarena charts bar --type small --top 3 --columns mmlu,humaneval

# Release workflow
pre-release: check-all version
	@echo "✅ Ready for release"

release: pre-release build publish
	@echo "🚀 Released to PyPI"
