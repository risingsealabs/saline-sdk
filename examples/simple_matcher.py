"""
Simple Swap Matcher Example for Saline Protocol

Demonstrates how to:
1. Create multiple accounts with different swap intents
2. Find matching swap pairs on-chain by analyzing all intents
3. Fulfill the matching swap
"""

import asyncio
import json
from typing import Dict, List, Tuple, Optional, Any, TypedDict

from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, TransferFunds, Signed,
    Send, Receive, Flow, Token, Restriction, Relation, All, Any, Lit, Expr # Added necessary imports
)
from saline_sdk.transaction.tx import prepareSimpleTx, encodeSignedTx
from saline_sdk.rpc.client import Client
from saline_sdk.crypto import BLS
from saline_sdk.rpc.testnet.faucet import top_up
RPC_URL = "http://localhost:26657"

# --- Type Hinting for Clarity ---
class SwapDetails(TypedDict):
    address: str
    give_token: str
    give_amount: int
    want_token: str
    want_amount: int

# Define token pairs and amounts for our swap intents
SWAP_CONFIGS = [
    # The matching pair
    {"name": "alice", "give_token": "USDC", "give_amount": 100, "want_token": "BTC", "want_amount": 1},
    {"name": "bob", "give_token": "BTC", "give_amount": 1, "want_token": "USDC", "want_amount": 100},
    # Non-matching intents
    {"name": "carol", "give_token": "ETH", "give_amount": 10, "want_token": "USDT", "want_amount": 10000},
    {"name": "dave", "give_token": "USDT", "give_amount": 20000, "want_token": "ETH", "want_amount": 10},
    {"name": "eve", "give_token": "USDC", "give_amount": 200, "want_token": "BTC", "want_amount": 1},
    {"name": "frank", "give_token": "BTC", "give_amount": 2, "want_token": "USDC", "want_amount": 100},
    {"name": "grace", "give_token": "USDC", "give_amount": 100, "want_token": "ETH", "want_amount": 1},
    {"name": "hank", "give_token": "SALT", "give_amount": 100, "want_token": "USDT", "want_amount": 50}
]

async def create_accounts_with_swap_intents(client: Client, root_account: Account) -> Dict[str, Account]:
    """Create accounts and set up different swap intents for each"""
    print("=== Setting up accounts and swap intents... ===")
    accounts = {}
    intent_creation_tasks = []

    for config in SWAP_CONFIGS:
        name = config["name"]
        account = root_account.create_subaccount(label=name)
        accounts[name] = account

        # Fund the account using the testnet faucet (likely provides SALT)
        try:
            print(f"  -> Requesting faucet top-up for {name} ({account.public_key[:10]}...)")
            await top_up(account=account, client=client, use_dynamic_amounts=False)
            print(f"     Faucet top-up request submitted for {name} using default amounts.")
            wallet_info = await client.get_wallet_info_async(account.public_key)
            print(f"{name} balance: {wallet_info.get('balances', [])}")
        except Exception as e:
            print(f"WARN: Faucet top-up failed for {name}: {e}")

        send_restriction = Restriction(
            Send(Flow(None, Token[config["give_token"]])),
            Relation.EQ,
            Lit(config["give_amount"])
        )
        receive_restriction = Restriction(
            Receive(Flow(None, Token[config["want_token"]])),
            Relation.EQ,
            Lit(config["want_amount"])
        )
        swap_intent = All([send_restriction, receive_restriction])

        set_intent_instruction = SetIntent(account.public_key, swap_intent)
        tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))
        signed_tx = prepareSimpleTx(account, tx)

        # Add the submission task to a list to run concurrently
        intent_creation_tasks.append(
            client.tx_commit(signed_tx)
        )

    # Wait for all intent transactions to complete
    results = await asyncio.gather(*intent_creation_tasks)

    # Check results and print status for each
    print("\n--- Intent Creation Status ---")
    for i, result in enumerate(results):
        config = SWAP_CONFIGS[i]
        name = config["name"]
        give_token = config["give_token"]
        give_amount = config["give_amount"]
        want_token = config["want_token"]
        want_amount = config["want_amount"]
        if result.get("error") is None:
            print(f"✓ Intent for {name}: Give {give_amount} {give_token} for {want_amount} {want_token}")
        else:
            print(f"✗ Failed intent for {name}: {result.get('error')}")

    return accounts

def _extract_restriction_details(restriction_node: Dict[str, Any]) -> Optional[Dict]:
    """Helper to extract token and amount from a Send/Receive Restriction"""
    if not isinstance(restriction_node, dict) or restriction_node.get('tag') != 'Restriction':
        return None

    lhs = restriction_node.get('lhs', {})
    rhs = restriction_node.get('rhs', {})
    relation = restriction_node.get('relation')

    if relation != Relation.EQ.name or not isinstance(rhs, dict) or rhs.get('tag') != 'Lit':
        return None

    amount = rhs.get('value')
    if amount is None:
        return None

    flow_node = lhs.get('flow', {})
    token_str = flow_node.get('token')
    if not token_str:
        return None

    tag_type = lhs.get('tag')
    if tag_type == 'Send':
        return {'type': 'send', 'token': token_str, 'amount': int(amount)}
    elif tag_type == 'Receive':
        return {'type': 'receive', 'token': token_str, 'amount': int(amount)}
    else:
        return None

