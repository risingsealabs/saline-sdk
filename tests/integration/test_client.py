#!/usr/bin/env python3
"""
Integration tests for Saline Client class functionality.

These tests require a running Saline node to execute successfully.
"""

import pytest
import json
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import (
    Intent, All, Any, Finite, Temporary, Signature,
    Lit, Restriction, Relation, Token as SDKToken
)

# Markers to indicate these are integration tests that require a live chain
pytestmark = pytest.mark.integration


def display_intent_details(intent, indent=0, max_depth=3):
    """
    Helper function to display detailed information about an intent.

    Args:
        intent: The intent to display
        indent: Current indentation level
        max_depth: Maximum recursion depth to prevent infinite loops
    """
    if max_depth <= 0:
        print(" " * indent + "... (max depth reached)")
        return

    if intent is None:
        print(" " * indent + "No intent")
        return

    # Print the main intent type and details
    intent_type = intent.__class__.__name__
    print(" " * indent + f"Intent Type: {intent_type}")

    # Display type-specific properties
    if isinstance(intent, All):
        print(" " * indent + f"  All intent with {len(intent.children)} child intents:")
        for child_intent in intent.children:
            display_intent_details(child_intent, indent + 4, max_depth - 1)

    elif isinstance(intent, Any):
        print(" " * indent + f"  Any intent with threshold {intent.threshold} and {len(intent.children)} child intents:")
        for child_intent in intent.children:
            display_intent_details(child_intent, indent + 4, max_depth - 1)

    elif isinstance(intent, Finite):
        print(" " * indent + f"  Finite intent with {intent.uses} uses")
        display_intent_details(intent.inner, indent + 4, max_depth - 1)

    elif isinstance(intent, Temporary):
        print(" " * indent + f"  Temporary intent available {"after" if intent.availableAfter else "before"} {intent.timestamp}")
        display_intent_details(intent.inner, indent + 4, max_depth - 1)

    elif isinstance(intent, Signature):
        print(" " * indent + f"  Signature intent for public key: {intent.signer}")

    elif isinstance(intent, Restriction):
        lhs_str = str(intent.lhs) if hasattr(intent, 'lhs') else "Unknown"
        relation_str = str(intent.relation) if hasattr(intent, 'relation') else "Unknown"
        rhs_str = str(intent.rhs) if hasattr(intent, 'rhs') else "Unknown"
        print(" " * indent + f"  Restriction: {lhs_str} {relation_str} {rhs_str}")

    else:
        # For any other intent types
        print(" " * indent + f"  Properties: {vars(intent)}")


@pytest.fixture
def client():
    """Create a client connected to the local Saline node."""
    return Client(debug=False)  # Set debug=False to reduce log noise in tests


def test_client_status(client):
    """Test retrieving node status."""
    try:
        status = client.get_status()

        # Verify the structure of the status response
        assert "node_info" in status, "Status response missing node_info"
        assert "sync_info" in status, "Status response missing sync_info"

        # Print node information
        print(f"Node ID: {status.get('node_info', {}).get('id', 'Unknown')}")
        print(f"Node Version: {status.get('node_info', {}).get('version', 'Unknown')}")
        print(f"Latest Block Height: {status.get('sync_info', {}).get('latest_block_height', 'Unknown')}")
        print(f"Chain ID: {status.get('node_info', {}).get('network', 'Unknown')}")

    except Exception as e:
        pytest.skip(f"Failed to get node status: {e}")


@pytest.mark.asyncio
async def test_client_get_block(client):
    """Test retrieving block data."""
    try:
        # Get status to find the latest block height
        status = client.get_status()  # Removed await, get_status is synchronous
        latest_height = int(status.get('sync_info', {}).get('latest_block_height', '0'))

        # Get the latest block
        block_data = await client.get_block()  # Use async version

        # Verify block structure
        assert "block_meta" in block_data, "Block data missing block_meta"
        assert "block" in block_data, "Block data missing block"

        # Check block height matches or is very close to what we got from status
        block_height = int(block_data["block_meta"]["header"]["height"])
        assert abs(block_height - latest_height) <= 1, "Block height mismatch"

        print(f"Retrieved block at height: {block_height}")
        print(f"Block time: {block_data['block_meta']['header']['time']}")
        print(f"Block hash: {block_data['block_meta']['block_id']['hash']}")

        # Try to get a specific block (a few blocks back)
        if latest_height > 5:
            older_block = await client.get_block(latest_height - 5)  # Use async version
            older_height = int(older_block["block_meta"]["header"]["height"])
            assert older_height == latest_height - 5, "Specific block height mismatch"
            print(f"Successfully retrieved older block at height {older_height}")

    except Exception as e:
        pytest.fail(f"Failed to get block data: {e}")


@pytest.mark.asyncio
async def test_client_get_transactions(client):
    """Test retrieving transaction data."""
    try:
        # Get latest block to check for transactions
        block_data = await client.get_block()  # Use async version
        txs = block_data.get('block', {}).get('data', {}).get('txs', [])

        # If the latest block has transactions, try to decode them
        if txs:
            print(f"Found {len(txs)} transactions in the latest block")

            # Use the get_transactions method to get decoded transactions
            latest_height = int(block_data["block_meta"]["header"]["height"])
            transactions = await client.get_transactions(latest_height)  # Use async version

            assert len(transactions) == len(txs), "Transaction count mismatch"

            # Print transaction data
            for i, tx in enumerate(transactions):
                print(f"Transaction {i+1}: {json.dumps(tx, indent=2)[:100]}...")
        else:
            print("No transactions in the latest block")

            # Try to find a block with transactions (look back a few blocks)
            status = client.get_status()  # Removed await, get_status is synchronous
            latest_height = int(status.get('sync_info', {}).get('latest_block_height', '0'))

            # Look back up to 10 blocks for transactions
            found_txs = False
            for height in range(latest_height, max(0, latest_height - 10), -1):
                block = await client.get_block(height)  # Use async version
                txs = block.get('block', {}).get('data', {}).get('txs', [])
                if txs:
                    print(f"Found {len(txs)} transactions in block {height}")
                    transactions = await client.get_transactions(height)  # Use async version
                    assert len(transactions) == len(txs), "Transaction count mismatch"
                    found_txs = True
                    break
            if not found_txs:
                print("No transactions found in recent blocks, test passes but did not verify decoding.")

    except Exception as e:
        pytest.fail(f"Failed to get transaction data: {e}")


