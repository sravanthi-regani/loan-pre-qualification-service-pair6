# Developer Guide - Local CI/CD Setup

This guide explains how to use the local CI/CD tools for the Loan Pre-Qualification Service.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Pre-commit Hooks](#pre-commit-hooks)
3. [Testing](#testing)
4. [Makefile Commands](#makefile-commands)
5. [Code Quality Tools](#code-quality-tools)
6. [Troubleshooting](#troubleshooting)

## Quick Start

### Initial Setup

1. **Install dependencies:**
   ```bash
   make install
   ```

2. **Setup pre-commit hooks:**
   ```bash
   make setup-hooks
   ```

3. **Run tests to verify setup:**
   ```bash
   make test
   ```

## Pre-commit Hooks

Pre-commit hooks automatically run code quality checks before each commit, ensuring code quality and consistency.

### What Gets Checked?

- **Ruff Linter**: Fast Python linter that checks for code quality issues
- **Ruff Formatter**: Fast Python formatter (alternative to Black)
- **Black**: Python code formatter that enforces PEP 8 style
- **Trailing Whitespace**: Removes unnecessary whitespace at line ends
- **End of File Fixer**: Ensures files end with a newline
- **YAML Syntax**: Validates YAML file syntax
- **Large Files**: Prevents accidentally committing large files
- **Merge Conflicts**: Checks for unresolved merge conflict markers
- **Debug Statements**: Detects debug statements like `import pdb`

### How It Works (AC 5.1)

**GIVEN** I have configured pre-commit
**WHEN** I try to git commit code that is poorly formatted (does not pass Black)
**THEN** my commit is rejected, and Black automatically formats the code for me.

#### Example Workflow:

```bash
# Stage your changes
git add .

# Try to commit (pre-commit hooks will run automatically)
git commit -m "Your commit message"

# If code is poorly formatted:
# - Commit will be REJECTED
# - Black and Ruff will automatically format your code
# - You'll see which files were modified
# - Simply stage the formatted files and commit again

git add .
git commit -m "Your commit message"
```

### Manual Pre-commit Execution

You can run pre-commit checks manually without committing:

```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

## Testing

The project includes comprehensive unit tests for all three services:
- **prequal-api**: 16 tests
- **credit-service**: 15 tests (CIBIL simulation logic)
- **decision-service**: 44 tests (decision rules)

### Running Tests (AC 5.2)

**GIVEN** I have made a logic change
**WHEN** I run `make test`
**THEN** pytest runs all unit tests for the API, credit, and decision services, and all tests pass.

#### Test Commands:

```bash
# Run all tests (simple output)
make test

# Run tests with verbose output
make test-verbose

# Run tests with coverage report
make test-coverage
```

### Test Structure

Each service has its own test suite:
- `prequal-api/app/test_main.py` - API endpoint tests
- `credit-service/app/test_cibil_simulator.py` - CIBIL score calculation tests
- `credit-service/app/test_main.py` - Credit service endpoint tests
- `decision-service/app/test_decision_engine.py` - Decision logic tests
- `decision-service/app/test_main.py` - Decision service endpoint tests

## Makefile Commands

The Makefile provides standardized commands for common development tasks:

| Command | Description |
|---------|-------------|
| `make help` | Display all available commands |
| `make install` | Install all Python dependencies |
| `make setup-hooks` | Install pre-commit git hooks |
| `make lint` | Run Ruff linter with auto-fix |
| `make format` | Run Black code formatter |
| `make test` | Run all unit tests |
| `make test-verbose` | Run tests with detailed output |
| `make test-coverage` | Run tests with coverage report |
| `make run-local` | Start all services with docker-compose |
| `make docker-up` | Start services in detached mode |
| `make docker-down` | Stop all services |
| `make clean` | Remove cache and temporary files |

## Code Quality Tools

### Black

Black is an opinionated Python code formatter that enforces a consistent style.

**Configuration:** `pyproject.toml`
- Line length: 88 characters
- Target: Python 3.9+

**Manual usage:**
```bash
# Format all Python files
make format

# Or use Black directly
black .

# Check what would be formatted (dry run)
black --check .
```

### Ruff

Ruff is a fast Python linter and formatter written in Rust.

**Configuration:** `ruff.toml`
- Enabled rules: pycodestyle (E), Pyflakes (F), isort (I), warnings (W)
- Line length: 88 characters
- Target: Python 3.9+

**Manual usage:**
```bash
# Run linter with auto-fix
make lint

# Or use Ruff directly
ruff check . --fix

# Check without fixing
ruff check .
```

### pytest

pytest is the testing framework used for all unit tests.

**Configuration:** `pytest.ini` (per service) and `pyproject.toml`

**Manual usage:**
```bash
# Run tests for a specific service
cd prequal-api && pytest -v
cd credit-service && pytest -v
cd decision-service && pytest -v

# Run a specific test file
pytest credit-service/app/test_cibil_simulator.py -v

# Run a specific test
pytest credit-service/app/test_cibil_simulator.py::TestCIBILSimulator::test_predefined_test_pan_1 -v
```

## Troubleshooting

### Pre-commit Hook Issues

**Problem:** Pre-commit hooks fail to install
```bash
# Solution: Reinstall pre-commit
pip install --upgrade pre-commit
pre-commit install
```

**Problem:** Hooks are not running
```bash
# Solution: Verify hooks are installed
pre-commit install

# Check if hooks are in .git/hooks/
ls -la .git/hooks/pre-commit
```

**Problem:** Want to bypass hooks temporarily (NOT RECOMMENDED)
```bash
# Use --no-verify flag (use with caution)
git commit --no-verify -m "Message"
```

### Test Issues

**Problem:** Tests fail due to import errors
```bash
# Solution: Ensure you're in the correct directory or PYTHONPATH is set
cd prequal-api && pytest
# OR
cd credit-service && pytest
# OR
cd decision-service && pytest
```

**Problem:** Pytest not found
```bash
# Solution: Ensure dependencies are installed
make install
# OR
pip install pytest pytest-asyncio httpx
```

### Formatting Issues

**Problem:** Black and Ruff disagree on formatting
```bash
# Solution: Run both tools
make format
make lint
```

**Problem:** Line too long errors persist
```bash
# Solution: Manually break long lines, especially comments
# Bad:
# This is a very long comment that exceeds the 88 character limit for code formatting

# Good:
# This is a very long comment that exceeds the 88 character limit
# for code formatting
```

## Best Practices

1. **Always run tests before pushing:**
   ```bash
   make test
   ```

2. **Format code regularly:**
   ```bash
   make format
   make lint
   ```

3. **Use meaningful commit messages:**
   ```bash
   git commit -m "feat: Add CIBIL score validation logic"
   git commit -m "fix: Resolve decision engine threshold bug"
   git commit -m "test: Add edge case tests for income calculation"
   ```

4. **Run tests for the specific service you're working on:**
   ```bash
   cd credit-service && pytest -v
   ```

5. **Check coverage to ensure adequate testing:**
   ```bash
   make test-coverage
   ```

## Development Workflow

Recommended workflow for making changes:

```bash
# 1. Create a new branch
git checkout -b feature/your-feature-name

# 2. Make your changes
# ... edit files ...

# 3. Format code
make format
make lint

# 4. Run tests
make test

# 5. Stage and commit (pre-commit hooks will run)
git add .
git commit -m "Your commit message"

# 6. If hooks fail, fix issues and recommit
git add .
git commit -m "Your commit message"

# 7. Push to remote
git push origin feature/your-feature-name
```

## Summary

- **AC 5.1** is satisfied: Pre-commit hooks automatically reject poorly formatted code and format it with Black
- **AC 5.2** is satisfied: `make test` runs all unit tests for API, credit, and decision services
- All tools (Poetry alternative: pip, Docker Compose, pre-commit, pytest, Makefile) are configured and working
- Code quality is enforced through Ruff (lint) and Black (format) on every commit
- Unit tests cover all business logic (CIBIL simulation, decision rules) and API endpoints
