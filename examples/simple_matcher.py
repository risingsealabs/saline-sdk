"""
Simple Swap Matcher Example for Saline Protocol

Demonstrates how to:
1. Create multiple accounts with different swap intents
2. Find matching swap pairs on-chain by analyzing all intents
3. Fulfill the first matching swap found.
"""

import asyncio
from typing import Dict, List, Tuple, Optional, Any, TypedDict

from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, TransferFunds, Signed,
    Send, Receive, Flow, Token, Restriction, Relation, All, Any, Lit, Expr
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client
from saline_sdk.rpc.testnet.faucet import top_up

# Configuration
RPC_URL = "https://node0.try-saline.com"
INTENT_PROCESSING_WAIT_SECONDS = 5
POST_SWAP_WAIT_SECONDS = 3

# --- Swap typehint ---
class SwapDetails(TypedDict):
    address: str
    give_token: str
    give_amount: int
    want_token: str
    want_amount: int

# --- Example Swap Configurations ---
SWAP_CONFIGS = [
    # Matching pair
    {"name": "alice", "give_token": "USDC", "give_amount": 100, "want_token": "BTC", "want_amount": 1},
    {"name": "bob", "give_token": "BTC", "give_amount": 1, "want_token": "USDC", "want_amount": 100},
    # Non-matching intents
    {"name": "carol", "give_token": "ETH", "give_amount": 10, "want_token": "USDT", "want_amount": 10000},
    {"name": "dave", "give_token": "USDT", "give_amount": 20000, "want_token": "ETH", "want_amount": 10},
]

async def create_accounts_with_swap_intents(client: Client, root_account: Account) -> Dict[str, Account]:
    """Creates subaccounts, funds them via faucet, and sets swap intents."""
    print(f"Creating {len(SWAP_CONFIGS)} accounts and setting swap intents...")
    accounts = {}
    tasks = []

    for config in SWAP_CONFIGS:
        name = config["name"]
        account = root_account.create_subaccount(label=name)
        accounts[name] = account

        # Request faucet top-up (non-blocking)
        tasks.append(top_up(account=account, client=client, use_dynamic_amounts=False))

        # Define swap intent
        send_restriction = Restriction(
            Send(Flow(None, Token[config["give_token"]])), Relation.EQ, Lit(config["give_amount"])
        )
        receive_restriction = Restriction(
            Receive(Flow(None, Token[config["want_token"]])), Relation.EQ, Lit(config["want_amount"])
        )
        swap_intent = All([send_restriction, receive_restriction])

        # Prepare and submit SetIntent transaction (non-blocking)
        set_intent_instruction = SetIntent(account.public_key, swap_intent)
        tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))
        signed_tx = prepareSimpleTx(account, tx)
        tasks.append(client.tx_commit(signed_tx))

    # Wait for all faucet and intent transactions to complete
    results = await asyncio.gather(*tasks, return_exceptions=True)

    success_count = sum(1 for r in results if isinstance(r, dict) and r.get("error") is None)
    fail_count = len(tasks) - success_count
    print(f"Intent/Faucet submissions complete: {success_count} succeeded, {fail_count} failed/exceptions.")


    return accounts

def _extract_restriction_details(restriction_node: Dict[str, Any]) -> Optional[Dict]:
    """Helper to extract token/amount from Send/Receive Restriction nodes."""
    if not isinstance(restriction_node, dict) or restriction_node.get('tag') != 'Restriction': return None
    lhs = restriction_node.get('lhs', {}); rhs = restriction_node.get('rhs', {})
    if restriction_node.get('relation') != Relation.EQ.name: return None
    if not isinstance(rhs, dict) or rhs.get('tag') != 'Lit': return None
    amount = rhs.get('value'); token_str = lhs.get('flow', {}).get('token')
    if amount is None or not token_str: return None

    tag_type = lhs.get('tag')
    details = {'token': token_str, 'amount': int(amount)}
    if tag_type == 'Send': return {'type': 'send', **details}
    if tag_type == 'Receive': return {'type': 'receive', **details}
    return None

