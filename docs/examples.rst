========
Examples
========

This section provides detailed examples of using the Saline SDK for various blockchain operations.
These examples correspond to the scripts found in the ``examples/`` directory of the project.

Basic Transaction
===============

This example demonstrates how to create and submit a basic transfer transaction. See ``examples/basic_transaction.py``.

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.rpc.client import Client
    from saline_sdk.transaction.instructions import transfer
    from saline_sdk.transaction.bindings import NonEmpty, Transaction
    from saline_sdk.transaction.tx import prepareSimpleTx

    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    RPC_URL = "http://localhost:26657"

    async def main():
        # Create the root account from mnemonic
        account = Account.from_mnemonic(TEST_MNEMONIC)

        # Derive subaccounts for sender and receiver
        sender = account.create_subaccount(name="sender")
        receiver = account.create_subaccount(name="receiver")

        transfer_instruction = transfer(
            sender=sender.public_key,
            recipient=receiver.public_key,
            token="USDC",
            amount=20
        )

        tx = Transaction(
            instructions=NonEmpty.from_list([transfer_instruction]),
        )

        rpc = Client(http_url=RPC_URL)
        # Submit transaction and wait for validation
        result = await rpc.tx_broadcast(prepareSimpleTx(sender,tx))
        print(f"\nRPC response: {json.dumps(result, indent=2)}")

Token Swap
=========

This example shows how to create a token swap transaction between two parties.
See ``examples/token_swap.py``.

.. code-block:: python

    import asyncio
    import json
    import uuid
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import NonEmpty, Signed, Transaction
    from saline_sdk.transaction.tx import encodeSignedTx
    from saline_sdk.transaction.instructions import transfer
    from saline_sdk.rpc.client import Client
    from saline_sdk.crypto.bls import BLS

    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    RPC_URL = "http://localhost:26657"

    async def create_and_submit_swap():
        # Create accounts for the swap participants
        root = Account.from_mnemonic(TEST_MNEMONIC)
        alice = root.create_subaccount(name="alice")
        bob = root.create_subaccount(name="bob")

        # Define swap parameters
        alice_token = "USDC"
        alice_amount = 100
        bob_token = "BTC"
        bob_amount = 1

        # Create the transfer instructions for both sides of the swap
        alice_instruction = transfer(
            sender=alice.public_key,
            recipient=bob.public_key,
            token=alice_token,
            amount=alice_amount
        )

        bob_instruction = transfer(
            sender=bob.public_key,
            recipient=alice.public_key,
            token=bob_token,
            amount=bob_amount
        )

        # Combine the instructions into a single transaction
        tx = Transaction(instructions=NonEmpty.from_list([alice_instruction, bob_instruction]))
        
        # Generate a unique nonce for the transaction
        nonce = str(uuid.uuid4())
        
        # Prepare the message to sign (this would be shared between parties)
        msg = json.dumps([nonce, Transaction.to_json(tx)], separators=(',', ':')).encode('utf-8')

        # Each party signs the same message
        alice_sig = alice.sign(msg)
        bob_sig = bob.sign(msg)

        # Aggregate the signatures into a single BLS signature
        aggregate_signature = BLS.aggregate_signatures([alice_sig, bob_sig])

        # Create the final signed transaction
        signed_tx = Signed(
            nonce=nonce,
            signature=aggregate_signature.hex(),
            signee=tx,
            signers=NonEmpty.from_list([alice.public_key, bob.public_key])
        )

        # Submit the transaction to the network
        rpc = Client(http_url=RPC_URL)
        result = await rpc.tx_commit(encodeSignedTx(signed_tx))
        return result

Multi-Signature Intent
=========================

This example demonstrates creating and installing a multi-signature intent on an account.
See ``examples/install_multisig_intent.py``.

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Transaction, SetIntent, Any, 
        Signature, Send, Flow, Token
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client

    async def create_and_install_multisig_intent():
        root = Account.from_mnemonic(TEST_MNEMONIC)

        # Create 3 signers for the multisig
        signer1 = root.create_subaccount(name="signer1")
        signer2 = root.create_subaccount(name="signer2")
        signer3 = root.create_subaccount(name="signer3")
        
        # Create a multisig wallet subaccount that will have the intent
        multisig_wallet = root.create_subaccount(name="multisig_wallet")

        # Define the multisig intent
        # This creates an intent that requires either:
        # 1. The transaction only sends <= 1 BTC (small transaction limit), OR
        # 2. The transaction has at least 2 of 3 signatures from the signers
        
        # First part: restriction for small amounts (<=1 BTC)
        small_tx_restriction = Send(Flow(None, Token.BTC)) <= 1
        
        # Second part: 2-of-3 multisignature requirement
        signatures = [
            Signature(signer1.public_key),
            Signature(signer2.public_key),
            Signature(signer3.public_key)
        ]
        multisig_requirement = Any(2, signatures)
        
        # Combine the two conditions with OR (using the Any operator with threshold 1)
        multisig_intent = Any(1, [small_tx_restriction, multisig_requirement])
        
        # Create a SetIntent instruction to install the intent on the multisig wallet
        set_intent_instruction = SetIntent(multisig_wallet.public_key, multisig_intent)
        
        tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))
        signed_tx = prepareSimpleTx(multisig_wallet, tx)
        
        rpc = Client(http_url=RPC_URL)
        result = await rpc.tx_commit(signed_tx)
        return result

Additional Examples
=================

The SDK repository contains additional example files demonstrating more advanced use cases:

1. ``install_swap_intent.py`` - Setting up an intent to enable automated swaps
2. ``intent_queries_example.py`` - Querying the blockchain for intent information 
3. ``simple_matcher.py`` - Implementing a matching engine for swap intents
4. ``fulfill_faucet_intent.py`` - Interacting with faucet intents to obtain tokens 