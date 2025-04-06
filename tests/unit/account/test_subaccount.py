"""
Unit tests for the Subaccount class in saline_sdk.account module.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
from typing import Optional
from mnemonic import Mnemonic

from saline_sdk.account import Subaccount, Account
from saline_sdk.crypto import BLS, derive_key_from_path


class TestSubaccount(unittest.TestCase):
    """Test suite for Subaccount class functionality."""
    
    # Use the same test mnemonic from other test classes for consistency
    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    
    def setUp(self):
        """Set up test fixtures before each test."""
        # Generate derived keys from mnemonic instead of random keys
        mnemo = Mnemonic("english")
        self.test_seed = mnemo.to_seed(self.TEST_MNEMONIC)
        
        # Derive a deterministic private key from the seed
        self.test_private_key = derive_key_from_path(self.test_seed, "m/12381/997/0/0/0")
        self.test_public_key = BLS.sk_to_pk(self.test_private_key)
        self.test_label = "test_subaccount"
        self.test_path = "m/12381/997/0/0/0"
        
        # Create a test subaccount
        self.subaccount = Subaccount(
            private_key_bytes=self.test_private_key,
            public_key_bytes=self.test_public_key,
            path=self.test_path,
            label=self.test_label
        )
    
    def test_init_with_public_key(self):
        """Test initialization with provided public key."""
        subaccount = Subaccount(
            private_key_bytes=self.test_private_key,
            public_key_bytes=self.test_public_key,
            path=self.test_path,
            label=self.test_label
        )
        
        # Verify the subaccount was created with the right properties
        self.assertEqual(subaccount.private_key_bytes, self.test_private_key)
        self.assertEqual(subaccount._public_key_bytes, self.test_public_key)
        self.assertEqual(subaccount.path, self.test_path)
        self.assertEqual(subaccount.label, self.test_label)
    
    def test_init_without_public_key(self):
        """Test initialization with derived public key."""
        # Create a subaccount without providing a public key
        subaccount = Subaccount(
            private_key_bytes=self.test_private_key,
            path=self.test_path,
            label=self.test_label
        )
        
        # Verify public key was derived correctly
        self.assertEqual(subaccount.private_key_bytes, self.test_private_key)
        self.assertEqual(subaccount._public_key_bytes, self.test_public_key)
        self.assertEqual(subaccount.path, self.test_path)
        self.assertEqual(subaccount.label, self.test_label)
    
    def test_public_key_property(self):
        """Test the public_key property."""
        # Verify public_key returns the hex-encoded public key
        self.assertEqual(self.subaccount.public_key, self.test_public_key.hex())
    
    def test_sign_message(self):
        """Test signing a message with the subaccount's private key."""
        # Create a test message
        test_message = b"test message"
        
        # Mock the BLS.sign function
        with patch('saline_sdk.crypto.BLS.sign') as mock_sign:
            mock_signature = b"mock_signature"
            mock_sign.return_value = mock_signature
            
            # Sign the message
            signature = self.subaccount.sign(test_message)
            
            # Verify BLS.sign was called correctly
            mock_sign.assert_called_once_with(self.test_private_key, test_message)
            self.assertEqual(signature, mock_signature)
    
    def test_str_representation(self):
        """Test string representation of subaccount."""
        # Test __str__ with label
        representation = str(self.subaccount)
        
        # Check that it follows the format "Subaccount 'label' (prefix...suffix)"
        self.assertIn(self.test_label, representation)
        self.assertTrue(representation.startswith(f"Subaccount '{self.test_label}' ("))
        self.assertTrue(representation.endswith(")"))
        
        # Test __str__ without label
        subaccount_no_label = Subaccount(
            private_key_bytes=self.test_private_key,
            path=self.test_path
        )
        representation = str(subaccount_no_label)
        
        # Format is "Subaccount prefix...suffix" when no label
        self.assertTrue(representation.startswith("Subaccount "))
        self.assertTrue("..." in representation)


if __name__ == '__main__':
    unittest.main() 