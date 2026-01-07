.PHONY: help install test test-cov run clean lint format check

# Default target
help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run all tests"
	@echo "  make test-cov   - Run tests with coverage report"
	@echo "  make run        - Start development server"
	@echo "  make clean      - Remove cache and temporary files"
	@echo "  make lint       - Run code linter (ruff)"
	@echo "  make format     - Format code (ruff)"
	@echo "  make check      - Run linter and tests"

# Install dependencies
install:
	uv sync

# Run tests
test:
	uv run pytest test_main.py -v

# Run tests with coverage
test-cov:
	uv run pytest test_main.py -v --cov=main --cov-report=term-missing --cov-report=html

# Start development server
run:
# 	uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
	uv run uvicorn main:app --reload --host 0.0.0.0

# Clean cache and temporary files
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Lint code
lint:
	@command -v ruff >/dev/null 2>&1 && uv run ruff check . || echo "Ruff not installed. Run: uv pip install ruff"

# Format code
format:
	@command -v ruff >/dev/null 2>&1 && uv run ruff format . || echo "Ruff not installed. Run: uv pip install ruff"

# Check code quality and run tests
check: lint test
