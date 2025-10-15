# Makefile for RAG Anything MCP Server
# Provides convenient commands for development and deployment

.PHONY: help install install-dev test lint format clean docker-build docker-run deploy

# Default target
.DEFAULT_GOAL := help

# Python interpreter
PYTHON := python
PIP := pip

# Docker
DOCKER := docker
DOCKER_COMPOSE := docker-compose

# Project
PROJECT_NAME := rag-anything-mcp
DOCKER_IMAGE := $(PROJECT_NAME):latest

help: ## Show this help message
	@echo "RAG Anything MCP Server - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: ## Install development dependencies
	$(PIP) install -r requirements-dev.txt
	pre-commit install

test: ## Run all tests
	pytest tests/ -v --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v -m integration

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -v

lint: ## Run linting checks
	flake8 src tests
	mypy src
	pylint src

format: ## Format code with black and isort
	black src tests
	isort src tests

format-check: ## Check code formatting without changes
	black --check src tests
	isort --check-only src tests

clean: ## Clean build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml

docker-build: ## Build Docker image
	$(DOCKER) build -t $(DOCKER_IMAGE) -f deployment/docker/Dockerfile .

docker-run: ## Run Docker container
	$(DOCKER) run -it --rm \
		-v $(PWD)/rag_storage:/app/rag_storage \
		-e OPENAI_API_KEY=$(OPENAI_API_KEY) \
		$(DOCKER_IMAGE)

docker-compose-up: ## Start services with docker-compose
	cd deployment/docker && $(DOCKER_COMPOSE) up -d

docker-compose-down: ## Stop services
	cd deployment/docker && $(DOCKER_COMPOSE) down

docker-compose-logs: ## View service logs
	cd deployment/docker && $(DOCKER_COMPOSE) logs -f

run: ## Run the MCP server locally
	$(PYTHON) main.py

dev: ## Run in development mode with auto-reload
	ENVIRONMENT=development DEBUG=true $(PYTHON) main.py

check: format-check lint test ## Run all checks (format, lint, test)

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

security: ## Run security checks
	bandit -r src -f json -o bandit-report.json
	safety check

docs: ## Generate documentation
	cd docs && mkdocs build

docs-serve: ## Serve documentation locally
	cd docs && mkdocs serve

setup: install-dev ## Setup development environment
	@echo "Development environment setup complete!"
	@echo "Don't forget to copy .env.example to .env and configure your settings."

release-patch: ## Bump patch version and create tag
	bump2version patch
	git push && git push --tags

release-minor: ## Bump minor version and create tag
	bump2version minor
	git push && git push --tags

release-major: ## Bump major version and create tag
	bump2version major
	git push && git push --tags
