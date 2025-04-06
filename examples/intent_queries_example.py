#!/usr/bin/env python3
"""
Intent Querying Example

This example demonstrates how to use the Saline SDK to query intents and wallet information.
It shows three main capabilities:
1. Get all intents in the system
2. Get wallet information including intent for a specific address
3. Get aggregate balances across multiple addresses

Usage:
    python intent_queries_example.py
"""

from typing import Optional
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import Intent, All, Any as AnyIntent

RPC_URL = "http://localhost:26657"
def print_intent_structure(intent: Optional[Intent], indent: int = 0) -> None:
    """Print an intent's structure with indentation to show hierarchy."""
    if intent is None:
        print(f"{' ' * indent}None")
        return
    
    intent_type = intent.__class__.__name__
    print(f"{' ' * indent}{intent_type}")
    
    if isinstance(intent, All) or isinstance(intent, AnyIntent):
        for i, child in enumerate(intent.children):
            print(f"{' ' * (indent+2)}Child {i+1}:")
            print_intent_structure(child, indent + 4)
            

def main():
    client = Client(debug=True, http_url=RPC_URL)
    

    address1 = "a947ddcc9264a722671c6e4e283cf0e0f3d9cd7baadf5a67e5bbb81865f2560eb80e94591bdc4a80027f2c728be3a7cd"
    address2 = "b036c83f4653fe40b4e94159a507da3cd5f95a36ad1444052a0f82ef0f0c3e5a836f5315580de5c2aa90b4ee0bcc24a5"
    
    print("\n========== 1. Query All Intents ==========")
    all_intents = client.get_all_intents()
    print(f"Found {len(all_intents)} intents")
    
    # Count intent types
    intent_types = {}
    for tag, data in all_intents.items():
        if data.get('intent'):
            intent_type = data['intent'].__class__.__name__
            intent_types[intent_type] = intent_types.get(intent_type, 0) + 1
    
    print("\nIntent Type Summary:")
    for intent_type, count in intent_types.items():
        print(f"  {intent_type}: {count}")
    
    # Print the first intent as an example
    if all_intents:
        print("\nExample Intent Structure:")
        for tag, data in all_intents.items():
            if data.get('intent'):
                print(f"Intent {tag}:")
                print_intent_structure(data['intent'])
                break
    
    print("\n========== 2. Query Wallet Info ==========")
    wallet_info = client.get_wallet_info(address1)
    
    # Print balances
    balances = wallet_info.get('balances', {})
    print("Wallet Balances:")
    if isinstance(balances, dict):
        for token, amount in balances.items():
            print(f"  {token}: {amount}")
    elif isinstance(balances, list):
        for item in balances:
            if isinstance(item, list) and len(item) == 2:
                token, amount = item
                print(f"  {token}: {amount}")
    
    # Print intent structure
    intent = wallet_info.get('sdk_intent')
    print("\nWallet Intent Structure:")
    print_intent_structure(intent)
    
    print("\n========== 3. Query Aggregate Balances ==========")
    addresses = [address1, address2]
    aggregate_balances = client.get_aggregate_balances(addresses)
    
    print(f"Aggregate Balances across {len(addresses)} addresses:")
    for token, amount in aggregate_balances.items():
        print(f"  {token}: {amount}")


if __name__ == "__main__":
    main() 