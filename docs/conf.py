"""
Sphinx configuration for Saline SDK documentation.
"""

import os
import sys
import inspect
import importlib
from pathlib import Path
from datetime import datetime

# Add the project root to the path so we can import the package
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup mock modules for ReadTheDocs build
try:
    import mock
    # Import our mock modules script
    from docs import mock_modules
    print("Using mock modules for documentation build.")
except ImportError:
    print("Mock modules not used - assuming full environment is available.")

# -- Apply docstrings to bindings.py ---------------------------------------

# Check if the saline_sdk package is available
try:
    import saline_sdk
    SALINE_SDK_AVAILABLE = True
except ImportError:
    SALINE_SDK_AVAILABLE = False
    print("Warning: saline_sdk package not found. Documentation may be incomplete.")

# Import the module with docstrings
try:
    from saline_sdk.transaction.bindings_docstrings import *
    BINDINGS_DOCSTRINGS_AVAILABLE = True

    # Import bindings module
    import saline_sdk.transaction.bindings as bindings

    # Add module docstring
    if BINDINGS_MODULE_DOC:
        bindings.__doc__ = BINDINGS_MODULE_DOC

    # Apply docstrings to NonEmpty class and methods
    if hasattr(bindings, 'NonEmpty'):
        bindings.NonEmpty.__doc__ = NON_EMPTY_DOC
        if hasattr(bindings.NonEmpty, '__init__'):
            bindings.NonEmpty.__init__.__doc__ = NON_EMPTY_INIT_DOC
        if hasattr(bindings.NonEmpty, 'from_list'):
            bindings.NonEmpty.from_list.__doc__ = NON_EMPTY_FROM_LIST_DOC

    # Apply docstrings to enum classes
    if hasattr(bindings, 'Relation'):
        bindings.Relation.__doc__ = RELATION_DOC
    if hasattr(bindings, 'Token'):
        bindings.Token.__doc__ = TOKEN_DOC
    if hasattr(bindings, 'Arithmetic'):
        bindings.Arithmetic.__doc__ = ARITHMETIC_DOC

    # Apply docstrings to witness classes
    if hasattr(bindings, 'Witness'):
        bindings.Witness.__doc__ = WITNESS_DOC
    if hasattr(bindings, 'AllW'):
        bindings.AllW.__doc__ = ALLW_DOC
    if hasattr(bindings, 'AnyW'):
        bindings.AnyW.__doc__ = ANYW_DOC
    if hasattr(bindings, 'AutoW'):
        bindings.AutoW.__doc__ = AUTOW_DOC

    # Apply docstrings to expression classes
    if hasattr(bindings, 'Expr'):
        bindings.Expr.__doc__ = EXPR_DOC
    if hasattr(bindings, 'Lit'):
        bindings.Lit.__doc__ = LIT_DOC
    if hasattr(bindings, 'Receive'):
        bindings.Receive.__doc__ = RECEIVE_DOC
    if hasattr(bindings, 'Send'):
        bindings.Send.__doc__ = SEND_DOC
    if hasattr(bindings, 'Var'):
        bindings.Var.__doc__ = VAR_DOC
    if hasattr(bindings, 'Arithmetic2'):
        bindings.Arithmetic2.__doc__ = ARITHMETIC2_DOC

    # Apply docstrings to intent classes
    if hasattr(bindings, 'Intent'):
        bindings.Intent.__doc__ = INTENT_DOC
    if hasattr(bindings, 'All'):
        bindings.All.__doc__ = ALL_DOC
    if hasattr(bindings, 'Any'):
        bindings.Any.__doc__ = ANY_DOC
    if hasattr(bindings, 'Restriction'):
        bindings.Restriction.__doc__ = RESTRICTION_DOC
    if hasattr(bindings, 'Limited'):
        bindings.Limited.__doc__ = LIMITED_DOC
    if hasattr(bindings, 'Signature'):
        bindings.Signature.__doc__ = SIGNATURE_DOC

    # Apply docstrings to bridge instruction classes
    if hasattr(bindings, 'BridgeInstruction'):
        bindings.BridgeInstruction.__doc__ = BRIDGE_INSTRUCTION_DOC
    if hasattr(bindings, 'Burn'):
        bindings.Burn.__doc__ = BURN_DOC
    if hasattr(bindings, 'Mint'):
        bindings.Mint.__doc__ = MINT_DOC

    # Apply docstrings to instruction classes
    if hasattr(bindings, 'Instruction'):
        bindings.Instruction.__doc__ = INSTRUCTION_DOC
    if hasattr(bindings, 'TransferRights'):
        bindings.TransferRights.__doc__ = TRANSFER_RIGHTS_DOC
    if hasattr(bindings, 'TransferFunds'):
        bindings.TransferFunds.__doc__ = TRANSFER_FUNDS_DOC
    if hasattr(bindings, 'OrIntent'):
        bindings.OrIntent.__doc__ = OR_INTENT_DOC
    if hasattr(bindings, 'SetIntent'):
        bindings.SetIntent.__doc__ = SET_INTENT_DOC
    if hasattr(bindings, 'Delete'):
        bindings.Delete.__doc__ = DELETE_DOC
    if hasattr(bindings, 'Bridge'):
        bindings.Bridge.__doc__ = BRIDGE_DOC

    # Apply docstrings to transaction classes
    if hasattr(bindings, 'Transaction'):
        bindings.Transaction.__doc__ = TRANSACTION_DOC
    if hasattr(bindings, 'Signed'):
        bindings.Signed.__doc__ = SIGNED_DOC

except ImportError:
    BINDINGS_DOCSTRINGS_AVAILABLE = False
    print("Note: bindings_docstrings module not available. API documentation will have limited details.")
    # Continue with the documentation build, but without the enhanced docstrings

# -- Project information -----------------------------------------------------

project = 'Saline SDK'
copyright = f'{datetime.now().year}, Rising Sea Labs'
author = 'Rising Sea Labs'

# The full version, including alpha/beta/rc tags
release = '0.1.0'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.autosummary',
    'sphinx_autodoc_typehints',
    'myst_parser',
]

# Add any paths that contain templates here, relative to this directory
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing
todo_include_todos = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
html_theme_options = {
    'navigation_depth': 4,
    'collapse_navigation': False,
    'sticky_navigation': True,
    'display_version': True,
    'includehidden': True,
    'titles_only': False,
    'prev_next_buttons_location': 'both',
}

# Add any paths that contain custom static files (such as style sheets)
html_static_path = ['_static']

# Add custom CSS files
html_css_files = [
    'custom.css',
]

# -- Extension configuration -------------------------------------------------

# AutoDoc options
autodoc_member_order = 'groupwise'
autodoc_typehints = 'description'
autoclass_content = 'both'

# Napoleon settings
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False

# Intersphinx mappings
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'aiohttp': ('https://docs.aiohttp.org/en/stable/', None),
}

# MyST Parser settings
myst_enable_extensions = [
    'colon_fence',
    'deflist',
]

# Make the master doc index
master_doc = 'index'

# Keep the sidebar
html_sidebars = {
    '**': [
        'globaltoc.html',
        'searchbox.html',
    ]
}
