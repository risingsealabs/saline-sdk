"""
Unit tests for the key derivation functionality in saline_sdk.crypto.key_derivation.
"""

import unittest
from unittest.mock import patch, MagicMock
import hashlib
import hmac
from typing import Optional
from mnemonic import Mnemonic

from saline_sdk.crypto import (
    derive_key_from_path,
    derive_master_SK,
    derive_child_SK,
    BLS
)


class TestKeyDerivation(unittest.TestCase):
    """Test suite for key derivation functionality."""
    
    # Test vector mnemonic from EIP-2333 or standard test vectors
    TEST_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    ALTERNATE_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Create test seeds from mnemonics
        mnemo = Mnemonic("english")
        self.test_seed = mnemo.to_seed(self.TEST_MNEMONIC)
        self.alternate_seed = mnemo.to_seed(self.ALTERNATE_MNEMONIC)
        
        # Common test paths
        self.valid_base_path = "m/12381/997"
        self.valid_account_path = "m/12381/997/0"
        self.valid_full_path = "m/12381/997/0/0/0"
        self.invalid_path = "m/invalid/path"
    
    def test_validate_path(self):
        """Test path validation logic."""
        # Test with valid paths
        try:
            derive_key_from_path(self.test_seed, self.valid_base_path)
            derive_key_from_path(self.test_seed, self.valid_account_path)
            derive_key_from_path(self.test_seed, self.valid_full_path)
        except Exception as e:
            self.fail(f"Path validation failed unexpectedly: {e}")
        
        # Test with invalid paths
        with self.assertRaises(ValueError):
            derive_key_from_path(self.test_seed, self.invalid_path)
            
        with self.assertRaises(ValueError):
            derive_key_from_path(self.test_seed, "not_a_path")
            
        with self.assertRaises(ValueError):
            derive_key_from_path(self.test_seed, "m/not/numbers")
            
        with self.assertRaises(ValueError):
            derive_key_from_path(self.test_seed, "12381/997/0")  # Missing 'm/' prefix
    
    def test_derive_master_SK(self):
        """Test derivation of the master key from a seed."""
        master_key = derive_master_SK(self.test_seed)
        
        self.assertIsNotNone(master_key)
        self.assertTrue(isinstance(master_key, bytes))
        self.assertEqual(len(master_key), 32)  # BLS private key should be 32 bytes
        
            
        master_key2 = derive_master_SK(self.test_seed)
        self.assertEqual(master_key, master_key2)
        
        different_master_key = derive_master_SK(self.alternate_seed)
        self.assertNotEqual(master_key, different_master_key)
    
    def test_derive_child_SK(self):
        """Test derivation of child keys from parent keys."""
        master_key = derive_master_SK(self.test_seed)
        
        index = 12381
        child_key = derive_child_SK(master_key, index)
        
        self.assertIsNotNone(child_key)
        self.assertTrue(isinstance(child_key, bytes))
        self.assertEqual(len(child_key), 32)
        
        child_key2 = derive_child_SK(master_key, index)
        self.assertEqual(child_key, child_key2)
        
        different_index = 997
        different_child_key = derive_child_SK(master_key, different_index)
        self.assertNotEqual(child_key, different_child_key)
        
        different_master_key = derive_master_SK(self.alternate_seed)
        different_parent_child_key = derive_child_SK(different_master_key, index)
        self.assertNotEqual(child_key, different_parent_child_key)
    
    def test_derive_key_from_path(self):
        """Test derivation of a key from a path."""
        key1 = derive_key_from_path(self.test_seed, self.valid_base_path)
        key2 = derive_key_from_path(self.test_seed, self.valid_account_path)
        key3 = derive_key_from_path(self.test_seed, self.valid_full_path)
        
        # Verify keys are valid private keys
        for key in [key1, key2, key3]:
            self.assertIsNotNone(key)
            self.assertTrue(isinstance(key, bytes))
            self.assertEqual(len(key), 32)
        
        self.assertNotEqual(key1, key2)
        self.assertNotEqual(key2, key3)
        self.assertNotEqual(key1, key3)
        
        key1_repeat = derive_key_from_path(self.test_seed, self.valid_base_path)
        self.assertEqual(key1, key1_repeat)
        
        with self.assertRaises(ValueError):
            derive_key_from_path(self.test_seed, self.invalid_path)
    
    def test_path_consistency(self):
        """Test that longer paths are consistent with shorter paths plus child derivation."""
        base_key = derive_key_from_path(self.test_seed, self.valid_base_path)
        
        account_path = f"{self.valid_base_path}/0"
        account_key = derive_key_from_path(self.test_seed, account_path)
        
        account_key_manual = derive_child_SK(base_key, 0)
        self.assertEqual(account_key, account_key_manual)
    
    
    def test_mnemonic_to_key_consistency(self):
        """Test full path from mnemonic to derived keys."""
        mnemo = Mnemonic("english")
        new_mnemonic = mnemo.generate(strength=256)
        new_seed = mnemo.to_seed(new_mnemonic)
        
        master_key = derive_master_SK(new_seed)
        
        key1 = derive_key_from_path(new_seed, "m/12381/997/0/0/0")
        key2 = derive_key_from_path(new_seed, "m/12381/997/0/0/1")
        
        self.assertNotEqual(key1, key2)
        
        pubkey1 = BLS.sk_to_pk(key1)
        pubkey2 = BLS.sk_to_pk(key2)
        
        self.assertNotEqual(pubkey1, pubkey2)
    
    def test_sign_with_derived_key(self):
        """Test signature creation with a derived key."""
        key = derive_key_from_path(self.test_seed, self.valid_full_path)
        
        message = b"test message for signing"
        
        signature = BLS.sign(key, message)
        
        public_key = BLS.sk_to_pk(key)
        self.assertTrue(BLS.verify(public_key, message, signature))
        
        modified_message = b"modified test message"
        self.assertFalse(BLS.verify(public_key, modified_message, signature))


if __name__ == '__main__':
    unittest.main()
