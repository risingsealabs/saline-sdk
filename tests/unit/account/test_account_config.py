"""
Unit tests for account configuration functionality in saline_sdk.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import re
from mnemonic import Mnemonic

from saline_sdk.account import Account, Subaccount
from saline_sdk.crypto import derive_key_from_path


class TestAccountConfig(unittest.TestCase):
    """Test suite for account configuration and initialization functionality."""
    
    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Create a test seed from the mnemonic
        mnemo = Mnemonic("english")
        self.test_seed = mnemo.to_seed(self.TEST_MNEMONIC)
        
        # Test paths
        self.valid_base_path = "m/12381/997"
        self.valid_full_path = "m/12381/997/0/0/0"
        self.invalid_path = "m/invalid/path"
    
    def test_derive_key_from_path(self):
        """Test deriving a key from a valid path."""
        # Test deriving with valid path
        try:
            key = derive_key_from_path(self.test_seed, self.valid_full_path)
            self.assertIsNotNone(key)
            self.assertTrue(isinstance(key, bytes))
            self.assertEqual(len(key), 32)  # BLS private key should be 32 bytes
        except Exception as e:
            self.fail(f"derive_key_from_path raised exception unexpectedly: {e}")
    
    def test_validate_path(self):
        """Test validating derivation paths."""
        # Test with valid paths
        try:
            # Since there's no dedicated path validation function exposed,
            # we'll test by using derive_key_from_path which validates internally
            derive_key_from_path(self.test_seed, self.valid_base_path)
            derive_key_from_path(self.test_seed, self.valid_full_path)
        except Exception as e:
            self.fail(f"Path validation failed unexpectedly: {e}")
        
        # Test with invalid path
        with self.assertRaises(ValueError):
            derive_key_from_path(self.test_seed, self.invalid_path)
        
        # Test with non-BIP44 paths
        non_bip44_paths = [
            "m",                 # Too short
            "m/12381",           # Too short
            "m/not/a/number",    # Not numeric
            "12381/997/0/0/0",   # Missing 'm' prefix
            "m/12381/997/0/0/0/0"  # Too many segments
        ]
        
        for path in non_bip44_paths:
            with self.assertRaises(ValueError):
                derive_key_from_path(self.test_seed, path)
    
    def test_account_base_path(self):
        """Test setting and retrieving the account base path."""
        # Default base path
        account = Account.from_mnemonic(self.TEST_MNEMONIC)
        self.assertEqual(account.base_path, "m/12381/997")
        
        # Custom base path
        custom_path = "m/12381/997/1"
        account = Account.from_mnemonic(self.TEST_MNEMONIC, base_path=custom_path)
        self.assertEqual(account.base_path, custom_path)
        
        # Invalid base path
        with self.assertRaises(ValueError):
            Account.from_mnemonic(self.TEST_MNEMONIC, base_path=self.invalid_path)
    
    def test_account_subaccount_path_generation(self):
        """Test generating subaccount paths from base path."""
        account = Account.from_mnemonic(self.TEST_MNEMONIC)
        
        # Create subaccounts and check their paths
        subaccount1 = account.create_subaccount("sub1")
        subaccount2 = account.create_subaccount("sub2")
        subaccount3 = account.create_subaccount("sub3")
        
        # Paths should be incrementing from the base path
        self.assertEqual(subaccount1.path, "m/12381/997/0/0/0")
        self.assertEqual(subaccount2.path, "m/12381/997/0/0/1")
        self.assertEqual(subaccount3.path, "m/12381/997/0/0/2")
        
        # Custom full path
        custom_path = "m/12381/997/1/2/3"
        subaccount_custom = account.create_subaccount("custom", custom_path)
        self.assertEqual(subaccount_custom.path, custom_path)
    
    def test_mnemonic_validation(self):
        """Test that mnemonic validation works correctly."""
        # Valid mnemonic
        try:
            Account.from_mnemonic(self.TEST_MNEMONIC)
        except Exception as e:
            self.fail(f"Account.from_mnemonic raised exception unexpectedly for valid mnemonic: {e}")
        
        # Invalid mnemonic (wrong number of words)
        invalid_mnemonic = "excuse ozone east canoe"
        with self.assertRaises(ValueError):
            Account.from_mnemonic(invalid_mnemonic)
        
        # Invalid mnemonic (invalid checksum)
        invalid_checksum = "excuse ozone east canoe duck tortoise dentist approve bid wagon area area"
        with self.assertRaises(ValueError):
            Account.from_mnemonic(invalid_checksum)
    
    def test_seed_generation(self):
        """Test that seed generation works consistently."""
        # Generate seed from mnemonic
        mnemo = Mnemonic("english")
        seed1 = mnemo.to_seed(self.TEST_MNEMONIC)
        seed2 = mnemo.to_seed(self.TEST_MNEMONIC)
        
        # Seeds should be deterministic
        self.assertEqual(seed1, seed2)
        
        # Different mnemonics should produce different seeds
        different_mnemonic = Mnemonic("english").generate(strength=256)
        different_seed = mnemo.to_seed(different_mnemonic)
        self.assertNotEqual(seed1, different_seed)


if __name__ == '__main__':
    unittest.main() 