"""
Test that the docstrings from bindings_docstrings.py can be applied to the bindings module.

This test verifies that our approach for documenting auto-generated code works correctly
by checking if docstrings can be applied to the bindings module without errors.
"""

import importlib
import inspect
import sys
import pytest


def test_can_apply_docstrings():
    """Test that docstrings can be applied to bindings module."""
    # Import the docstrings module
    try:
        from saline_sdk.transaction.bindings_docstrings import (
            BINDINGS_MODULE_DOC,
            NON_EMPTY_DOC,
            TOKEN_DOC,
            RELATION_DOC,
            TRANSACTION_DOC,
            SIGNED_DOC
        )
    except ImportError:
        pytest.skip("bindings_docstrings.py module not found")

    # Import the bindings module
    from saline_sdk.transaction import bindings

    # Store original docstrings to restore later
    original_module_doc = bindings.__doc__

    # Classes to test docstring application
    classes_to_test = [
        ("NonEmpty", NON_EMPTY_DOC),
        ("Token", TOKEN_DOC),
        ("Relation", RELATION_DOC),
        ("Transaction", TRANSACTION_DOC),
        ("Signed", SIGNED_DOC)
    ]

    original_class_docs = {}

    # Save original docstrings for cleanup
    for class_name, _ in classes_to_test:
        if hasattr(bindings, class_name):
            cls = getattr(bindings, class_name)
            original_class_docs[class_name] = cls.__doc__

    try:
        # Apply docstrings
        bindings.__doc__ = BINDINGS_MODULE_DOC

        # Check module docstring was applied
        assert bindings.__doc__ == BINDINGS_MODULE_DOC

        # Apply and check class docstrings
        for class_name, doc in classes_to_test:
            if hasattr(bindings, class_name):
                cls = getattr(bindings, class_name)
                cls.__doc__ = doc
                assert cls.__doc__ == doc

    finally:
        # Restore original docstrings
        bindings.__doc__ = original_module_doc

        for class_name, original_doc in original_class_docs.items():
            if hasattr(bindings, class_name):
                cls = getattr(bindings, class_name)
                cls.__doc__ = original_doc


def test_bindings_module_has_required_classes():
    """Test that the bindings module contains the expected classes."""
    from saline_sdk.transaction import bindings

    # Check that essential classes exist
    required_classes = [
        "NonEmpty",
        "Token",
        "Relation",
        "Transaction",
        "Signed",
    ]

    for class_name in required_classes:
        assert hasattr(bindings, class_name), f"bindings module missing {class_name} class"

    # Check that essential functions exist
    required_functions = [
        "dumps",
        "loads",
    ]

    for func_name in required_functions:
        assert hasattr(bindings, func_name), f"bindings module missing {func_name} function"
