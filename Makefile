.PHONY: help install format lint check test clean demo chat
.DEFAULT_GOAL := help

PYTHON_DIRS = src tests main.py

help: ## Show this help message
	@echo "MCP Sandbox - Available Make Commands"
	@echo "===================================="
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make install     # Install dependencies"
	@echo "  make demo        # Run demo mode"
	@echo "  make chat        # Run interactive chat"
	@echo "  make test        # Run test suite"

install: ## Install dependencies using Poetry
	@echo "🔧 Installing dependencies with Poetry..."
	poetry install
	@echo "✅ Dependencies installed successfully!"

format: ## Format code with ruff and isort
	@echo "🎨 Formatting code with ruff and isort..."
	poetry run ruff format $(PYTHON_DIRS)
	poetry run isort $(PYTHON_DIRS)
	@echo "✅ Code formatting complete!"

lint: ## Check code quality with ruff
	@echo "🔍 Checking code quality with ruff..."
	poetry run ruff check $(PYTHON_DIRS)
	@echo "✅ Linting check complete!"

check: ## Auto-fix code issues with ruff and isort
	@echo "🔧 Checking and fixing code issues..."
	poetry run ruff check $(PYTHON_DIRS) --fix
	poetry run isort $(PYTHON_DIRS)
	poetry run ruff format $(PYTHON_DIRS)
	@echo "✅ Code check and fixes complete!"

test: ## Run the test suite
	@echo "🧪 Running test suite..."
	poetry run pytest -v
	@echo "✅ Tests complete!"

demo: ## Run MCP demo
	@echo "🚀 Running MCP demo..."
	poetry run demo

chat: ## Start interactive chat
	@echo "💬 Starting interactive chat..."
	poetry run chat

clean: ## Clean up cache files and temporary directories
	@echo "🧹 Cleaning up cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name "*.pyo" -delete 2>/dev/null || true
	find . -name "*~" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete!"

dev-setup: install ## Complete development setup
	@echo "🛠️  Setting up development environment..."
	@if [ ! -f .envrc ]; then \
		echo "⚠️  .envrc not found. Please add your ANTHROPIC_API_KEY"; \
	else \
		echo "✅ .envrc found"; \
	fi
	@echo "🔧 Running initial code check..."
	$(MAKE) check
	@echo "🧪 Running tests to verify setup..."
	$(MAKE) test
	@echo "✅ Development environment setup complete!"

all: clean install check test ## Run complete CI pipeline
	@echo "🎉 All checks passed! Ready for deployment."
