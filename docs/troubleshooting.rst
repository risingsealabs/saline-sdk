===============
Troubleshooting
===============

This page provides solutions to common issues you might encounter when using the Saline SDK.

Connection Issues
----------------

**Problem**: Cannot connect to the Saline node.

**Solution**: 
- Verify the node URL is correct and the node is running
- Check network connectivity between your application and the node
- Ensure the node's RPC endpoint is accessible from your network

.. code-block:: python

    # Check node connection
    from saline_sdk import Saline
    
    saline = Saline(node_url="http://localhost:26657")
    
    # You can debug connection issues with:
    if not saline.is_connected():
        print("Cannot connect to node. Check your node_url and network connectivity.")

Transaction Errors
----------------

**Problem**: Transaction fails to be submitted or is rejected.

**Solution**:
- Check that the account has sufficient funds
- Verify the transaction is properly signed
- Ensure the nonce is unique and not already used

.. code-block:: python

    # Get the balance before attempting a transfer
    balance = saline.get_balance(currency="USDC")
    if balance < amount_to_send:
        print("Insufficient funds")
    
    # Use a unique nonce for each transaction
    import uuid
    nonce = str(uuid.uuid4())

Account Issues
------------

**Problem**: Unable to access subaccounts or getting "No default subaccount" errors.

**Solution**:
- Ensure you've created a subaccount before trying to use it
- Set a default subaccount if you're not specifying a subaccount name

.. code-block:: python

    # Create a subaccount if you don't have one
    subaccount = saline.account.create_subaccount("my_subaccount")
    
    # Set as default
    saline.account.default_subaccount = "my_subaccount"
    
    # Now you can use methods without specifying the subaccount name
    balance = saline.get_balance()  # Uses the default subaccount

Using Async Methods
----------------

**Problem**: Seeing "coroutine was never awaited" errors.

**Solution**:
- Async methods must be called with `await` inside an async function
- Use asyncio.run() to call async functions from synchronous code

.. code-block:: python

    # Incorrect:
    balance = saline.get_balance_async()  # This returns a coroutine, not the balance
    
    # Correct (inside an async function):
    async def check_balance():
        balance = await saline.get_balance_async()
        return balance
    
    # Correct (from synchronous code):
    import asyncio
    balance = asyncio.run(saline.get_balance_async())

Auto-Generated Bindings
---------------------

**Problem**: Errors related to the auto-generated bindings.py file.

**Solution**:
- Don't modify the bindings.py file directly, as it's auto-generated
- For documentation purposes, update the bindings_docstrings.py file
- For tests, use the test skipping configuration to handle version mismatches

Getting Help
-----------

If you encounter an issue that isn't addressed here, please:

1. Check the API documentation for correct usage
2. Look at the examples for guidance
3. Contact support at support@risingsealabs.com 