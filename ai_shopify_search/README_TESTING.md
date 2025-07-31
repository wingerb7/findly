# Testing and Quality Assurance

This document describes how to run tests and quality checks locally for the Findly AI Search project.

## Prerequisites

Make sure you have the following installed:
- Python 3.9+ 
- pip
- Redis (for integration tests)

## Installation

1. Install the project dependencies:
```bash
pip install -r requirements.txt
```

2. Install development dependencies:
```bash
pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-xdist
pip install flake8 mypy radon black isort bandit
```

## Running Tests

### Unit Tests
Run all unit tests with coverage:
```bash
python -m pytest tests/unit/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

Run specific test files:
```bash
python -m pytest tests/unit/test_background_tasks.py -v
python -m pytest tests/unit/test_analytics_manager.py -v
python -m pytest tests/unit/test_intent.py -v
```

### Integration Tests
Run integration tests (requires Redis):
```bash
python -m pytest tests/integration/ -v
```

### API Tests
Run API endpoint tests:
```bash
python -m pytest tests/test_api_endpoints.py -v
```

### All Tests
Run all tests:
```bash
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80
```

## Code Quality Checks

### Linting (flake8)
Check code style and potential errors:
```bash
# Check for errors only
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Check style with complexity limits
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics
```

### Type Checking (mypy)
Check type annotations:
```bash
mypy . --ignore-missing-imports --disallow-untyped-defs --disallow-incomplete-defs
```

### Code Complexity (radon)
Analyze code complexity:
```bash
# Cyclomatic complexity
radon cc . -a -s --min C

# Maintainability index
radon mi . -s

# Raw metrics
radon raw . -s
```

### Code Formatting

#### Check formatting (Black)
```bash
black --check --diff .
```

#### Format code (Black)
```bash
black .
```

#### Check import sorting (isort)
```bash
isort --check-only --diff .
```

#### Sort imports (isort)
```bash
isort .
```

### Security Checks (bandit)
Run security analysis:
```bash
bandit -r . -f json -o bandit-report.json
bandit -r . -f txt -o bandit-report.txt
```

## Running All Checks

### Using the test runner script
```bash
python run_tests.py
```

### Manual comprehensive check
```bash
# 1. Run tests with coverage
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80

# 2. Run linting
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

# 3. Run type checking
mypy . --ignore-missing-imports --disallow-untyped-defs --disallow-incomplete-defs

# 4. Run complexity analysis
radon cc . -a -s --min C
radon mi . -s

# 5. Check formatting
black --check --diff .
isort --check-only --diff .

# 6. Run security checks
bandit -r . -f json -o bandit-report.json
```

## Test Coverage

The project maintains a minimum test coverage of **80%**. Coverage reports are generated in multiple formats:

- **Terminal output**: Shows missing lines
- **HTML report**: Detailed coverage report in `htmlcov/index.html`
- **XML report**: For CI/CD integration

### Coverage Targets by Module

| Module | Current Coverage | Target |
|--------|------------------|--------|
| background_tasks.py | 100% | 80% |
| performance_monitor.py | 100% | 80% |
| intent.py | 100% | 80% |
| analytics_manager.py | 85% | 80% |
| api/products_v2.py | 80% | 80% |
| services/ai_search_service.py | 78% | 80% |
| utils/error_handling.py | 63% | 80% |
| utils/validation.py | 85% | 80% |

## Test Categories

### Unit Tests
- **Location**: `tests/unit/`
- **Purpose**: Test individual functions and classes in isolation
- **Mocking**: External dependencies are mocked
- **Speed**: Fast execution

### Integration Tests
- **Location**: `tests/integration/`
- **Purpose**: Test component interactions
- **Dependencies**: May require Redis, database
- **Speed**: Slower than unit tests

### API Tests
- **Location**: `tests/test_api_endpoints.py`
- **Purpose**: Test HTTP endpoints
- **Mocking**: Database and external services mocked
- **Speed**: Medium execution time

## Writing Tests

### Test Structure
```python
#!/usr/bin/env python3
"""
Unit tests for module_name.py
Tests functionality, edge cases, and error scenarios.
"""

import pytest
from unittest.mock import Mock, patch
from module_name import function_name

class TestFunctionName:
    """Test function_name functionality."""
    
    def test_happy_path(self):
        """Test normal operation."""
        result = function_name("test_input")
        assert result == "expected_output"
    
    def test_edge_case(self):
        """Test edge case handling."""
        result = function_name("")
        assert result is None
    
    def test_error_handling(self):
        """Test error scenarios."""
        with pytest.raises(ValueError):
            function_name(None)
```

### Test Guidelines

1. **Test Coverage**: Aim for 100% coverage of new code
2. **Test Names**: Use descriptive names that explain what is being tested
3. **Docstrings**: Include docstrings explaining test purpose
4. **Mocking**: Mock external dependencies to isolate units
5. **Edge Cases**: Test boundary conditions and error scenarios
6. **Performance**: Keep tests fast and efficient

### Async Tests
For testing async functions:
```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result == "expected"
```

### Mocking Examples
```python
@patch('module.external_service')
def test_with_mock(mock_service):
    """Test with mocked external service."""
    mock_service.return_value = "mocked_result"
    result = function_under_test()
    assert result == "mocked_result"
```

## Continuous Integration

The project uses GitHub Actions for CI/CD with the following checks:

1. **Tests**: Unit, integration, and API tests with coverage
2. **Linting**: flake8 style and error checking
3. **Type Checking**: mypy type validation
4. **Complexity**: radon complexity analysis
5. **Security**: bandit security scanning
6. **Formatting**: black and isort checks

### Local CI Simulation
To run all CI checks locally:
```bash
# Create a script to run all checks
cat > run_ci.sh << 'EOF'
#!/bin/bash
set -e

echo "🧪 Running tests..."
python -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80

echo "🔍 Running linting..."
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics

echo "📝 Checking types..."
mypy . --ignore-missing-imports --disallow-untyped-defs --disallow-incomplete-defs

echo "📊 Checking complexity..."
radon cc . -a -s --min C

echo "🎨 Checking formatting..."
black --check --diff .
isort --check-only --diff .

echo "🔒 Running security checks..."
bandit -r . -f json -o bandit-report.json

echo "✅ All checks passed!"
EOF

chmod +x run_ci.sh
./run_ci.sh
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're in the correct directory (`ai_shopify_search/`)
2. **Redis Connection**: For integration tests, ensure Redis is running
3. **Coverage Issues**: Check that all code paths are tested
4. **Type Errors**: Add proper type annotations to functions

### Performance Tips

1. **Parallel Testing**: Use `pytest-xdist` for parallel test execution
2. **Test Selection**: Use `-k` flag to run specific tests
3. **Coverage Optimization**: Focus on uncovered lines first

### Getting Help

- Check the test output for specific error messages
- Review the coverage report to identify untested code
- Consult the pytest documentation for advanced features
- Check the project's test examples for patterns

## Contributing

When contributing new code:

1. Write tests for all new functionality
2. Ensure tests pass locally before submitting
3. Maintain or improve test coverage
4. Follow the established test patterns
5. Update this documentation if needed 