def _find_swap_in_intent_node(intent_node: Dict[str, Any]) -> Optional[Tuple[Dict, Dict]]:
    """Recursively searches intent structure for a Send/Receive pair under an 'All' node."""
    if not isinstance(intent_node, dict): return None
    tag = intent_node.get('tag')

    if tag == 'All':
        children = intent_node.get('children', [])
        send_details, receive_details = None, None
        for child in children:
            details = _extract_restriction_details(child)
            if details:
                if details['type'] == 'send': send_details = details
                elif details['type'] == 'receive': receive_details = details
            if send_details and receive_details: return send_details, receive_details
        # Recurse if not found directly under this 'All'
        for child in children:
             if isinstance(child, dict) and child.get('tag') in ['All', 'Any']:
                 if nested := _find_swap_in_intent_node(child): return nested
    elif tag == 'Any': # Also check branches under 'Any'
        for child in intent_node.get('children', []):
            if isinstance(child, dict) and child.get('tag') in ['All', 'Any']:
                 if nested := _find_swap_in_intent_node(child): return nested
    return None

def extract_swap_details(intent_data: Dict[str, Any], intent_key: str) -> Optional[SwapDetails]:
    """Extracts swap details and signer address from intent data."""
    if not intent_data: return None

    # Extract signer address (robustly check structure)
    actual_address: Optional[str] = None
    try:
        addr_list = intent_data.get('addresses')
        if isinstance(addr_list, list) and addr_list and isinstance(addr_list[0], list) and addr_list[0]:
            if isinstance(addr := addr_list[0][0], str):
                actual_address = addr
    except Exception:
        pass

    if not actual_address:
        return None

    # Extract raw intent structure
    raw_intent_list = intent_data.get('raw_intent')
    if not isinstance(raw_intent_list, list) or not raw_intent_list:
        return None
    intent_structure = raw_intent_list[0]


    try:
        swap_components = _find_swap_in_intent_node(intent_structure)
        if not swap_components: return None

        comp1, comp2 = swap_components
        if comp1['type'] == 'send' and comp2['type'] == 'receive':
            return SwapDetails(address=actual_address, give_token=comp1['token'], give_amount=comp1['amount'], want_token=comp2['token'], want_amount=comp2['amount'])
        elif comp1['type'] == 'receive' and comp2['type'] == 'send':
            return SwapDetails(address=actual_address, give_token=comp2['token'], give_amount=comp2['amount'], want_token=comp1['token'], want_amount=comp1['amount'])
        else:
            return None

    except Exception as e:

        return None

async def find_matching_swaps_from_blockchain(client: Client) -> List[Tuple[SwapDetails, SwapDetails]]:
    """Queries all intents, extracts swap details, and finds matching pairs."""
    print("Querying blockchain for all intents...")
    all_intents = await client.get_all_intents()
    if not all_intents:
        print("WARN: No intents found or failed to retrieve intents.")
        return []
    print(f"Retrieved {len(all_intents)} intent entries. Analyzing for swaps...")

    # Extract valid swaps
    swaps: List[SwapDetails] = []
    for intent_key, intent_data in all_intents.items():
        if swap_details := extract_swap_details(intent_data, intent_key):
            swaps.append(swap_details)
    print(f"Found {len(swaps)} potential swap intents.")

    # Find matching pairs (simple exact match)
    matching_pairs: List[Tuple[SwapDetails, SwapDetails]] = []
    matched_indices = set()
    for i, swap1 in enumerate(swaps):
        if i in matched_indices: continue
        for j, swap2 in enumerate(swaps):
            if i == j or j in matched_indices: continue

            is_match = (
                swap1["give_token"] == swap2["want_token"] and
                swap1["want_token"] == swap2["give_token"] and
                swap1["give_amount"] == swap2["want_amount"] and
                swap1["want_amount"] == swap2["give_amount"]
            )
            if is_match:
                matching_pairs.append((swap1, swap2))
                matched_indices.update([i, j])
                print(f"  -> Found matching pair: {swap1['address'][:6]}... <=> {swap2['address'][:6]}...")
                break # Found match for swap1, move to next i

    print(f"Found {len(matching_pairs)} matching swap pair(s).")
    return matching_pairs

def print_balances(wallet_info: Optional[Dict[str, Any]], address_label: str):
    if not wallet_info or 'balances' not in wallet_info:
        print(f"    {address_label} Balances: Unavailable or no balances")
        return

    balances_list = wallet_info['balances']
    if not balances_list:
        print(f"    {address_label} Balances: Empty")
        return

    balance_parts = []
    for item in balances_list:
        try:
            if isinstance(item, list) and len(item) == 2:
                balance_parts.append(f"{item[1]} {item[0]}")
            elif isinstance(item, dict) and 'token' in item and 'amount' in item:
                balance_parts.append(f"{item['amount']} {item['token']}")
        except (IndexError, KeyError, TypeError):
            pass

    if not balance_parts:
         print(f"    {address_label} Balances: (Could not parse format: {balances_list})")
    else:
        print(f"    {address_label} Balances: {', '.join(balance_parts)}")

