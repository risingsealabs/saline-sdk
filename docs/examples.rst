========
Examples
========

This section provides detailed examples of using the Saline SDK for various blockchain operations.
These examples correspond to the scripts found in the ``examples/`` directory of the project.

Basic Transaction
===============

This example demonstrates how to create, sign, and submit a basic transfer transaction. See ``examples/basic_transaction.py``.

.. code-block:: python

    import asyncio
    import json
    import uuid
    import base64
    from saline_sdk.account import Account
    from saline_sdk.rpc.client import Client
    from saline_sdk.transaction.instructions import transfer
    from saline_sdk.transaction.tx import Transaction, sign, encodeSignedTx

    # Create the root account from mnemonic
    account = Account.from_mnemonic(TEST_MNEMONIC)
    
    # Derive subaccounts for sender and receiver
    sender = account.create_subaccount(name="sender")
    receiver = account.create_subaccount(name="receiver")
    
    # Create a transfer instruction
    transfer_instruction = transfer(
        sender=sender.public_key,
        recipient=receiver.public_key,
        token="USDC",
        amount=20
    )
    
    # Create a transaction
    tx = Transaction(
        instructions=[transfer_instruction]
    )
    
    # Set the signer
    tx.set_signer(sender.public_key)
    
    # Generate a nonce
    nonce = str(uuid.uuid4())
    
    # Sign the transaction 
    signed_tx = sign(sender, nonce, tx)
    
    # Encode for network submission
    encoded_tx = encodeSignedTx(signed_tx)
    
    # Submit via RPC
    client = Client(http_url="http://localhost:26657")
    result = await client.tx_broadcast(encoded_tx)

Token Swap
=========

This example shows how to create a token swap transaction between two parties.
See ``examples/token_swap.py``.

.. code-block:: python

    import uuid
    from saline_sdk.account import Account
    from saline_sdk.transaction.tx import Transaction, sign, encodeSignedTx
    from saline_sdk.transaction.instructions import swap
    from saline_sdk.rpc.client import Client
    
    # Create a master account and sub-accounts for the swap participants
    root = Account.from_mnemonic(TEST_MNEMONIC)
    
    # Create accounts for the swap participants
    alice = root.create_subaccount(name="alice")
    bob = root.create_subaccount(name="bob")
    
    # Create a swap instruction
    swap_instructions = swap(
        sender=alice.public_key,  # Alice is sending ETH
        recipient=bob.public_key,  # to Bob
        give_token="ETH",         # Alice gives ETH
        give_amount=1,            # 1 ETH
        take_token="USDC",        # Bob gives USDC
        take_amount=1000          # 1000 USDC
    )
    
    # Create the transaction
    tx = Transaction(instructions=[swap_instructions])
    
    # Set the signer
    tx.set_signer(alice.public_key)
    
    # Generate a nonce
    nonce = str(uuid.uuid4())
    
    # Sign the transaction
    signed_tx = sign(alice, nonce, tx)
    
    # Encode for network submission
    encoded_tx = encodeSignedTx(signed_tx)
    
    # Submit via RPC
    client = Client(http_url="http://localhost:26657")
    result = await client.tx_broadcast(encoded_tx)

Multi-Signature Transaction
=========================

This example demonstrates creating a transaction that requires multiple signatures.
See ``examples/multisig_transaction.py``.

.. code-block:: python

    from saline_sdk.account import Account
    from saline_sdk.transaction.tx import Transaction
    from saline_sdk.transaction.instructions import transfer
    from saline_sdk.crypto.bls import BLS
    
    # Create a master account and sub-accounts
    root = Account.from_mnemonic(TEST_MNEMONIC)
    
    # Create 3 signers for the multisig
    signer1 = root.create_subaccount(name="signer1")
    signer2 = root.create_subaccount(name="signer2")
    signer3 = root.create_subaccount(name="signer3")
    
    # Create a recipient
    recipient = root.create_subaccount(name="recipient")
    
    # Create a transfer instruction
    transfer_instruction = transfer(
        sender=signer1.public_key,
        recipient=recipient.public_key,
        token="USDC",
        amount=50
    )
    
    # Create the transaction
    tx = Transaction(instructions=[transfer_instruction])
    
    # Add all signers
    tx.set_signer(signer1.public_key)
    tx.add_intent(signer2.public_key)
    tx.add_intent(signer3.public_key)
    
    # Manually create the message to sign
    import json
    from uuid import uuid4
    
    nonce = str(uuid4())
    tx_dict = Transaction.to_json(tx)
    message = json.dumps([nonce, tx_dict], separators=(',', ':')).encode('utf-8')
    
    # Collect signatures from all signers
    sig1 = signer1.sign_message(message)
    sig2 = signer2.sign_message(message)
    sig3 = signer3.sign_message(message)
    
    # Aggregate the signatures
    signatures = [sig1, sig2, sig3]
    aggregated_sig = BLS.aggregate_signatures(signatures)
    
    # Create a signed transaction with the aggregated signature
    from saline_sdk.transaction.sdk import Signed, NonEmpty
    
    signed_tx = Signed(
        nonce=nonce,
        signature=aggregated_sig.hex(),
        signee=tx,
        signers=NonEmpty.from_list([signer1.public_key, signer2.public_key, signer3.public_key])
    )

Debugging Transactions
=====================

This example shows how to debug transaction serialization and submission.
See ``examples/debug_transaction.py``.

.. code-block:: python

    import json
    import binascii
    import base64
    import logging
    
    # Set up logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Helper function to print dictionaries in a sorted, consistent way
    def sort_nested_dict(d):
        """Recursively sort all nested dictionaries by key."""
        if isinstance(d, dict):
            return {k: sort_nested_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [sort_nested_dict(x) for x in d]
        else:
            return d
    
    # Serialize transaction for network submission
    def serialize_for_network(tx):
        # First, sort the dictionary to ensure consistent serialization
        sorted_tx = sort_nested_dict(tx)
        
        # Convert to JSON with no whitespace
        json_data = json.dumps(sorted_tx, separators=(',', ':')).encode('utf-8')
        
        # Convert JSON bytes to hex string
        hex_data = binascii.hexlify(json_data)
        
        # Print debug info
        print(f"JSON payload: {json_data.decode('utf-8')}")
        print(f"JSON length: {len(json_data)} bytes")
        print(f"Hex payload: {hex_data[:64].decode('utf-8')}...")
        print(f"Hex length: {len(hex_data)} bytes")
        
        # Base64 encode for network submission
        base64_data = base64.b64encode(hex_data).decode('utf-8')
        print(f"Base64 payload: {base64_data[:64]}...")
        print(f"Base64 length: {len(base64_data)} bytes")
        
        return hex_data 