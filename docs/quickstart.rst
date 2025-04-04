==========
Quickstart
==========

This guide will help you get started with the Saline SDK quickly.

Basic Usage
===========

Initialize the SDK Client
-------------------------

To interact with the Saline network, you need to initialize an RPC client:

.. code-block:: python

    from saline_sdk.rpc.client import Client

    # Initialize the client with your node connection
    rpc_url = "http://localhost:26657"
    client = Client(http_url=rpc_url)

Working with Accounts
--------------------

Accounts manage your keys and identities.

.. code-block:: python

    from saline_sdk.account import Account

    # Create a new root account (holds the mnemonic)
    account = Account.create()
    print(f"Save this mnemonic: {account.mnemonic}")

    # Or load an existing account from mnemonic
    account = Account.from_mnemonic("your twelve word mnemonic phrase goes here")

    # Create subaccounts (derived wallets)
    subaccount = account.create_subaccount("my_subaccount")
    print(f"Subaccount public key: {subaccount.public_key}")

Checking Balances
----------------

Use the client to query balances for a specific public key.

.. code-block:: python

    import asyncio

    async def check_balances():
        # Get wallet info, which includes balances
        wallet_info = await client.get_wallet_info_async(subaccount.public_key)
        balances = wallet_info.get('balances', []) # Balances are usually a list
        print(f"Balances for {subaccount.public_key[:10]}...: {balances}")

    # Run the async function
    asyncio.run(check_balances())

Creating and Signing Transactions
-------------------

Transactions are built using instructions from `saline_sdk.transaction.bindings`.

.. code-block:: python

    from saline_sdk.transaction.bindings import Transaction, TransferFunds, NonEmpty
    from saline_sdk.transaction.tx import prepareSimpleTx, encodeSignedTx

    # Create a transaction with a transfer instruction
    transfer_instruction = TransferFunds(
        source=subaccount.public_key, # The sender's public key
        target="destination_public_key",
        funds={"USDC": 100} # Dictionary of token strings to amounts
    )
    tx = Transaction(instructions=NonEmpty.from_list([transfer_instruction]))

    # Sign the transaction using the subaccount's key
    # prepareSimpleTx handles nonce and signature generation
    signed_tx = prepareSimpleTx(subaccount, tx)

    # Encode for network submission (optional, client handles if needed)
    # encoded_tx = encodeSignedTx(signed_tx)

    # Send the signed transaction using the client
    async def send_tx():
        tx_result = await client.tx_commit(signed_tx)
        print(f"Transaction sent with hash: {tx_result.get('hash')}")
        print(f"Result: {tx_result}")

    asyncio.run(send_tx())

Checking Transaction Status
-------------------------

.. code-block:: python

    # Use the transaction hash returned by tx_commit
    tx_hash = tx_result.get('hash')

    async def check_tx_status():
        if tx_hash:
            tx_info = await client.get_tx_async(tx_hash)
            if tx_info:
                print(f"Transaction {tx_hash[:10]}... info: {tx_info}")
                if tx_info.get('error'):
                    print(f"Transaction failed: {tx_info.get('error')}")
                else:
                    print("Transaction appears successful!")
            else:
                print(f"Transaction {tx_hash[:10]}... not found or still pending.")
        else:
            print("No transaction hash available to check.")

    asyncio.run(check_tx_status())

Asynchronous Operations
--------------------

The Saline SDK is primarily asynchronous. Most interactions with the `Client` are `async` functions and should be awaited, typically within an `async def` function run via `asyncio.run()`.

Using the Testnet Faucet
--------------------

The SDK includes utilities for obtaining tokens from the testnet faucet.

.. code-block:: python

    import asyncio
    from saline_sdk.account import Account
    from saline_sdk.rpc.client import Client
    from saline_sdk.rpc.testnet.faucet import top_up

    async def get_testnet_tokens():
        # Create account and client
        account = Account.create()
        alice = account.create_subaccount(label="alice")
        client = Client(http_url="http://localhost:26657")

        # Request tokens (uses defaults or faucet intent)
        print(f"Requesting faucet tokens for Alice ({alice.public_key[:10]}...)")
        try:
            await top_up(
                account=alice,  # Pass Subaccount directly
                client=client
            )
            print("Faucet request submitted.")
            # Check balance after a short delay
            await asyncio.sleep(2)
            alice_info = await client.get_wallet_info_async(alice.public_key)
            print(f"Alice balances: {alice_info.get('balances', [])}")
        except Exception as e:
            print(f"Faucet top-up failed: {e}")

        # Request specific token amounts, overriding faucet intent/defaults
        bob = account.create_subaccount(label="bob")
        print(f"\nRequesting specific faucet tokens for Bob ({bob.public_key[:10]}...)")
        try:
            await top_up(
                account=bob,
                client=client,
                tokens={"BTC": 0.5, "ETH": 5},
                use_dynamic_amounts=False  # Force use of 'tokens' arg
            )
            print("Faucet request submitted for specific amounts.")
            await asyncio.sleep(2)
            bob_info = await client.get_wallet_info_async(bob.public_key)
            print(f"Bob balances: {bob_info.get('balances', [])}")
        except Exception as e:
             print(f"Faucet top-up failed: {e}")

    # Run the async function
    asyncio.run(get_testnet_tokens())