def _find_swap_in_intent_node(intent_node: Dict[str, Any]) -> Optional[Tuple[Dict, Dict]]:
    """Recursively searches an intent structure for the Send/Receive pair"""
    if not isinstance(intent_node, dict):
        return None

    tag = intent_node.get('tag')

    if tag == 'All':
        children = intent_node.get('children', [])
        send_details = None
        receive_details = None

        for child in children:
            details = _extract_restriction_details(child)
            if details:
                if details['type'] == 'send' and not send_details:
                    send_details = details
                elif details['type'] == 'receive' and not receive_details:
                    receive_details = details
            if send_details and receive_details:
                return send_details, receive_details

        # Recurse if not found directly
        if not (send_details and receive_details):
            for child in children:
                if isinstance(child, dict) and child.get('tag') in ['All', 'Any']:
                    nested_result = _find_swap_in_intent_node(child)
                    if nested_result:
                        return nested_result

    elif tag == 'Any':
         children = intent_node.get('children', [])
         for child in children:
            if isinstance(child, dict) and child.get('tag') in ['All', 'Any']:
                nested_result = _find_swap_in_intent_node(child)
                if nested_result:
                    return nested_result

    return None # Ignore Restriction, Finite, Temporary etc. at this level

def extract_swap_details(intent_data: Dict[str, Any], wallet_address: str) -> Optional[SwapDetails]:
    """
    Extracts swap details (give/want tokens and amounts) from raw intent data.
    Searches for the common All([Send==Lit, Receive==Lit]) pattern.
    """
    if not intent_data:
        return None

    raw_intent_list = intent_data.get('raw_intent')
    if not isinstance(raw_intent_list, list) or not raw_intent_list:
        return None

    intent_structure = raw_intent_list[0]

    try:
        swap_components = _find_swap_in_intent_node(intent_structure)

        if swap_components:
            comp1, comp2 = swap_components
            # Map components to give/want based on type
            if comp1['type'] == 'send' and comp2['type'] == 'receive':
                 details = SwapDetails(
                    address=wallet_address,
                    give_token=comp1['token'], give_amount=comp1['amount'],
                    want_token=comp2['token'], want_amount=comp2['amount']
                 )
                 return details
            elif comp1['type'] == 'receive' and comp2['type'] == 'send':
                 details = SwapDetails(
                    address=wallet_address,
                    give_token=comp2['token'], give_amount=comp2['amount'],
                    want_token=comp1['token'], want_amount=comp1['amount']
                 )
                 return details

        return None # Pattern not found or invalid components

    except Exception as e:
        # Log unexpected errors during parsing
        print(f"WARN: Error extracting swap details for {wallet_address[:10]}...: {e}")
        return None

async def find_matching_swaps_from_blockchain(client: Client) -> List[Tuple[SwapDetails, SwapDetails]]:
    """Find matching swap pairs by analyzing all intents on the blockchain"""
    print("\n=== Finding matching swap pairs from blockchain intents... ===")

    all_intents = await client.get_all_intents()
    print(f"Found {len(all_intents)} total intents on the blockchain.")

    swaps: List[SwapDetails] = []
    print("--- Extracting Swap Details from Intents ---")
    for address, intent_data in all_intents.items():
        print(f"Parsing intent for address: {address[:10]}..." , end=" ")
        swap_details = extract_swap_details(intent_data, address)
        if swap_details:
            swaps.append(swap_details)
            print(f" -> Found swap: {swap_details['give_amount']} {swap_details['give_token']} for {swap_details['want_amount']} {swap_details['want_token']}")
        else:
            print(" -> Not a recognized swap intent.")

    print(f"\nExtracted {len(swaps)} valid swap intents.")

    matching_pairs: List[Tuple[SwapDetails, SwapDetails]] = []
    matched_indices = set()

    print("--- Searching for Matching Pairs ---")
    for i, swap1 in enumerate(swaps):
        if i in matched_indices:
            continue
        for j, swap2 in enumerate(swaps):
            if i == j or j in matched_indices:
                continue

            # Exact match condition
            if (swap1["give_token"] == swap2["want_token"] and
                swap1["want_token"] == swap2["give_token"] and
                swap1["give_amount"] == swap2["want_amount"] and
                swap1["want_amount"] == swap2["give_amount"]):

                matching_pairs.append((swap1, swap2))
                matched_indices.add(i)
                matched_indices.add(j)

                # Use addresses directly
                addr1 = swap1['address']
                addr2 = swap2['address']

                print(f"  -> Found matching pair:")
                print(f"     - {addr1} ({swap1['give_amount']} {swap1['give_token']} -> {swap1['want_amount']} {swap1['want_token']})")
                print(f"     - {addr2} ({swap2['give_amount']} {swap2['give_token']} -> {swap2['want_amount']} {swap2['want_token']})")
                break # Move to next swap1 once match is found

    print(f"\nFound {len(matching_pairs)} matching pair(s).")
    return matching_pairs

