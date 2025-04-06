"""
Configuration and fixtures for the unit tests.
"""

import pytest
import os
import os.path
from unittest.mock import MagicMock, patch
from saline_sdk.saline import Saline
from saline_sdk.account import Account

TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"

@pytest.fixture
def test_client():
    """Create a mock client."""
    with patch('saline_sdk.saline.Client') as mock_client:
        client = mock_client.return_value
        client.get_status = MagicMock(return_value={"node_info": {"version": "1.0.0"}})
        client.get_balance = MagicMock(return_value=100.0)
        client.get_all_balances = MagicMock(return_value={"USDC": 100.0, "BTC": 0.5})
        client.get_intent = MagicMock(return_value={"condition": "signature"})
        client.tx_commit = MagicMock(return_value={"hash": "tx_hash"})
        client.tx_broadcast = MagicMock(return_value={"hash": "tx_hash"})
        yield client

@pytest.fixture
def saline_instance(test_client):
    """Create a Saline instance with a mock client."""
    with patch('saline_sdk.saline.Client', return_value=test_client):
        saline = Saline(node_url="http://fake-node:26657", mnemonic=TEST_MNEMONIC)
        yield saline

@pytest.fixture
def test_account():
    """Create a test account."""
    return Account.from_mnemonic(TEST_MNEMONIC)

@pytest.fixture
def fixtures_path():
    """Get the path to the fixtures directory."""
    # Try different relative paths to find the fixtures directory
    possible_paths = [
        'tests/fixtures',
        'saline-sdk/tests/fixtures',

    ]
    
    for path in possible_paths:
        if os.path.isdir(path):
            return path
    
    # If no fixtures directory found, use a default path
    return 'tests/fixtures' 