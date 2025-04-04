"""
Simple Swap Matcher Example for Saline Protocol

Demonstrates how to:
1. Create multiple accounts with different swap intents
2. Find matching swap pairs on-chain
3. Fulfill the matching swap
"""

import asyncio
import json
import uuid
from typing import Dict, List, Tuple, Optional
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, TransferFunds, Signed,
    Send, Receive, Flow, Token, Restriction, Relation
)
from saline_sdk.transaction.tx import prepareSimpleTx, encodeSignedTx
from saline_sdk.rpc.client import Client
from saline_sdk.crypto import BLS

# Test mnemonic - only use for development
TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "http://localhost:26657"

# Define token pairs and amounts for our swap intents
SWAP_CONFIGS = [
    # The matching pair
    {"name": "alice", "give_token": "USDC", "give_amount": 10, "want_token": "BTC", "want_amount": 0.001},
    {"name": "bob", "give_token": "BTC", "give_amount": 0.001, "want_token": "USDC", "want_amount": 10},
    
    # Non-matching intents (different tokens, amounts, or rates)
    {"name": "carol", "give_token": "ETH", "give_amount": 1, "want_token": "USDT", "want_amount": 1000},
    {"name": "dave", "give_token": "USDT", "give_amount": 2000, "want_token": "ETH", "want_amount": 1},
    {"name": "eve", "give_token": "USDC", "give_amount": 20, "want_token": "BTC", "want_amount": 0.001},  # Different rate
    {"name": "frank", "give_token": "BTC", "give_amount": 0.002, "want_token": "USDC", "want_amount": 10},  # Different rate
    {"name": "grace", "give_token": "USDC", "give_amount": 10, "want_token": "ETH", "want_amount": 0.1},  # Different token
    {"name": "hank", "give_token": "SALT", "give_amount": 100, "want_token": "USDT", "want_amount": 50}
]

async def create_accounts_with_swap_intents(client: Client, root_account: Account) -> Dict[str, Account]:
    """Create accounts and set up different swap intents for each"""
    print("=== Setting up accounts with swap intents ===")
    
    accounts = {}
    
    # Create each account and setup its swap intent
    for config in SWAP_CONFIGS:
        name = config["name"]
        give_token = config["give_token"]
        give_amount = config["give_amount"]
        want_token = config["want_token"]
        want_amount = config["want_amount"]
        
        # Create subaccount
        account = root_account.create_subaccount(label=name)
        accounts[name] = account
        
        # "I'll send give_token if I receive want_token"
        swap_intent = Send(Flow(None, Token[give_token])) * give_amount <= Receive(Flow(None, Token[want_token])) * want_amount
        
        set_intent_instruction = SetIntent(account.public_key, swap_intent)
        tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))
        signed_tx = prepareSimpleTx(account, tx)
        
        result = await client.tx_commit(signed_tx)
        
        if result.get("error") is None:
            print(f"✓ Created swap intent for {name}: Give {give_amount} {give_token} for {want_amount} {want_token}")
        else:
            print(f"✗ Failed to create swap intent for {name}: {result.get('error')}")
    
    return accounts

async def find_matching_swaps(client: Client, accounts: Dict[str, Account]) -> List[Tuple[Dict, Dict]]:
    """Find matching swap pairs in the system"""
    print("\n=== Finding matching swap pairs ===")
    
    matching_pairs = []
    
    # For simplicity, since we created all the accounts and intents ourselves, 
    # we'll use a direct approach to find matching pairs
    for i, config1 in enumerate(SWAP_CONFIGS):
        for config2 in SWAP_CONFIGS[i+1:]:
            # Check if the swap configs match (one's give matches the other's want)
            if (config1["give_token"] == config2["want_token"] and 
                config1["want_token"] == config2["give_token"]):
                
                # Check if exchange rates are compatible
                rate1 = config1["give_amount"] / config1["want_amount"]  
                rate2 = config2["want_amount"] / config2["give_amount"]
                
                if rate1 <= rate2:  # Rate is acceptable
                    account1 = accounts[config1["name"]]
                    account2 = accounts[config2["name"]]
                    
                    swap1 = {
                        "address": account1.public_key,
                        "name": config1["name"],
                        "give_token": config1["give_token"],
                        "give_amount": config1["give_amount"],
                        "want_token": config1["want_token"],
                        "want_amount": config1["want_amount"]
                    }
                    
                    swap2 = {
                        "address": account2.public_key,
                        "name": config2["name"],
                        "give_token": config2["give_token"],
                        "give_amount": config2["give_amount"],
                        "want_token": config2["want_token"],
                        "want_amount": config2["want_amount"]
                    }
                    
                    matching_pairs.append((swap1, swap2))
                    print(f"Found matching swap pair:")
                    print(f"  - {swap1['name']} offers {swap1['give_amount']} {swap1['give_token']} for {swap1['want_amount']} {swap1['want_token']}")
                    print(f"  - {swap2['name']} offers {swap2['give_amount']} {swap2['give_token']} for {swap2['want_amount']} {swap2['want_token']}")
    
    print(f"Found {len(matching_pairs)} matching pairs")
    return matching_pairs

async def fulfill_swap_pair(client: Client, swap_pair: Tuple[Dict, Dict], matcher_account: Account):
    """Fulfill a matching swap pair"""
    swap1, swap2 = swap_pair
    print(f"\n=== Fulfilling swap between {swap1['name']} and {swap2['name']} ===")
    
    # Create two transfer instructions to fulfill the swap
    instruction1 = TransferFunds(
        source=swap1["address"],
        target=swap2["address"],
        funds={swap1["give_token"]: swap1["give_amount"]}
    )
    
    instruction2 = TransferFunds(
        source=swap2["address"],
        target=swap1["address"],
        funds={swap2["give_token"]: swap2["give_amount"]}
    )
    
    tx = Transaction(instructions=NonEmpty.from_list([instruction1, instruction2]))
    
    # Use the dedicated matcher account to execute the swap
    # The matcher doesn't need to be either of the swap parties
    # The intents themselves provide the authorization for the transfers
    print(f"Using dedicated matcher account to execute the swap...")
    signed_tx = prepareSimpleTx(matcher_account, tx)
    
    # Submit to the network
    try:
        print("Submitting transaction to the network...")
        result = await client.tx_commit(signed_tx)
        
        if result.get("error") is None:
            print("✓ Swap successful!")
            print(f"  - {swap1['name']} sent {swap1['give_amount']} {swap1['give_token']} and received {swap1['want_amount']} {swap1['want_token']}")
            print(f"  - {swap2['name']} sent {swap2['give_amount']} {swap2['give_token']} and received {swap2['want_amount']} {swap2['want_token']}")
        else:
            print(f"✗ Swap failed: {result.get('error')}")
            print("Note: This could happen if the intents don't provide sufficient authorization or have additional conditions")
    except Exception as e:
        print(f"✗ Error fulfilling swap: {str(e)}")

async def main():
    print("=== Saline SDK Simple Swap Matcher Example ===\n")
    
    # Initialize the client
    client = Client(http_url=RPC_URL)

    root = Account.from_mnemonic(TEST_MNEMONIC)

    matcher = root.create_subaccount(label="matcher")
    print(f"Created dedicated matcher account: {matcher.public_key[:10]}...")
    
    
    accounts = await create_accounts_with_swap_intents(client, root)
    
    matching_pairs = await find_matching_swaps(client, accounts)
    
    if matching_pairs:
        await fulfill_swap_pair(client, matching_pairs[0], matcher)
    else:
        print("\nNo matching swap pairs found")

if __name__ == "__main__":
    asyncio.run(main())