# Helper function to print balances nicely
def print_balances(wallet_info: Dict[str, Any], address_label: str):
    balances_list = wallet_info.get('balances', []) # Expect a list
    if not balances_list:
        print(f"    {address_label} Balances: (No balances found)")
        return

    # Handle potential list-of-lists or list-of-dicts format
    balance_parts = []
    for item in balances_list:
        if isinstance(item, list) and len(item) == 2:
            token, amount = item
            balance_parts.append(f"{amount} {token}")
        elif isinstance(item, dict) and 'token' in item and 'amount' in item:
            balance_parts.append(f"{item['amount']} {item['token']}")
        # Add more checks here if other formats are possible

    if not balance_parts:
         print(f"    {address_label} Balances: (Could not parse balance format)")
    else:
        balance_str = ", ".join(balance_parts)
        print(f"    {address_label} Balances: {balance_str}")

async def fulfill_swap_pair(client: Client, swap_pair: Tuple[SwapDetails, SwapDetails], matcher_account: Account):
    """Fulfill a matching swap pair using the matcher account, printing balances before and after"""
    swap1, swap2 = swap_pair

    # Use truncated addresses for labels
    addr1_short = swap1['address'][:10] + "..."
    addr2_short = swap2['address'][:10] + "..."

    print(f"\n=== Fulfilling swap between {addr1_short} and {addr2_short} ===")

    # --- Get balances BEFORE swap ---
    print("--- Balances Before Swap ---")
    try:
        info1_before = await client.get_wallet_info_async(swap1['address'])
        info2_before = await client.get_wallet_info_async(swap2['address'])
        print_balances(info1_before, f"{addr1_short} ({swap1['give_token']}->{swap1['want_token']})")
        print_balances(info2_before, f"{addr2_short} ({swap2['give_token']}->{swap2['want_token']})")
    except Exception as e:
        print(f"WARN: Failed to get pre-swap balances: {e}")

    # --- Prepare and Submit Swap Transaction ---
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

    print(f"Using dedicated matcher account ({matcher_account.public_key[:10]}...) to sign and submit swap transaction...")
    signed_tx = prepareSimpleTx(matcher_account, tx)

    tx_successful = False
    tx_hash = None
    error_msg = None
    try:
        print("Submitting transaction to the network...")
        result = await client.tx_commit(signed_tx)
        if result.get("error") is None:
            tx_successful = True
            tx_hash = result.get('hash')
            print("✓ Swap transaction submitted successfully!")
            print(f"  - Tx Hash: {tx_hash}")
        else:
            error_msg = result.get("error")
            print(f"✗ Swap transaction failed on submission: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Exception during swap submission: {e}")

    # --- Get balances AFTER swap attempt ---
    print("--- Balances After Swap Attempt ---")
    try:
        # Increase delay significantly to allow node state to potentially update
        print("Waiting longer for node state update...")
        await asyncio.sleep(2)
        print(swap1['address'])
        info1_after = await client.get_wallet_info_async(swap1['address'])
        info2_after = await client.get_wallet_info_async(swap2['address'])
        print_balances(info1_after, f"{addr1_short}")
        print_balances(info2_after, f"{addr2_short}")
    except Exception as e:
        print(f"WARN: Failed to get post-swap balances: {e}")

    # Final outcome summary
    if tx_successful:
         print(f"\nTx: {tx_hash}")
    else:
         print(f"\nOutcome: Swap failed ({error_msg}")

async def main():
    print("=== Saline SDK Simple Swap Matcher Example ===\n")
    client = Client(http_url=RPC_URL)

    # Creates a new account with a random mnemonic
    root = Account.create()

    # TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    # root = Account.from_mnemonic(TEST_MNEMONIC)

    matcher = root.create_subaccount(label="matcher")
    print(f"Created dedicated matcher account: {matcher.public_key[:10]}...")

    # Create accounts and intents, but we don't need to store the mapping
    await create_accounts_with_swap_intents(client, root)

    wait_time = 10 # seconds
    print(f"\nWaiting {wait_time} seconds for intents to process...")
    await asyncio.sleep(wait_time)

    # Find matches without needing the accounts map
    matching_pairs = await find_matching_swaps_from_blockchain(client)

    if matching_pairs:
        # Fulfill the first matching pair found
        await fulfill_swap_pair(client, matching_pairs[0], matcher)
    else:
        print("\nNo matching swap pairs found to fulfill.")

if __name__ == "__main__":
    asyncio.run(main())
