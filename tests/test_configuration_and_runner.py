"""
Test configuration and runner for waterrocketpy.

This file provides utilities to run all tests and generate coverage reports.
"""

import pytest
import sys
import os
from pathlib import Path

# Add the waterrocketpy package to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all tests with coverage report."""
    
    # Test configuration
    pytest_args = [
        # Test files
        'tests/test_rocket_builder.py',
        'tests/test_simulator.py',
        
        # Coverage options
        '--cov=waterrocketpy',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-report=xml',
        
        # Output options
        '-v',  # verbose
        '--tb=short',  # shorter traceback format
        
        # Warnings
        '--disable-warnings',
        
        # Test discovery
        '--collect-only',  # Remove this line to actually run tests
    ]
    
    # Remove --collect-only to run tests
    if '--collect-only' in pytest_args:
        pytest_args.remove('--collect-only')
    
    return pytest.main(pytest_args)

def run_builder_tests():
    """Run only rocket builder tests."""
    return pytest.main([
        'tests/test_rocket_builder.py',
        '-v',
        '--tb=short'
    ])

def run_simulator_tests():
    """Run only simulator tests."""
    return pytest.main([
        'tests/test_simulator.py',
        '-v',
        '--tb=short'
    ])

def run_integration_tests():
    """Run integration tests that use both builder and simulator."""
    return pytest.main([
        'tests/test_integration.py',
        '-v',
        '--tb=short'
    ])

if __name__ == '__main__':
    print("Running waterrocketpy tests...")
    exit_code = run_all_tests()
    sys.exit(exit_code)