.PHONY: help install setup-hooks lint format test test-verbose test-coverage run-local clean docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  make install       - Install all dependencies"
	@echo "  make setup-hooks   - Install pre-commit hooks"
	@echo "  make lint          - Run Ruff linter on all Python files"
	@echo "  make format        - Run Black formatter on all Python files"
	@echo "  make test          - Run all pytest unit tests"
	@echo "  make test-verbose  - Run tests with verbose output"
	@echo "  make test-coverage - Run tests with coverage report"
	@echo "  make run-local     - Run all services locally with docker-compose"
	@echo "  make docker-up     - Start all services in detached mode"
	@echo "  make docker-down   - Stop all services"
	@echo "  make clean         - Clean up cache and temporary files"

# Install dependencies
install:
	pip install -r requirements.txt

# Setup pre-commit hooks
setup-hooks:
	pre-commit install
	@echo "Pre-commit hooks installed successfully!"

# Run linter
lint:
	@echo "Running Ruff linter..."
	ruff check . --fix

# Run formatter
format:
	@echo "Running Black formatter..."
	black .

# Run all unit tests
test:
	@echo "Running tests for prequal-api..."
	PYTHONPATH=. pytest prequal-api/app -v
	@echo "\nRunning tests for credit-service..."
	PYTHONPATH=. pytest credit-service/app -v
	@echo "\nRunning tests for decision-service..."
	PYTHONPATH=. pytest decision-service/app -v
	@echo "\n✓ All tests passed!"

# Run tests with verbose output
test-verbose:
	@echo "Running tests for prequal-api..."
	PYTHONPATH=. pytest prequal-api/app -vv
	@echo "\nRunning tests for credit-service..."
	PYTHONPATH=. pytest credit-service/app -vv
	@echo "\nRunning tests for decision-service..."
	PYTHONPATH=. pytest decision-service/app -vv

# Run tests with coverage
test-coverage:
	@echo "Running tests with coverage for prequal-api..."
	PYTHONPATH=. pytest prequal-api/app --cov=prequal-api/app --cov-report=term-missing
	@echo "\nRunning tests with coverage for credit-service..."
	PYTHONPATH=. pytest credit-service/app --cov=credit-service/app --cov-report=term-missing
	@echo "\nRunning tests with coverage for decision-service..."
	PYTHONPATH=. pytest decision-service/app --cov=decision-service/app --cov-report=term-missing

# Run all services locally
run-local:
	@echo "Starting all services with docker-compose..."
	docker-compose up

# Start services in detached mode
docker-up:
	@echo "Starting all services in detached mode..."
	docker-compose up -d
	@echo "Services are running. Use 'docker-compose logs -f' to view logs."

# Stop all services
docker-down:
	@echo "Stopping all services..."
	docker-compose down

# Clean up cache and temporary files
clean:
	@echo "Cleaning up cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@echo "Cleanup complete!"