async def fulfill_swap_pair(client: Client, swap_pair: Tuple[SwapDetails, SwapDetails], matcher_account: Account):
    """Fulfills a swap using TransferFunds and prints balances before/after."""
    swap1, swap2 = swap_pair
    addr1, addr2 = swap1['address'], swap2['address']
    addr1_short, addr2_short = f"{addr1[:6]}...", f"{addr2[:6]}..."

    print(f"\nAttempting to fulfill swap between {addr1_short} and {addr2_short}...")

    # Get balances BEFORE
    print("--- Balances Before Swap ---")
    info1_before = await client.get_wallet_info_async(addr1)
    info2_before = await client.get_wallet_info_async(addr2)
    print_balances(info1_before, f"{addr1_short}")
    print_balances(info2_before, f"{addr2_short}")

    # Prepare Swap Transaction
    instruction1 = TransferFunds(source=addr1, target=addr2, funds={swap1["give_token"]: swap1["give_amount"]})
    instruction2 = TransferFunds(source=addr2, target=addr1, funds={swap2["give_token"]: swap2["give_amount"]})
    tx = Transaction(instructions=NonEmpty.from_list([instruction1, instruction2]))
    signed_tx = prepareSimpleTx(matcher_account, tx)

    # Submit Swap Transaction
    print(f"Submitting swap transaction signed by matcher {matcher_account.public_key[:6]}...")
    tx_successful = False
    tx_hash, error_msg = None, None
    try:
        result = await client.tx_commit(signed_tx)
        if result and result.get("error") is None:
            tx_successful = True
            tx_hash = result.get('hash')
            print(f"  ✓ Transaction submitted successfully. Hash: {tx_hash}")
        else:
            error_msg = result.get("error") if result else "Empty result from tx_commit"
            print(f"  ✗ Transaction failed on submission: {error_msg}")
    except Exception as e:
        error_msg = str(e)
        print(f"  ✗ Exception during submission: {e}")

    # Get balances AFTER (with a short delay)
    print(f"Waiting {POST_SWAP_WAIT_SECONDS}s for balance updates...")
    await asyncio.sleep(POST_SWAP_WAIT_SECONDS)
    print("--- Balances After Swap Attempt ---")
    try:
        info1_after = await client.get_wallet_info_async(addr1)
        info2_after = await client.get_wallet_info_async(addr2)
        print_balances(info1_after, f"{addr1_short}")
        print_balances(info2_after, f"{addr2_short}")
    except Exception as e:
        print(f"WARN: Failed to get post-swap balances: {e}")

    # Final outcome summary
    if tx_successful:
         print(f"Swap between {addr1_short} and {addr2_short} potentially completed (Tx: {tx_hash}). Verify balances.")
    else:
         print(f"Swap between {addr1_short} and {addr2_short} failed: {error_msg}")

async def main():
    print("=== Saline SDK Simple Swap Matcher Example ===")
    client = Client(http_url=RPC_URL)

    try:
        status = client.get_status()
        print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
    except Exception as e:
        print(f"ERROR: Could not connect to RPC @ {RPC_URL}. Is node running? ({e})")
        return

    # Create a new account
    root = Account.create()
    print("account mnemonic:", root._mnemonic)
    matcher = root.create_subaccount(label="matcher")
    print(f"matcher public key: {matcher.public_key[:10]}...")

    # 1. Create accounts and set intents
    # We don't need the returned accounts dict for matching
    await create_accounts_with_swap_intents(client, root)

    # Allow time for intents to be processed by the network
    print(f"Waiting {INTENT_PROCESSING_WAIT_SECONDS}s for intents to propagate...")
    await asyncio.sleep(INTENT_PROCESSING_WAIT_SECONDS)

    # 2. Find matches by querying blockchain state
    matching_pairs = await find_matching_swaps_from_blockchain(client)

    # 3. Fulfill the first match found
    if matching_pairs:
        await fulfill_swap_pair(client, matching_pairs[0], matcher)
    else:
        print("\nNo matching swap pairs found.")

if __name__ == "__main__":
    # Setup asyncio event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution cancelled by user.")
