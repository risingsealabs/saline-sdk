===============
Troubleshooting
===============

This page provides solutions to common issues you might encounter when using the Saline SDK.

Connection Issues
----------------

**Problem**: Cannot connect to the Saline node.

**Solution**:
- Verify the node URL (`http_url`) is correct and the node is running.
- Check network connectivity between your application and the node.
- Ensure the node's RPC endpoint (`http://...:26657` by default) is accessible.

.. code-block:: python

    # Check node connection
    from saline_sdk.rpc.client import Client

    rpc_url = \"https://node0.try-saline.com\" # Or your node URL
    try:
        client = Client(http_url=rpc_url)
        status = client.get_status() # Synchronous check
        print(f\"Successfully connected to node: {status['node_info']['network']}!\")
    except Exception as e:
        print(f\"Cannot connect to node at {rpc_url}. Check URL and node status. Error: {e}\")

Transaction Errors
----------------

**Problem**: Transaction fails to be submitted or is rejected by the node (e.g., intent error, insufficient funds).

**Solution**:
- Check the account's balance using `client.get_wallet_info_async()` before sending.
- Ensure the transaction instructions match the account's intent (if any).
- Verify the correct account (with the necessary keys) is used to sign (`prepareSimpleTx(account, tx)`).
- Examine the error message returned in the `tx_commit` result.

.. code-block:: python

    import asyncio
    from saline_sdk.rpc.client import Client
    from saline_sdk.account import Account # Assuming Account object exists

    # Example: Check balance before sending (inside an async function)
    async def check_funds_before_send(client: Client, account: Account, token: str, amount: int):
        try:
            wallet_info = await client.get_wallet_info_async(account.public_key)
            current_balance = 0
            if wallet_info and wallet_info.get('balances'):
                for bal_token, bal_amount in wallet_info['balances']:
                    if bal_token == token:
                        current_balance = int(bal_amount) # Assuming amount is string/int
                        break

            print(f\"Current {token} balance: {current_balance}\")
            if current_balance < amount:
                print(f\"Insufficient funds to send {amount} {token}.\")
                return False
            return True
        except Exception as e:
            print(f\"Error checking balance: {e}\")
            return False

    # Note: prepareSimpleTx handles nonce generation automatically.
    # Ensure the signing account (`my_account` below) has the funds and matches the 'source' in TransferFunds
    # signed_tx = prepareSimpleTx(my_account, transaction_object)
    # result = await client.tx_commit(signed_tx)
    # if result and result.get('error'):
    #    print(f\"Transaction Error: {result['error']}\")

Account Issues
------------

**Problem**: Confusion about root accounts vs. subaccounts.

**Solution**:
- `Account.create()` or `Account.from_mnemonic()` creates a *root* account object holding the mnemonic.
- `root_account.create_subaccount("label")` derives a specific wallet (with its own public/private key) from the root mnemonic.
- Operations like signing transactions (`prepareSimpleTx`) or specifying transaction sources/targets require the *subaccount* object or its `public_key`.

.. code-block:: python

    from saline_sdk.account import Account

    # Create root
    root_account = Account.create()

    # Create the specific subaccount you intend to use
    my_wallet = root_account.create_subaccount(\"my_wallet_label\")
    print(f\"Using wallet with PK: {my_wallet.public_key}\")

    # Use 'my_wallet' for signing transactions originated by it
    # signed_tx = prepareSimpleTx(my_wallet, tx)

    # Use 'my_wallet.public_key' when referring to it in instructions (e.g., target)
    # instruction = TransferFunds(source=..., target=my_wallet.public_key, ...)

Using Async Methods
----------------

**Problem**: Seeing "coroutine `XYZ` was never awaited" errors.

**Solution**:
- Most `Client` methods involving network interaction (e.g., `tx_commit`, `get_wallet_info_async`, `get_tx_async`, `get_all_intents`, `top_up`) are `async` and must be called with `await`.
- `await` can only be used inside an `async def` function.
- Use `asyncio.run(your_async_function())` to start the execution from synchronous code.

.. code-block:: python

    import asyncio
    from saline_sdk.rpc.client import Client
    from saline_sdk.account import Account

    # Incorrect (example using get_wallet_info_async):
    # info = client.get_wallet_info_async(pk)  # Returns a coroutine, doesn't run it

    # Correct (inside an async function):
    async def check_wallet(client: Client, pk: str):
        print(\"Checking wallet info...\")
        info = await client.get_wallet_info_async(pk) # Use await
        print(f\"Wallet Info: {info}\")
        return info

    # To run it:
    # client = Client(http_url=...)
    # pk_to_check = \"some_public_key...\"
    # asyncio.run(check_wallet(client, pk_to_check))

Auto-Generated Bindings
---------------------

**Problem**: Issues seemingly related to files like `bindings.py`.

**Solution**:
- The `saline_sdk/transaction/bindings.py` file is auto-generated from the Saline core definitions. **Do not modify it directly.** Changes will be overwritten.
- If you encounter issues with bindings, ensure you have the latest compatible version of the SDK installed and that it matches the version of the Saline node you are connecting to.
- Report persistent binding issues to the SDK developers.

Getting Help
-----------

If you encounter an issue that isn't addressed here, please:

1. Check the specific API documentation (:doc:`../api/index`)
2. Review the :doc:`examples` for usage patterns.
3. Report issues on the GitHub repository: https://github.com/risingsealabs/saline-sdk/issues
4. Contact support via appropriate channels if available.