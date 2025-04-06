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
    rpc_url = "https://node0.try-saline.com"
    client = Client(http_url=rpc_url)

    # Check connection (optional but recommended)
    try:
        status = client.get_status() # Synchronous call
        print(f"Connected to Saline node network: {status['node_info']['network']}!")
    except Exception as e:
        print(f"Failed to connect or get status: {e}")

Working with Accounts
--------------------

Accounts manage your keys and identities.

.. code-block:: python

    from saline_sdk.account import Account

    # Create a new root account (holds the mnemonic)
    root_account = Account.create()
    print(f"Save this mnemonic safely: {root_account.mnemonic}")

    # Or load an existing account from mnemonic
    # root_account = Account.from_mnemonic("your twelve word mnemonic phrase goes here")

    # Create subaccounts (derived wallets)
    subaccount = root_account.create_subaccount("my_subaccount")
    print(f"Subaccount public key: {subaccount.public_key}")

Checking Balances
----------------

Use the client to query balances for a specific public key. Requires an `async` context.

.. code-block:: python

    import asyncio
    from saline_sdk.rpc.client import Client
    from saline_sdk.account import Account

    # Assume client and subaccount are initialized as shown above
    # rpc_url = "http://localhost:26657"
    # client = Client(http_url=rpc_url)
    # root_account = Account.create()
    # subaccount = root_account.create_subaccount(label="my_subaccount")

    async def check_balances(client: Client, address: str):
        print(f"Checking balances for {address[:10]}...")
        try:
            # get_wallet_info_async is an async function
            wallet_info = await client.get_wallet_info_async(address)
            balances = wallet_info.get('balances', []) if wallet_info else []
            print(f"Balances: {balances}")
        except Exception as e:
            print(f"Could not retrieve balances: {e}")

    # Example usage within an async main function
    async def main():
        rpc_url = "https://node0.try-saline.com"
        client = Client(http_url=rpc_url)
        root_account = Account.create()
        subaccount = root_account.create_subaccount(label="my_subaccount")
        # Need to fund the account first to see balances, e.g., via faucet
        await check_balances(client, subaccount.public_key)

    if __name__ == "__main__":
        # Run the async function
        asyncio.run(main())

Creating and Signing Transactions
-------------------

Transactions are built using instructions from `saline_sdk.transaction.bindings`.
`prepareSimpleTx` helps sign transactions easily for single-signer scenarios.

.. code-block:: python

    import asyncio
    from saline_sdk.rpc.client import Client
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import Transaction, TransferFunds, NonEmpty
    # prepareSimpleTx is sufficient for basic signing
    from saline_sdk.transaction.tx import prepareSimpleTx
    import json # For printing results

    # Assume client and subaccount are initialized
    # rpc_url = "http://localhost:26657"
    # client = Client(http_url=rpc_url)
    # root_account = Account.create()
    # subaccount = root_account.create_subaccount(label="sender")

    async def create_and_send_tx(client: Client, sender_account: Account):
        # Create a transaction with a transfer instruction
        transfer_instruction = TransferFunds(
            source=sender_account.public_key, # The sender's public key
            target="destination_public_key...", # Replace with actual destination PK
            funds={"USDC": 100} # Dictionary of token strings to amounts
        )
        tx = Transaction(instructions=NonEmpty.from_list([transfer_instruction]))

        # Sign the transaction using the subaccount's key
        # prepareSimpleTx handles nonce and signature generation
        print("Signing transaction...")
        signed_tx = prepareSimpleTx(sender_account, tx)

        # Send the signed transaction using the client
        print("Submitting transaction...")
        try:
            # tx_commit handles the signed transaction object directly
            tx_result = await client.tx_commit(signed_tx)
            print(f"Transaction submitted! Result: {json.dumps(tx_result)}")
            return tx_result.get('hash') # Return hash for status check
        except Exception as e:
            print(f"Transaction failed: {e}")
            return None

    # Example usage (requires funding the sender account first)
    async def main():
        rpc_url = "https://node0.try-saline.com"
        client = Client(http_url=rpc_url)
        root_account = Account.create()
        sender = root_account.create_subaccount(label="sender")
        # --- Add funding logic here (e.g., using faucet top_up) ---
        tx_hash = await create_and_send_tx(client, sender)
        # ... can use tx_hash later ...

    if __name__ == "__main__":
        asyncio.run(main())