def test_client_direct_methods(client):
    """Test direct synchronous methods for ABCI queries."""
    # Test address from examples
    test_address = "a947ddcc9264a722671c6e4e283cf0e0f3d9cd7baadf5a67e5bbb81865f2560eb80e94591bdc4a80027f2c728be3a7cd"

    try:
        # Test direct balance query
        usdc_balance = client.get_balance(test_address, "USDC")
        assert usdc_balance is not None, "Balance query failed"
        print(f"USDC Balance: {usdc_balance}")

        # Test direct intent query
        intent_data = client.get_intent(test_address)
        assert intent_data is not None, "Intent query failed"
        print(f"Intent Type: {intent_data.get('tag')}")

        # Test all balances query
        all_balances = client.get_all_balances(test_address)
        assert isinstance(all_balances, dict), "All balances query failed"
        print("All token balances:")
        for token, balance in all_balances.items():
            print(f"  {token}: {balance}")

    except Exception as e:
        pytest.skip(f"Direct methods test failed: {e}")


@pytest.mark.asyncio
async def test_client_intent_queries(client):
    """Test methods for querying intents and wallet info."""
    # Test address from examples
    test_address = "a947ddcc9264a722671c6e4e283cf0e0f3d9cd7baadf5a67e5bbb81865f2560eb80e94591bdc4a80027f2c728be3a7cd"
    test_address2 = "b036c83f4653fe40b4e94159a507da3cd5f95a36ad1444052a0f82ef0f0c3e5a836f5315580de5c2aa90b4ee0bcc24a5"

    try:
        # Test all intents query
        print("\nTesting get_all_intents_async:")
        all_intents = await client.get_all_intents()  # Use async version
        assert isinstance(all_intents, dict), "All intents query failed"
        print(f"Retrieved {len(all_intents)} intents")

        # Display intent types found
        intent_types = {}
        for tag, intent_data in all_intents.items():
            if intent_data.get('intent'):
                intent_type = intent_data['intent'].__class__.__name__
                intent_types[intent_type] = intent_types.get(intent_type, 0) + 1
            elif intent_data.get('error'):
                 print(f"Intent {tag} has parsing error: {intent_data['error']}")

        print("Intent types found:")
        for intent_type, count in intent_types.items():
            print(f"  {intent_type}: {count}")

        # Display details for a sample intent if available
        if all_intents:
            print("\nSample intent details:")
            # Get first intent with a non-None sdk_intent
            displayed_sample = False
            for tag, intent_data in all_intents.items():
                if intent_data.get('intent'):
                    print(f"Details for intent {tag}:")
                    display_intent_details(intent_data['intent'])
                    displayed_sample = True
                    # Just show one as an example
                    break
            if not displayed_sample:
                 print("No successfully parsed intents found to display sample.")

        # Test wallet info query
        print("\nTesting get_wallet_info_async:")
        wallet_info = await client.get_wallet_info_async(test_address)  # Use async version
        assert isinstance(wallet_info, dict), "Wallet info query failed"

        # Check if we have balances
        balances = wallet_info.get("balances", {})
        print(f"Retrieved wallet with {len(balances)} balance entries")

        # Display balances
        print("Wallet balances:")
        if isinstance(balances, dict):
            for token, amount in balances.items():
                print(f"  {token}: {amount}")
        elif isinstance(balances, list):
            for item in balances:
                if isinstance(item, list) and len(item) == 2:
                    print(f"  {item[0]}: {item[1]}")
                else:
                    print(f"  {item}")

        # Check if we have an intent and display its details
        sdk_intent = wallet_info.get("sdk_intent")
        print("\nWallet intent:")
        if sdk_intent:
            print(f"Wallet has a parsed intent of type: {sdk_intent.__class__.__name__}")
            display_intent_details(sdk_intent)
        else:
            raw_intent = wallet_info.get("raw_intent")
            if raw_intent:
                print(f"Wallet has an unparsed intent: {raw_intent}")
            else:
                print("Wallet has no intent")

        # Test aggregate balances query
        print("\nTesting get_aggregate_balances_async:")
        addresses = [test_address, test_address2]
        aggregate_balances = await client.get_aggregate_balances_async(addresses)  # Use async version
        assert isinstance(aggregate_balances, dict), "Aggregate balances query failed"

        print(f"Retrieved {len(aggregate_balances)} aggregate balance entries")
        for token, amount in aggregate_balances.items():
            print(f"  {token}: {amount}")

    except Exception as e:
        pytest.fail(f"Intent query methods test failed: {e}")


if __name__ == "__main__":
    # This allows running the tests directly (not through pytest)
    # Useful for quick manual testing
    client = Client(debug=True)
    print("\n=== Testing client status ===")
    test_client_status(client)

    print("\n=== Testing client get_block ===")
    test_client_get_block(client)

    print("\n=== Testing client get_transactions ===")
    test_client_get_transactions(client)

    print("\n=== Testing client direct methods ===")
    test_client_direct_methods(client)

    print("\n=== Testing client intent queries ===")
    test_client_intent_queries(client)
