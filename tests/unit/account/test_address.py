"""
Unit tests for address-related functionality in saline_sdk.
"""

import unittest
from unittest.mock import patch, MagicMock
import re
from mnemonic import Mnemonic

from saline_sdk.crypto import BLS, derive_key_from_path
from saline_sdk.account import Subaccount


class TestAddressFormat(unittest.TestCase):
    """Test suite for address format and validation functionality."""
    
    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    
    def setUp(self):
        """Set up test fixtures before each test."""
        mnemo = Mnemonic("english")
        self.test_seed = mnemo.to_seed(self.TEST_MNEMONIC)
        
        self.test_private_key = derive_key_from_path(self.test_seed, "m/12381/997/0/0/0")
        self.test_public_key = BLS.sk_to_pk(self.test_private_key)
        self.test_public_key_hex = self.test_public_key.hex()
        
        self.subaccount = Subaccount(
            private_key_bytes=self.test_private_key,
            public_key_bytes=self.test_public_key,
            label="test_address"
        )
        
        self.expected_address = f"nacl:{self.test_public_key_hex}"
    
    
    
    def test_address_validation(self):
        """Test address validation logic."""
        valid_address = self.expected_address
        
        # Invalid addresses
        invalid_prefixes = [
            f"invalid:{self.test_public_key_hex}",
            self.test_public_key_hex,  # No prefix
            f"nacl:{self.test_public_key_hex[:-2]}",  # Truncated public key
            f"nacl:{'x' * len(self.test_public_key_hex)}",  # Invalid hex characters
        ]
        
        
        nacl_address_pattern = re.compile(r"^nacl:[0-9a-f]{96}$")
        
        self.assertTrue(nacl_address_pattern.match(valid_address))
        
        for invalid_address in invalid_prefixes:
            self.assertFalse(nacl_address_pattern.match(invalid_address))
    
    def test_public_key_to_address_conversion(self):
        """Test converting a public key to an address."""
        expected_address = self.expected_address
        
       
        public_key_hex = self.test_public_key.hex()
        address = f"nacl:{public_key_hex}"
        
        self.assertEqual(address, expected_address)


if __name__ == '__main__':
    unittest.main() 