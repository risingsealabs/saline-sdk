"""
Simple Swap Matcher Example for Saline Protocol

Demonstrates how to:
1. Create multiple accounts with different swap intents
2. Find matching swap pairs on-chain by analyzing all intents
3. Fulfill the matching swap
"""

import asyncio
import json
from typing import Dict, List, Tuple, Optional, Any
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, TransferFunds, Signed,
    Send, Receive, Flow, Token, Restriction, Relation
)
from saline_sdk.transaction.tx import prepareSimpleTx, encodeSignedTx
from saline_sdk.rpc.client import Client
from saline_sdk.crypto import BLS

# Debug mode - set to True to see more detailed output
DEBUG = True

# Test mnemonic - only use for development
TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "http://localhost:26657"

# Define token pairs and amounts for our swap intents
SWAP_CONFIGS = [
    # The matching pair
    {"name": "alice", "give_token": "USDC", "give_amount": 100, "want_token": "BTC", "want_amount": 1},
    {"name": "bob", "give_token": "BTC", "give_amount": 1, "want_token": "USDC", "want_amount": 100},
    
    # Non-matching intents (different tokens, amounts, or rates)
    {"name": "carol", "give_token": "ETH", "give_amount": 10, "want_token": "USDT", "want_amount": 10000},
    {"name": "dave", "give_token": "USDT", "give_amount": 20000, "want_token": "ETH", "want_amount": 10},
    {"name": "eve", "give_token": "USDC", "give_amount": 200, "want_token": "BTC", "want_amount": 1},  # Different rate
    {"name": "frank", "give_token": "BTC", "give_amount": 2, "want_token": "USDC", "want_amount": 100},  # Different rate
    {"name": "grace", "give_token": "USDC", "give_amount": 100, "want_token": "ETH", "want_amount": 1},  # Different token
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

def extract_swap_details(intent_data: Dict[str, Any], wallet_address: str) -> Optional[Dict]:
    """
    Extracts swap details from an intent.
    We make the simplification that a swap contains at least two opposite flows.
    """
    try:
        # First, check if we have data
        if not intent_data:
            if DEBUG:
                print(f"No intent data for {wallet_address[:10]}...")
            return None
            
        # Check for the raw_intent field instead of intent
        if 'raw_intent' in intent_data and intent_data['raw_intent']:
            raw_intent = intent_data['raw_intent']
            if DEBUG:
                print(f"Using raw_intent for {wallet_address[:10]}...")
            
            # The raw_intent appears to be an array with the first element containing the intent structure
            if isinstance(raw_intent, list) and len(raw_intent) > 0:
                intent_struct = raw_intent[0]
                
                # Look for restrictions in different places
                
                # Case 1: Direct restriction
                if isinstance(intent_struct, dict) and intent_struct.get('tag') == 'Restriction':
                    return process_restriction(intent_struct, wallet_address)
                
                # Case 2: All/Any with children containing restrictions
                if isinstance(intent_struct, dict) and intent_struct.get('tag') in ['All', 'Any'] and 'children' in intent_struct:
                    for child in intent_struct['children']:
                        # Check if child is a direct restriction
                        if child.get('tag') == 'Restriction':
                            result = process_restriction(child, wallet_address)
                            if result:
                                return result
                        
                        # Check if child is another All/Any with nested restrictions
                        if child.get('tag') in ['All', 'Any'] and 'children' in child:
                            for nested_child in child['children']:
                                if nested_child.get('tag') == 'Restriction':
                                    result = process_restriction(nested_child, wallet_address)
                                    if result:
                                        return result
        
        # Fall back to the original intent field check
        elif 'intent' in intent_data and intent_data['intent']:
            intent = intent_data['intent']
            if DEBUG:
                print(f"Using intent field for {wallet_address[:10]}...")
            
            # Look for restrictions directly
            if 'tag' in intent and intent['tag'] == 'Restriction':
                return process_restriction(intent, wallet_address)
            
            # Look for nested restrictions in children
            if 'children' in intent:
                for child in intent['children']:
                    if child.get('tag') == 'Restriction':
                        result = process_restriction(child, wallet_address)
                        if result:
                            return result
        
        if DEBUG:
            print(f"No matching swap pattern found for {wallet_address[:10]}...")
        return None
    except Exception as e:
        print(f"Error extracting swap details for {wallet_address[:10]}...: {str(e)}")
        return None

def process_restriction(restriction: Dict[str, Any], wallet_address: str) -> Optional[Dict]:
    """
    Process a restriction to extract swap details.
    """
    try:
        if DEBUG:
            print(f"Processing restriction for {wallet_address[:10]}...")
        
        lhs = restriction.get('lhs', {})
        rhs = restriction.get('rhs', {})
        relation = restriction.get('relation')
        
        # Extract Send-Receive pattern
        if lhs.get('tag') == 'Send' and rhs.get('tag') == 'Receive':
            if DEBUG:
                print(f"Found Send-Receive pattern in restriction for {wallet_address[:10]}...")
            
            # Extract flows
            send_flow = lhs.get('flow', {})
            receive_flow = rhs.get('flow', {})
            
            # Get token info
            send_token = send_flow.get('token')
            receive_token = receive_flow.get('token')
            
            # Get amount info - multiple possible locations
            send_amount = None
            if 'value' in rhs:
                send_amount = rhs.get('value')
            elif restriction.get('lhs_value', {}).get('value') is not None:
                send_amount = restriction.get('lhs_value', {}).get('value')
            
            receive_amount = None
            if 'value' in rhs:
                receive_amount = rhs.get('value')
            elif restriction.get('rhs_value', {}).get('value') is not None:
                receive_amount = restriction.get('rhs_value', {}).get('value')
            
            # Check if we have all the required data
            if send_token and receive_token and send_amount is not None and receive_amount is not None:
                if DEBUG:
                    print(f"Successfully extracted Send-Receive swap for {wallet_address[:10]}...")
                return {
                    "address": wallet_address,
                    "give_token": send_token,
                    "give_amount": send_amount,
                    "want_token": receive_token,
                    "want_amount": receive_amount
                }
        
        # Extract Receive-Send pattern
        elif lhs.get('tag') == 'Receive' and rhs.get('tag') == 'Send':
            if DEBUG:
                print(f"Found Receive-Send pattern in restriction for {wallet_address[:10]}...")
            
            # Extract flows
            receive_flow = lhs.get('flow', {})
            send_flow = rhs.get('flow', {})
            
            # Get token info
            receive_token = receive_flow.get('token')
            send_token = send_flow.get('token')
            
            # Get amount info - multiple possible locations
            receive_amount = None
            if 'value' in lhs:
                receive_amount = lhs.get('value')
            elif restriction.get('lhs_value', {}).get('value') is not None:
                receive_amount = restriction.get('lhs_value', {}).get('value')
            
            send_amount = None
            if 'value' in rhs:
                send_amount = rhs.get('value')
            elif restriction.get('rhs_value', {}).get('value') is not None:
                send_amount = restriction.get('rhs_value', {}).get('value')
            
            # Check if we have all the required data
            if send_token and receive_token and send_amount is not None and receive_amount is not None:
                if DEBUG:
                    print(f"Successfully extracted Receive-Send swap for {wallet_address[:10]}...")
                return {
                    "address": wallet_address,
                    "give_token": send_token,
                    "give_amount": send_amount,
                    "want_token": receive_token,
                    "want_amount": receive_amount
                }
        
        # Look for simple token transfers
        if lhs.get('tag') == 'Send' and rhs.get('tag') == 'Lit':
            if DEBUG:
                print(f"Found Send with value for {wallet_address[:10]}...")
            
            send_flow = lhs.get('flow', {})
            send_token = send_flow.get('token')
            send_amount = rhs.get('value')
            
            if send_token and send_amount is not None:
                # This is probably a faucet or similar, not a swap
                if DEBUG:
                    print(f"Found simple Send of {send_amount} {send_token} for {wallet_address[:10]}...")
                # We don't return this as a swap since it's not a swap intent
                return None
        
        return None
    except Exception as e:
        print(f"Error processing restriction for {wallet_address[:10]}...: {str(e)}")
        return None

async def find_matching_swaps_from_blockchain(client: Client) -> List[Tuple[Dict, Dict]]:
    """Find matching swap pairs by analyzing all intents on the blockchain"""
    print("\n=== Finding matching swap pairs from all blockchain intents ===")
    
    # Get all intents from the blockchain
    all_intents = await client.get_all_intents()
    print(f"Found {len(all_intents)} total intents on the blockchain")
    
    # For debugging - print sample intents
    if DEBUG and all_intents:
        count = 0
        for address, intent_data in all_intents.items():
            if count < 3:  # Print the first few intents
                print(f"\nIntent {count+1} for address {address[:10]}...")
                print(json.dumps(intent_data, indent=2))
                count += 1
    
    # Extract swap details from each intent
    swaps = []
    for address, intent_data in all_intents.items():
        swap_details = extract_swap_details(intent_data, address)
        if swap_details:
            swaps.append(swap_details)
            if DEBUG:
                print(f"Found swap intent: {json.dumps(swap_details, indent=2)}")
    
    print(f"Extracted {len(swaps)} swap intents")
    
    # Find matching pairs
    matching_pairs = []
    for i, swap1 in enumerate(swaps):
        for swap2 in swaps[i+1:]:
            # Check if the swap configs match (one's give matches the other's want)
            if (swap1["give_token"] == swap2["want_token"] and 
                swap1["want_token"] == swap2["give_token"]):
                
                # Check if exchange rates are compatible
                # For integers, we multiply to avoid floating point division
                rate1_numerator = swap1["give_amount"] * swap2["give_amount"]
                rate1_denominator = swap1["want_amount"] * swap2["want_amount"]
                
                # Rate is acceptable if what I give relative to what I want is favorable
                if rate1_numerator <= rate1_denominator:
                    matching_pairs.append((swap1, swap2))
                    print(f"Found matching swap pair:")
                    print(f"  - {swap1['address'][:10]}... offers {swap1['give_amount']} {swap1['give_token']} for {swap1['want_amount']} {swap1['want_token']}")
                    print(f"  - {swap2['address'][:10]}... offers {swap2['give_amount']} {swap2['give_token']} for {swap2['want_amount']} {swap2['want_token']}")
    
    print(f"Found {len(matching_pairs)} matching pairs")
    return matching_pairs

async def fulfill_swap_pair(client: Client, swap_pair: Tuple[Dict, Dict], matcher_account: Account):
    """Fulfill a matching swap pair"""
    swap1, swap2 = swap_pair
    print(f"\n=== Fulfilling swap between {swap1['address'][:10]}... and {swap2['address'][:10]}... ===")
    
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
            print(f"  - Account {swap1['address'][:10]}... sent {swap1['give_amount']} {swap1['give_token']} and received {swap1['want_amount']} {swap1['want_token']}")
            print(f"  - Account {swap2['address'][:10]}... sent {swap2['give_amount']} {swap2['give_token']} and received {swap2['want_amount']} {swap2['want_token']}")
        else:
            print(f"✗ Swap failed: {result.get('error')}")
            print("Note: This could happen if the intents don't provide sufficient authorization or have additional conditions")
    except Exception as e:
        print(f"✗ Error fulfilling swap: {str(e)}")

async def main():
    print("=== Saline SDK Simple Swap Matcher Example ===\n")
    
    # Initialize the client
    client = Client(http_url=RPC_URL)

    #root = Account.from_mnemonic(TEST_MNEMONIC)
    root = Account.create() 

    matcher = root.create_subaccount(label="matcher")
    print(f"Created dedicated matcher account: {matcher.public_key[:10]}...")
    
    
    accounts = await create_accounts_with_swap_intents(client, root)
    
    # Allow some time for intents to be stored (in a real system, this would be managed differently)
    print("Waiting for intents to be stored on the blockchain...")
    await asyncio.sleep(10)  # Increased delay to 10 seconds
    
    matching_pairs = await find_matching_swaps_from_blockchain(client)
    
    if matching_pairs:
        await fulfill_swap_pair(client, matching_pairs[0], matcher)
    else:
        print("\nNo matching swap pairs found")

if __name__ == "__main__":
    asyncio.run(main())