Checking Transaction Status
-------------------------

Use the hash returned by `tx_commit` to query the transaction's status.

.. code-block:: python

    import asyncio
    from saline_sdk.rpc.client import Client
    import json

    # Assume client is initialized and you have a tx_hash
    # rpc_url = "http://localhost:26657"
    # client = Client(http_url=rpc_url)
    # tx_hash = "ABCDEF1234..." # Replace with actual hash

    async def check_tx_status(client: Client, tx_hash: str | None):
        if not tx_hash:
            print("No transaction hash provided.")
            return

        print(f"Checking status for tx {tx_hash[:10]}...")
        try:
            # get_tx_async is async
            tx_info = await client.get_tx_async(tx_hash)
            if tx_info:
                print(f"Transaction Info: {json.dumps(tx_info)}")
                if tx_info.get('error'):
                    print(f"Transaction Status: FAILED ({tx_info.get('error')})")
                else:
                    print("Transaction Status: SUCCESS (likely)")
            else:
                # This might mean pending or hash is incorrect/not found
                print(f"Transaction not found or still pending.")
        except Exception as e:
            print(f"Error checking transaction status: {e}")

    # Example Usage
    async def main():
        rpc_url = "https://node0.try-saline.com"
        client = Client(http_url=rpc_url)
        example_tx_hash = "PASTE_A_REAL_TX_HASH_HERE" # Get this from a previous tx_commit result
        await check_tx_status(client, example_tx_hash)

    if __name__ == "__main__":
        asyncio.run(main())

Asynchronous Operations
--------------------

The Saline SDK is primarily asynchronous. Most interactions with the `Client` that involve network requests (like `tx_commit`, `get_wallet_info_async`, `get_tx_async`, `get_all_intents`) are `async` functions and should be `await`ed. These typically need to be called from within an `async def` function, which is then executed using `asyncio.run()`.

Synchronous methods like `client.get_status()` do not require `await`.

Using the Testnet Faucet
--------------------

The SDK includes utilities for obtaining tokens from the testnet faucet.

.. code-block:: python

    import asyncio
    from saline_sdk.account import Account
    from saline_sdk.rpc.client import Client
    from saline_sdk.rpc.testnet.faucet import top_up

    RPC_URL = "https://node0.try-saline.com"

    async def get_testnet_tokens():
        # Create account and client
        root_account = Account.create()
        alice = root_account.create_subaccount(label="alice")
        bob = root_account.create_subaccount(label="bob")
        client = Client(http_url=RPC_URL)

        # Check connection
        try:
            status = client.get_status()
            print(f"Connected: {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Connection failed: {e}")
            return

        # Request default tokens for Alice
        print(f"Requesting faucet tokens for Alice ({alice.public_key[:10]}...)")
        try:
            # top_up is async
            await top_up(
                account=alice,  # Pass Subaccount directly
                client=client
                # use_dynamic_amounts=True is default
            )
            print("Faucet request submitted for Alice.")
            # Wait briefly for faucet tx to potentially process
            await asyncio.sleep(3)
            alice_info = await client.get_wallet_info_async(alice.public_key)
            print(f"Alice balances: {alice_info.get('balances', []) if alice_info else 'Error/None'}")
        except Exception as e:
            print(f"Faucet top-up failed for Alice: {e}")

        # Request specific token amounts for Bob
        print(f"\nRequesting specific faucet tokens for Bob ({bob.public_key[:10]}...)")
        try:
            await top_up(
                account=bob,
                client=client,
                tokens={"BTC": 0.5, "ETH": 5}, # Specify desired tokens
                use_dynamic_amounts=False      # Required when specifying tokens
            )
            print("Faucet request submitted for Bob.")
            await asyncio.sleep(3)
            bob_info = await client.get_wallet_info_async(bob.public_key)
            print(f"Bob balances: {bob_info.get('balances', []) if bob_info else 'Error/None'}")
        except Exception as e:
             print(f"Faucet top-up failed for Bob: {e}")

    # Run the async function
    if __name__ == "__main__":
        asyncio.run(get_testnet_tokens())