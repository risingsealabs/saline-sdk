#!/usr/bin/env python3
"""
This module sets up mock objects for external dependencies that might be
difficult to install in the ReadTheDocs build environment, especially those
with C extensions like blspy.
"""

import sys
from unittest.mock import MagicMock

# List of modules to mock
MOCK_MODULES = [
    'blspy',
    'mnemonic',
    'websockets',
    'bitstring',
    'bitarray',
    'aiohttp',
    'httpx',
    'numpy'
]

# Create mock objects for these modules
class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
        return MagicMock()

# Apply the mocks to sys.modules
for mod_name in MOCK_MODULES:
    sys.modules[mod_name] = Mock()

print("Mock modules installed for documentation building.") 