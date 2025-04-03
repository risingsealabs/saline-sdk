"""
Unit tests for BLS cryptography functionality in saline_sdk.crypto.
"""

import unittest
from unittest.mock import patch, MagicMock
import binascii
from typing import List, Optional
from mnemonic import Mnemonic

from saline_sdk.crypto import BLS, derive_master_SK, derive_key_from_path


class TestBLSCrypto(unittest.TestCase):
    """Test suite for BLS cryptography functionality."""
    
    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    ALTERNATE_MNEMONIC = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    def setUp(self):
        """Set up test fixtures before each test."""
        mnemo = Mnemonic("english")
        self.test_seed1 = mnemo.to_seed(self.TEST_MNEMONIC)
        self.test_seed2 = mnemo.to_seed(self.ALTERNATE_MNEMONIC)
        
        self.test_private_key1 = derive_key_from_path(self.test_seed1, "m/12381/997/0/0/0")
        self.test_public_key1 = BLS.sk_to_pk(self.test_private_key1)
        
        self.test_private_key2 = derive_key_from_path(self.test_seed2, "m/12381/997/0/0/0")
        self.test_public_key2 = BLS.sk_to_pk(self.test_private_key2)
        
        self.test_message = b"test message for BLS signature"
        
        self.test_signature1 = BLS.sign(self.test_private_key1, self.test_message)
        self.test_signature2 = BLS.sign(self.test_private_key2, self.test_message)
    
    def test_sk_to_pk(self):
        """Test derivation of public keys from private keys."""
        for private_key in [self.test_private_key1, self.test_private_key2]:
            public_key = BLS.sk_to_pk(private_key)
            
            self.assertIsNotNone(public_key)
            self.assertTrue(isinstance(public_key, bytes))
            self.assertEqual(len(public_key), 48)
        
        public_key1 = BLS.sk_to_pk(self.test_private_key1)
        public_key1_repeat = BLS.sk_to_pk(self.test_private_key1)
        self.assertEqual(public_key1, public_key1_repeat)
        
        public_key2 = BLS.sk_to_pk(self.test_private_key2)
        self.assertNotEqual(public_key1, public_key2)
    
    def test_sign(self):
        """Test signing messages with private keys."""
        for private_key in [self.test_private_key1, self.test_private_key2]:
            signature = BLS.sign(private_key, self.test_message)
            
            self.assertIsNotNone(signature)
            self.assertTrue(isinstance(signature, bytes))
            self.assertEqual(len(signature), 96)
        
        signature1 = BLS.sign(self.test_private_key1, self.test_message)
        signature1_repeat = BLS.sign(self.test_private_key1, self.test_message)
        self.assertEqual(signature1, signature1_repeat)
        
        signature2 = BLS.sign(self.test_private_key2, self.test_message)
        self.assertNotEqual(signature1, signature2)
        
        different_message = b"different test message"
        different_message_signature = BLS.sign(self.test_private_key1, different_message)
        self.assertNotEqual(signature1, different_message_signature)
    
    def test_verify(self):
        """Test verification of signatures."""
        for i in range(1, 3):
            private_key = getattr(self, f"test_private_key{i}")
            public_key = getattr(self, f"test_public_key{i}")
            signature = getattr(self, f"test_signature{i}")
            
            self.assertTrue(BLS.verify(public_key, self.test_message, signature))
            
            wrong_message = b"wrong message"
            self.assertFalse(BLS.verify(public_key, wrong_message, signature))
            
            wrong_key = getattr(self, f"test_public_key{3-i}")  # Use the other key
            self.assertFalse(BLS.verify(wrong_key, self.test_message, signature))
    
    def test_aggregate_signatures(self):
        """Test aggregation of signatures."""
        signatures = [self.test_signature1, self.test_signature2]
        aggregate_signature = BLS.aggregate_signatures(signatures)
        
        self.assertIsNotNone(aggregate_signature)
        self.assertTrue(isinstance(aggregate_signature, bytes))
        self.assertEqual(len(aggregate_signature), 96)  # G2 element
        
        aggregate_signature_repeat = BLS.aggregate_signatures(signatures)
        self.assertEqual(aggregate_signature, aggregate_signature_repeat)
        
        signatures_reversed = [self.test_signature2, self.test_signature1]
        aggregate_signature_reversed = BLS.aggregate_signatures(signatures_reversed)
        self.assertEqual(aggregate_signature, aggregate_signature_reversed)
    
    def test_verify_aggregate_signature(self):
        """Test verification of aggregate signatures."""
        signatures = [self.test_signature1, self.test_signature2]
        public_keys = [self.test_public_key1, self.test_public_key2]
        messages = [self.test_message, self.test_message]  # Same message
        
        aggregate_signature = BLS.aggregate_signatures(signatures)
        
        self.assertTrue(
            BLS.verify_aggregate(aggregate_signature, messages, public_keys)
        )
        
        wrong_messages = [self.test_message, b"wrong message"]
        self.assertFalse(
            BLS.verify_aggregate(aggregate_signature, wrong_messages, public_keys)
        )
        
        flipped_order_public_keys = [self.test_public_key2, self.test_public_key1]  # Swapped
        self.assertTrue(
            BLS.verify_aggregate(aggregate_signature, messages, flipped_order_public_keys)
        )
    
    def test_verify_multiple_aggregates(self):
        """Test verification with multiple aggregate signatures."""
        keys = []
        messages = []
        signatures = []
        
        for i in range(5):
            priv_key = derive_key_from_path(self.test_seed1, f"m/12381/997/0/0/{i}")
            pub_key = BLS.sk_to_pk(priv_key)
            message = f"test message {i}".encode()
            signature = BLS.sign(priv_key, message)
            
            keys.append(pub_key)
            messages.append(message)
            signatures.append(signature)
        
        aggregate_signature = BLS.aggregate_signatures(signatures)
        
        self.assertTrue(
            BLS.verify_aggregate(aggregate_signature, messages, keys)
        )
        
        modified_messages = messages.copy()
        modified_messages[2] = b"modified message"
        self.assertFalse(
            BLS.verify_aggregate(aggregate_signature, modified_messages, keys)
        )
    
    def test_key_formats(self):
        """Test conversions between different key formats."""
        if hasattr(BLS, 'bytes_to_hex') and hasattr(BLS, 'hex_to_bytes'):
            private_key_hex = BLS.bytes_to_hex(self.test_private_key1)
            self.assertTrue(isinstance(private_key_hex, str))
            self.assertEqual(len(private_key_hex), 64)  # 32 bytes = 64 hex chars
            
            private_key_bytes = BLS.hex_to_bytes(private_key_hex)
            self.assertEqual(private_key_bytes, self.test_private_key1)
            
            public_key_hex = BLS.bytes_to_hex(self.test_public_key1)
            self.assertTrue(isinstance(public_key_hex, str))
            self.assertEqual(len(public_key_hex), 96)  # 48 bytes = 96 hex chars
            
            public_key_bytes = BLS.hex_to_bytes(public_key_hex)
            self.assertEqual(public_key_bytes, self.test_public_key1)
    
    def test_key_validation(self):
        """Test validation of keys if implemented."""
        if hasattr(BLS, 'validate_private_key'):
            self.assertTrue(BLS.validate_private_key(self.test_private_key1))
            
            invalid_private_key = bytes(32)
            self.assertFalse(BLS.validate_private_key(invalid_private_key))
        
        if hasattr(BLS, 'validate_public_key'):
            self.assertTrue(BLS.validate_public_key(self.test_public_key1))
            
            invalid_public_key = bytes(48)
            self.assertFalse(BLS.validate_public_key(invalid_public_key))


if __name__ == '__main__':
    unittest.main()
