"""
Unit tests for the Account class in saline_sdk.account module.
"""

import unittest
from unittest.mock import patch, MagicMock
from mnemonic import Mnemonic

from saline_sdk.account import Account, Subaccount
from saline_sdk.crypto import derive_key_from_path, BLS



class TestAccount(unittest.TestCase):
    """Test suite for Account class functionality."""

    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    
    def setUp(self):
        """Set up test fixtures before each test."""
        mnemo = Mnemonic("english")
        self.test_seed = mnemo.to_seed(self.TEST_MNEMONIC)
        
        self.account = Account.from_mnemonic(self.TEST_MNEMONIC)
        
        self.test_path = "m/12381/997/0/0/0"
        self.test_private_key = derive_key_from_path(self.test_seed, self.test_path)
        self.test_public_key = BLS.sk_to_pk(self.test_private_key)
        self.test_public_key_hex = self.test_public_key.hex()
    
    def test_create_account(self):
        """Test creating a new account with random mnemonic."""
        with patch('saline_sdk.account.Mnemonic') as mock_mnemonic:
            mock_mnemonic.return_value.generate.return_value = self.TEST_MNEMONIC
            mock_mnemonic.return_value.to_seed.return_value = self.test_seed
            
            account = Account.create()
            
            self.assertIsNotNone(account._mnemonic)
            self.assertIsNotNone(account._seed)
            self.assertEqual(len(account._subaccounts), 0)
            self.assertIsNone(account.default_subaccount)
    
    def test_from_mnemonic(self):
        """Test creating an account from a mnemonic phrase."""
        account = Account.from_mnemonic(self.TEST_MNEMONIC)
        self.assertEqual(account._mnemonic, self.TEST_MNEMONIC)
        self.assertIsNotNone(account._seed)
        
        with self.assertRaises(ValueError):
            Account.from_mnemonic("invalid mnemonic phrase")
    
    def test_derive_from_mnemonic(self):
        """Test deriving an account from a mnemonic phrase."""
        account = Account.from_mnemonic(self.TEST_MNEMONIC)
        self.assertEqual(account._mnemonic, self.TEST_MNEMONIC)
        self.assertIsNotNone(account._seed)
        
        custom_path = "m/12381/997/1"
        account = Account.from_mnemonic(self.TEST_MNEMONIC, custom_path)
        self.assertEqual(account._mnemonic, self.TEST_MNEMONIC)
        self.assertIsNotNone(account._seed)
        self.assertEqual(account.base_path, custom_path)
        
        with self.assertRaises(ValueError):
            Account.from_mnemonic("invalid mnemonic phrase")
    
    def test_create_subaccount(self):
        """Test creating a subaccount."""
        name = "test_subaccount"
        subaccount = self.account.create_subaccount(name)
        
        self.assertIsInstance(subaccount, Subaccount)
        self.assertEqual(subaccount.label, name)
        self.assertIn(name, self.account._subaccounts)
        self.assertEqual(self.account.default_subaccount, name)
        
        name2 = "test_subaccount2"
        subaccount2 = self.account.create_subaccount(name2)
        self.assertIsInstance(subaccount2, Subaccount)
        self.assertIn(name2, self.account._subaccounts)
        self.assertNotEqual(self.account.default_subaccount, name2)
        
        name3 = "test_subaccount3"
        explicit_path = "m/12381/997/0/1/0"
        subaccount3 = self.account.create_subaccount(name3, explicit_path)
        self.assertEqual(subaccount3.path, explicit_path)
        
        with self.assertRaises(ValueError):
            self.account.create_subaccount(name)
    
    def test_get_subaccount(self):
        """Test getting a subaccount by name."""
        name1 = "subaccount1"
        name2 = "subaccount2"
        subaccount1 = self.account.create_subaccount(name1)
        subaccount2 = self.account.create_subaccount(name2)
        
        retrieved1 = self.account.get_subaccount(name1)
        retrieved2 = self.account.get_subaccount(name2)
        self.assertEqual(retrieved1, subaccount1)
        self.assertEqual(retrieved2, subaccount2)
        
        with self.assertRaises(KeyError):
            self.account.get_subaccount("non_existent")
    
    def test_list_subaccounts(self):
        """Test listing all subaccounts."""
        name1 = "subaccount1"
        name2 = "subaccount2"
        subaccount1 = self.account.create_subaccount(name1)
        subaccount2 = self.account.create_subaccount(name2)
        
        subaccounts = self.account.list_subaccounts()
        self.assertIsInstance(subaccounts, dict)
        self.assertEqual(len(subaccounts), 2)
        self.assertIn(name1, subaccounts)
        self.assertIn(name2, subaccounts)
        self.assertEqual(subaccounts[name1], subaccount1.public_key)
        self.assertEqual(subaccounts[name2], subaccount2.public_key)
    
    def test_set_default_subaccount(self):
        """Test setting the default subaccount."""
        name1 = "subaccount1"
        name2 = "subaccount2"
        self.account.create_subaccount(name1)
        self.account.create_subaccount(name2)
        
        self.assertEqual(self.account.default_subaccount, name1)
        
        self.account.set_default_subaccount(name2)
        self.assertEqual(self.account.default_subaccount, name2)
        
        with self.assertRaises(KeyError):
            self.account.set_default_subaccount("non_existent")
    
    def test_transfer(self):
        """Test creating a transfer transaction."""
        from_account = "sender"
        self.account.create_subaccount(from_account)
        
        to_address = "nacl:aa04d11fa77e57490abc45e1af35b37cf8525af9577a29fbdeabbc000081a4c237152046eb9d9790c44391f4a18f1b07"
        amount = 100
        currency = "USDC"
        
        with patch('saline_sdk.transaction.tx.Transaction') as mock_tx:
            mock_instance = mock_tx.return_value
            mock_instance.sign.return_value = mock_instance
            
            result = self.account.transfer(to_address, amount, currency, from_account)
            mock_tx.assert_called()
            
            result = self.account.transfer(to_address, amount, currency)
            
            with self.assertRaises(KeyError):
                self.account.transfer(to_address, amount, currency, "non_existent")
    
    def test_dict_like_access(self):
        """Test dictionary-like access to subaccounts."""
        name1 = "subaccount1"
        name2 = "subaccount2"
        subaccount1 = self.account.create_subaccount(name1)
        subaccount2 = self.account.create_subaccount(name2)
        
        self.assertEqual(self.account[name1], subaccount1)
        self.assertEqual(self.account[name2], subaccount2)
        with self.assertRaises(KeyError):
            invalid = self.account["non_existent"]
        
        self.assertIn(name1, self.account)
        self.assertIn(name2, self.account)
        self.assertNotIn("non_existent", self.account)
        
        subaccounts = list(self.account)
        self.assertEqual(len(subaccounts), 2)
        self.assertIn(name1, subaccounts)
        self.assertIn(name2, subaccounts)
        
        self.assertEqual(len(self.account), 2)
    
    def test_str_representation(self):
        """Test string representation of account."""
        self.account.create_subaccount("subaccount1")
        self.account.create_subaccount("subaccount2")
        
        representation = str(self.account)
        self.assertIn("Account with", representation)
        self.assertIn("2 subaccounts", representation)
        self.assertIn("subaccount1", representation)
        self.assertIn("subaccount2", representation)


if __name__ == '__main__':
    unittest.main() 