import unittest
import json
import uuid
import os
import pytest
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import NonEmpty, Signed, TransferFunds, Transaction
from saline_sdk.transaction.tx import sign
from saline_sdk.transaction.instructions import transfer
from saline_sdk.crypto.bls import BLS

class TestSimpleTransfer(unittest.TestCase):
    """Test simple transfer transaction creation and signing."""

    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"

    def setUp(self):
        """Set up test accounts with deterministic keys."""
        self.master = Account.from_mnemonic(self.TEST_MNEMONIC)
        self.sender = self.master.create_subaccount(label="sender", path="m/12381/997/0/0/0")
        self.receiver = self.master.create_subaccount(label="receiver", path="m/12381/997/0/0/1")

        # Load fixture or fail
        fixtures_paths = [
            'tests/fixtures/known_good_simple_transfer.json',
            'saline-sdk/tests/fixtures/known_good_simple_transfer.json'
        ]
        
        for path in fixtures_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        self.known_good = json.load(f)
                        return
                except json.JSONDecodeError:
                    continue
                    
        self.fail("Required fixture 'known_good_simple_transfer.json' not found")

    def test_simple_transfer_transaction_creation(self):
        """Test that we can create a simple transfer transaction with the right structure."""
        transfer_instruction = transfer(
            sender=self.sender.public_key,
            recipient=self.receiver.public_key,
            token="USDC",
            amount=20
        )

        tx = Transaction(instructions=NonEmpty.from_list([transfer_instruction]))

        instructions = tx.instructions.list
        self.assertEqual(len(instructions), 1)
        self.assertTrue(isinstance(instructions[0], TransferFunds))
        self.assertEqual(instructions[0].source, self.sender.public_key)
        self.assertEqual(instructions[0].target, self.receiver.public_key)
        self.assertEqual(instructions[0].funds["USDC"], 20)

    def test_simple_transfer_signature(self):
        """Test that the signature is generated correctly for a simple transfer."""
        transfer_instruction = transfer(
            sender=self.sender.public_key,
            recipient=self.receiver.public_key,
            token="USDC",
            amount=20
        )

        tx = Transaction(instructions=NonEmpty.from_list([transfer_instruction]))

        new_nonce = str(uuid.uuid4())
        tx_dict = Transaction.to_json(tx)
        msg = json.dumps([new_nonce, tx_dict], separators=(',', ':')).encode('utf-8')

        direct_signature = self.sender.sign(msg)
        signed = sign(self.sender, new_nonce, tx)

        self.assertEqual(signed.signature, direct_signature.hex())

        public_key_bytes = bytes.fromhex(self.sender.public_key)
        signature_bytes = bytes.fromhex(signed.signature)
        is_valid = BLS.verify(public_key_bytes, msg, signature_bytes)
        self.assertTrue(is_valid)

@pytest.mark.usefixtures("test_account")
class TestSimpleTransferPytest:
    """Test simple transfer transaction creation and signing using pytest fixtures."""
    
    @pytest.fixture(autouse=True)
    def check_fixtures(self):
        """Check for fixture files and fail tests if they don't exist."""
        for path in ['tests/fixtures/known_good_simple_transfer.json', 
                     'saline-sdk/tests/fixtures/known_good_simple_transfer.json']:
            if os.path.exists(path):
                return  # Fixture exists, run the test
        
        assert False, "Required fixture 'known_good_simple_transfer.json' not found"
    
    def test_transfer_creation_with_fixtures(self, test_account):
        """Test transfer creation using pytest fixtures."""
        sender = test_account.create_subaccount(label="sender", path="m/12381/997/0/0/0")
        recipient = test_account.create_subaccount(label="recipient", path="m/12381/997/0/0/1")
        
        transfer_instruction = transfer(
            sender=sender.public_key,
            recipient=recipient.public_key,
            token="USDC",
            amount=20
        )
        
        tx = Transaction(instructions=NonEmpty.from_list([transfer_instruction]))
        
        instructions = tx.instructions.list
        assert len(instructions) == 1
        assert isinstance(instructions[0], TransferFunds)
        assert instructions[0].source == sender.public_key
        assert instructions[0].target == recipient.public_key
        assert instructions[0].funds["USDC"] == 20
        
    def test_transfer_signing_with_fixtures(self, test_account):
        """Test transfer signing using pytest fixtures."""
        sender = test_account.create_subaccount(label="sender", path="m/12381/997/0/0/0")
        recipient = test_account.create_subaccount(label="recipient", path="m/12381/997/0/0/1")
        
        transfer_instruction = transfer(
            sender=sender.public_key,
            recipient=recipient.public_key,
            token="USDC",
            amount=20
        )
        
        tx = Transaction(instructions=NonEmpty.from_list([transfer_instruction]))
        
        new_nonce = str(uuid.uuid4())
        signed_tx = sign(sender, new_nonce, tx)
        
        tx_dict = Transaction.to_json(tx)
        msg = json.dumps([new_nonce, tx_dict], separators=(',', ':')).encode('utf-8')
        
        public_key_bytes = bytes.fromhex(sender.public_key)
        signature_bytes = bytes.fromhex(signed_tx.signature)
        is_valid = BLS.verify(public_key_bytes, msg, signature_bytes)
        
        assert is_valid

if __name__ == '__main__':
    unittest.main() 