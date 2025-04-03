#!/usr/bin/env python3
"""
Swap Intent Example

This example demonstrates how to create and set swap intents using the Saline high-level interface:
1. Create a wallet and subaccounts
2. Create a swap intent (USDC to BTC)
3. Set the intent on a subaccount
4. Query the intent
"""

import time
from saline_sdk import Saline
from saline_sdk.rpc.error import RPCError

NODE_URL = "http://localhost:26657"
TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"

def main():
    print("Saline SDK Swap Intent Example")
    print("-" * 50)
    
    saline = Saline(node_url=NODE_URL, mnemonic=TEST_MNEMONIC)
    
    if not saline.is_connected():
        raise ConnectionError(f"Could not connect to node at {NODE_URL}")
    
    print(f"✅ Connected to node at {NODE_URL}")
    print("-" * 50)
    
    print("Creating trading subaccount...")
    trading = saline.account.create_subaccount("trading")
    print(f"Trading subaccount public key: {trading.public_key}")
    print("-" * 50)
    
    print("Creating swap intent: 10 USDC for 0.001 BTC...")
    
    intent = saline.create_swap_intent(
        give_token="USDC",
        give_amount=10.0,
        want_token="BTC",
        want_amount=0.001
    )
    
    print("Swap intent created!")
    print(f"Intent details:")
    print(f"  - Give: 10.0 USDC")
    print(f"  - Receive: 0.001 BTC")
    print("-" * 50)
    
    print("Setting intent on trading subaccount...")
    
    try:
        tx_hash = saline.set_intent(
            intent=intent,
            subaccount="trading",
            wait_for_confirmation=True
        )
        print(f"Intent set successfully! Transaction hash: {tx_hash}")
        print("Intent setting confirmed!")
        print("-" * 50)
        
        print("Querying current intent on trading subaccount...")
        
        current_intent = saline.get_intent(subaccount="trading")
        print("Current intent retrieved from node:")
        print(f"  - Send: {current_intent['send']['amount']} {current_intent['send']['token']}")
        print(f"  - Receive: {current_intent['receive']['amount']} {current_intent['receive']['token']}")
        print(f"  - Relation: {current_intent['relation']}")
        print("-" * 50)
        
        print("Removing intent from trading subaccount...")
        
        remove_tx = saline.set_intent(
            intent=None,
            subaccount="trading",
            wait_for_confirmation=True
        )
        print(f"Intent removed successfully! Transaction hash: {remove_tx}")
        print("Intent removal confirmed!")
        
    except RPCError as e:
        print(f"RPC error during intent operations: {e}")
    except Exception as e:
        print(f"Error during intent operations: {e}")
    
    print("-" * 50)
    print("Swap intent operations complete!")

if __name__ == "__main__":
    main() 