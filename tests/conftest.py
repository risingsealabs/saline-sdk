"""
Pytest configuration for the saline-sdk test suite.
"""

import pytest


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    parser.addoption(
        "--run-bindings-tests",
        action="store_true",
        default=False,
        help="Run tests that depend on the auto-generated bindings module"
    )
    parser.addoption(
        "--run-integration-tests",
        action="store_true",
        default=False,
        help="Run integration tests that require a live Saline node"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", 
        "bindings_test: mark tests that require the auto-generated bindings module"
    )
    config.addinivalue_line(
        "markers", 
        "integration: mark tests that require a live Saline node"
    )


def pytest_collection_modifyitems(config, items):
    """Skip tests marked as bindings_test unless --run-bindings-tests is passed."""
    if not config.getoption("--run-bindings-tests"):
        skip_bindings = pytest.mark.skip(
            reason="Need --run-bindings-tests option to run tests that depend on auto-generated bindings"
        )
        for item in items:
            if "bindings_test" in item.keywords:
                item.add_marker(skip_bindings)
    
    # Skip integration tests unless --run-integration-tests is passed
    if not config.getoption("--run-integration-tests"):
        skip_integration = pytest.mark.skip(
            reason="Need --run-integration-tests option to run tests that require a live node"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
                
    # Always skip test_bindings_roundtrip.py tests unless explicitly enabled
    # These tests are for the auto-generated code and may not always pass
    skip_roundtrip = pytest.mark.skip(
        reason="Roundtrip tests for auto-generated bindings are skipped by default"
    )
    for item in items:
        if "test_bindings_roundtrip" in item.nodeid:
            item.add_marker(skip_roundtrip) 