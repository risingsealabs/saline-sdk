==========
Quickstart
==========

This guide will help you get started with the Saline SDK quickly.

Basic Usage
==========

Initialize the SDK
-----------------

.. code-block:: python

    from saline_sdk import Saline
    
    # Initialize the SDK with your node connection
    saline = Saline(node_url="http://localhost:26657")
    
    # Optional: Enable debug logging
    saline = Saline(node_url="http://localhost:26657", debug=True)

Working with Accounts
--------------------

Create or load an account:

.. code-block:: python

    # Generate a new account directly through Saline
    mnemonic = saline.create_account()
    print(f"Save this mnemonic: {mnemonic}")
    
    # Or load an existing account from mnemonic
    saline.load_account("your twelve word mnemonic phrase goes here")
    
    # Alternatively, use the Account class directly
    from saline_sdk import Account
    
    # Create a new account
    account = Account.create()
    
    # Or load from mnemonic
    account = Account.from_mnemonic("your twelve word mnemonic phrase goes here")
    
    # Create subaccounts
    subaccount = account.create_subaccount("my_subaccount")
    print(f"Subaccount public key: {subaccount.public_key}")
    
    # Set a default subaccount
    account.set_default_subaccount("my_subaccount")

Checking Balances
----------------

.. code-block:: python

    # Get balance for the default subaccount
    balance = saline.get_balance(currency="USDC")
    print(f"Balance: {balance} USDC")
    
    # Get balance for a specific subaccount
    balance = saline.get_balance(subaccount="my_subaccount", currency="BTC")
    print(f"BTC Balance: {balance}")
    
    # Get all balances for a subaccount
    balances = saline.get_all_balances(subaccount="my_subaccount")
    for currency, amount in balances.items():
        print(f"{currency}: {amount}")
        
    # Asynchronous versions are also available
    import asyncio
    
    async def check_balances():
        balance = await saline.get_balance_async(currency="USDC")
        all_balances = await saline.get_all_balances_async()
        return balance, all_balances
    
    balance, all_balances = asyncio.run(check_balances())

Creating and Signing Transactions
-------------------

Using the transaction helpers:

.. code-block:: python

    from saline_sdk import transfer, sign, encodeSignedTx
    from saline_sdk.transaction.tx import Transaction
    import uuid
    
    # Create a transaction with a transfer instruction
    tx = Transaction(
        instructions=[
            transfer(
                sender=subaccount.public_key,
                recipient="destination_public_key",
                token="USDC",
                amount=100  # Integer amount
            )
        ]
    )
    
    # Set the signer
    tx.set_signer(subaccount.public_key)
    
    # Generate a nonce
    nonce = str(uuid.uuid4())
    
    # Sign the transaction
    signed_tx = sign(subaccount, nonce, tx)
    
    # Encode for network submission
    encoded_tx = encodeSignedTx(signed_tx)
    
    # Send the signed transaction
    tx_result = saline.send_transaction(encoded_tx)
    print(f"Transaction sent with hash: {tx_result.get('hash')}")

Using the convenience methods:

.. code-block:: python

    # Simple transfer using the convenience method
    tx_result = saline.transfer(
        to="recipient_public_key", 
        amount=50,  # Integer amount
        currency="USDC",
        from_subaccount="my_subaccount"  # Optional, uses default if not specified
    )
    print(f"Transfer completed with hash: {tx_result.get('hash')}")

Checking Transaction Status
-------------------------

.. code-block:: python

    # Wait for transaction confirmation
    receipt = saline.wait_for_transaction_receipt(tx_result.get('hash'))
    if receipt:
        print(f"Transaction confirmed: {receipt}")
    else:
        print("Transaction timed out - might still be pending")
    
    # Or check transaction directly
    tx_info = saline.client.get_tx(tx_result.get('hash'))
    if tx_info:
        print("Transaction successful!")
    else:
        print("Transaction not found or pending")

Asynchronous Operations
--------------------

All methods in the SDK have both synchronous and asynchronous versions:

.. code-block:: python

    import asyncio
    
    async def send_transaction_async():
        # Create and send transaction asynchronously
        tx_result = await saline.send_transaction_async(encoded_tx)
        
        # Wait for confirmation
        receipt = await saline.wait_for_transaction_receipt_async(tx_result.get('hash'))
        return receipt
    
    # Run the async function
    receipt = asyncio.run(send_transaction_async())
    
Working with Token Swaps
--------------------

.. code-block:: python

    from saline_sdk import swap
    
    # Create a swap transaction
    tx = Transaction(
        instructions=[
            swap(
                sender=subaccount.public_key,
                recipient="recipient_public_key",
                give_token="USDC",
                give_amount=100,
                take_token="BTC",
                take_amount=1
            )
        ]
    )
    
    # The rest of the signing and submission process is the same as above 