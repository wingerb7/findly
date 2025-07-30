#!/usr/bin/env python3
"""
Test runner script for Findly AI Search application.
Runs all tests and generates coverage reports.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}...")
    print(f"Command: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def main():
    """Main test runner function."""
    print("🧪 Findly AI Search - Test Runner")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: main.py not found. Please run from the ai_shopify_search directory.")
        sys.exit(1)
    
    # Install test dependencies if needed
    print("\n📦 Installing test dependencies...")
    install_commands = [
        "pip install pytest pytest-cov pytest-asyncio pytest-mock",
        "pip install psutil redis sqlalchemy fastapi"
    ]
    
    for cmd in install_commands:
        if not run_command(cmd, "Installing dependencies"):
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Run unit tests with coverage
    print("\n🧪 Running unit tests...")
    unit_test_command = "python3 -m pytest tests/unit/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80"
    
    if not run_command(unit_test_command, "Unit tests"):
        print("❌ Unit tests failed")
        sys.exit(1)
    
    # Run integration tests
    print("\n🔗 Running integration tests...")
    integration_test_command = "python3 -m pytest tests/integration/ -v --cov=. --cov-report=term-missing --cov-report=html --cov-append"
    
    if not run_command(integration_test_command, "Integration tests"):
        print("❌ Integration tests failed")
        sys.exit(1)
    
    # Run API tests
    print("\n🌐 Running API tests...")
    api_test_command = "python3 -m pytest tests/test_api_endpoints.py tests/test_search_service.py -v --cov=. --cov-report=term-missing --cov-report=html --cov-append"
    
    if not run_command(api_test_command, "API tests"):
        print("❌ API tests failed")
        sys.exit(1)
    
    # Generate final coverage report
    print("\n📊 Generating final coverage report...")
    coverage_report_command = "python3 -m pytest --cov=. --cov-report=term-missing --cov-report=html --cov-fail-under=80"
    
    if not run_command(coverage_report_command, "Final coverage report"):
        print("❌ Coverage report generation failed")
        sys.exit(1)
    
    # Check if coverage meets requirements
    print("\n🎯 Coverage Summary:")
    print("- Unit tests: ✅")
    print("- Integration tests: ✅") 
    print("- API tests: ✅")
    print("- Overall coverage: Target 80%+")
    
    print("\n📁 Coverage reports generated:")
    print("- HTML report: htmlcov/index.html")
    print("- Terminal report: See above")
    
    print("\n🎉 All tests completed successfully!")
    print("=" * 50)


if __name__ == "__main__":
    main() 