"""
Simple Swap Matcher Example for Saline Protocol

Demonstrates how to:
1. Create multiple accounts with different swap intents
2. Find matching swap pairs on-chain by analyzing all intents
3. Fulfill the first matching swap found with sufficient balances.
"""

import asyncio
from typing import Dict, List, Tuple, Optional, Any, TypedDict

from saline_sdk.account import Account
from saline_sdk.transaction.instructions import swap
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent,
    Send, Receive, Token, Restriction, Relation, All, Any, Lit, Intent
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client
from saline_sdk.rpc.query_responses import (
    ParsedIntentInfo
)
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
    """Creates subaccounts, funds them via faucet, and sets swap intents sequentially."""
    print("Creating accounts and setting swap intents sequentially...")
    accounts = {}

    for config in SWAP_CONFIGS:
        account = root_account.create_subaccount(label=config['name'])
        accounts[config["name"]] = account
        pubkey = account.public_key
        print(f"Created account {config['name']} with public key: {pubkey[:10]}...")

        # Fund the account via Faucet
        try:
            await top_up(account, client)
            print(f"  -> Funding requested for {config['name']} ({pubkey[:6]}...).")
        except Exception as e:
            print(f"  -> WARN: Failed to request funding for {config['name']}: {e}")

        # Verify balance
        account_balances = await client.get_wallet_info_async(account.public_key)
        print(f"  {config['name']} Balances: {format_balances(account_balances.balances)}")

        send_restriction = Restriction(
            Send(Token[config["give_token"]]), Relation.EQ, Lit(config["give_amount"])
        )
        receive_restriction = Restriction(
            Receive(Token[config["want_token"]]), Relation.EQ, Lit(config["want_amount"])
        )
        swap_intent = All([send_restriction, receive_restriction])
        intents = {account.public_key: SetIntent(swap_intent)}
        tx = Transaction(funds={}, burn={}, intents=intents, mint={})
        signed_tx = prepareSimpleTx(account, tx)
        try:
            intent_result = await client.tx_commit(signed_tx)
            if intent_result and intent_result.get("error") is None:
                print(f"Swap Intent for {config['name']} submitted successfully. Hash: {intent_result.get('hash')}")
            else:
                error_msg = intent_result.get("error") if intent_result else "Empty result"
                print(f"Swap Intent for {config['name']} failed: {error_msg}")
        except Exception as e:
            print(f"Swap Intent for {config['name']} failed: {e}")
    return accounts

def _extract_restriction_details(restriction_node: Restriction) -> Optional[Dict]:
    """Helper to extract token/amount from Send/Receive Restriction nodes using bindings."""
    if restriction_node.relation != Relation.EQ:
        return None
    if not isinstance(restriction_node.rhs, Lit):
        return None
    if not isinstance(restriction_node.lhs, (Send, Receive)):
        return None

    # Extract details
    amount = restriction_node.rhs.value
    token = restriction_node.lhs.token

    try:
        details = {'token': token.name, 'amount': int(amount)}
        if isinstance(restriction_node.lhs, Send):
            return {'type': 'send', **details}
        else: # Must be Receive
            return {'type': 'receive', **details}
    except (TypeError, ValueError):
        return None

def _find_swap_intent(intent_node: Optional[Intent]) -> Optional[Tuple[Dict, Dict]]:
    """Recursively searches bindings structure for a Send/Receive pair under an 'All' node."""
    if intent_node is None:
        return None

    if isinstance(intent_node, All):
        send_details, receive_details = None, None
        for child in intent_node.children:
            if isinstance(child, Restriction):
                details = _extract_restriction_details(child)
                if details:
                    if details['type'] == 'send':
                        send_details = details
                    elif details['type'] == 'receive':
                        receive_details = details
            if send_details and receive_details:
                return send_details, receive_details

        # If not found directly, recurse into nested All/Any children
        for child in intent_node.children:
            if isinstance(child, (All, Any)):
                if nested_result := _find_swap_intent(child):
                    return nested_result
    elif isinstance(intent_node, Any):
        # Recurse into Any children as well
        for child in intent_node.children:
            if isinstance(child, (All, Any)):
                if nested_result := _find_swap_intent(child):
                    return nested_result

    return None # Not found

def extract_swap_details(intent_info: ParsedIntentInfo) -> Optional[SwapDetails]:
    """Extracts swap details and signer address from ParsedIntentInfo."""
    if not intent_info or not intent_info.parsed_intent or intent_info.error:
        return None

    # Extract address from the associated address list
    actual_address: Optional[str] = None
    try:
        # addresses field structure: [["address_hash", []]]
        addr_list = intent_info.addresses
        if isinstance(addr_list, list) and addr_list and isinstance(addr_list[0], list) and addr_list[0]:
            if isinstance(addr := addr_list[0][0], str):
                actual_address = addr
    except Exception:
        pass

    if not actual_address:
        return None

    try:
        # Search within the parsed bindings.Intent object
        swap_components = _find_swap_intent(intent_info.parsed_intent)
        if not swap_components: return None

        comp1, comp2 = swap_components
        if comp1['type'] == 'send' and comp2['type'] == 'receive':
            return SwapDetails(address=actual_address, give_token=comp1['token'], give_amount=comp1['amount'], want_token=comp2['token'], want_amount=comp2['amount'])
        elif comp1['type'] == 'receive' and comp2['type'] == 'send':
            return SwapDetails(address=actual_address, give_token=comp2['token'], give_amount=comp2['amount'], want_token=comp1['token'], want_amount=comp1['amount'])
        else:
            return None

    except Exception:
        return None

async def find_matching_swaps_from_blockchain(client: Client) -> List[Tuple[SwapDetails, SwapDetails]]:
    """Queries all intents, extracts swap details, and finds matching pairs."""
    print("Querying blockchain for all intents...")
    all_intents_response = await client.get_all_intents()

    if not all_intents_response or not all_intents_response.intents:
        print("WARN: No intents found or failed to retrieve intents.")
        return []

    print(f"Retrieved {len(all_intents_response.intents)} intent entries. Analyzing for swaps...")

    # Filter for potential swap intents and parse them
    swaps: List[SwapDetails] = []

    # Iterate over the ParsedIntentInfo objects in the .intents dictionary
    for intent_info in all_intents_response.intents.values():
        # Pass the ParsedIntentInfo object to the extraction function
        if swap_details := extract_swap_details(intent_info):
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

def format_balances(balances_dict: Optional[Dict[str, Any]]) -> str:
    """Formats a balance dictionary into a readable string."""
    if not balances_dict:
        return "Unavailable or no balances"

    balance_parts = []
    for token, amount in balances_dict.items():
        try:
            balance_parts.append(f"{amount} {token}")
        except Exception:
            balance_parts.append(f"{token}: ErrorFormatting({amount})")

    if not balance_parts:
        return "(Empty)"
    else:
        return ', '.join(balance_parts)

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
    print(f"    {addr1_short}: {format_balances(info1_before.balances)}")
    print(f"    {addr2_short}: {format_balances(info2_before.balances)}")

    # Prepare Swap Transaction
    funds = swap(
        sender = addr1,
        recipient = addr2,
        give_token = swap1["give_token"],
        give_amount = swap1["give_amount"],
        take_token = swap2["give_token"],
        take_amount = swap2["give_amount"]
    )

    tx = Transaction(funds=funds, burn={}, intents={}, mint={})
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
        print(f"    {addr1_short}: {format_balances(info1_after.balances)}")
        print(f"    {addr2_short}: {format_balances(info2_after.balances)}")
    except Exception as e:
        print(f"WARN: Failed to get post-swap balances: {e}")

    # Final outcome summary
    if tx_successful:
         print(f"Swap between {addr1_short} and {addr2_short} completed (Tx: {tx_hash}).")
    else:
         print(f"Swap between {addr1_short} and {addr2_short} failed: {error_msg}")

async def main():
    print("=== Saline SDK Simple Swap Matcher Example ===")
    client = Client(http_url=RPC_URL)

    try:
        status = await client.get_status()
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
    accounts = await create_accounts_with_swap_intents(client, root)

    # Allow time for intents and faucet funding to be processed
    print(f"Waiting {INTENT_PROCESSING_WAIT_SECONDS + 10}s for intents and funding to propagate...")
    await asyncio.sleep(INTENT_PROCESSING_WAIT_SECONDS + 10)

    # 2. Find matches by querying blockchain state
    matching_pairs = await find_matching_swaps_from_blockchain(client)

    # 3. Check balances and fulfill the first valid match found
    fulfilled = False
    if matching_pairs:
        print(f"\nFound {len(matching_pairs)} potential swap pair(s). Checking balances...")
        for i, (swap1, swap2) in enumerate(matching_pairs):
            addr1, addr2 = swap1['address'], swap2['address']
            addr1_short, addr2_short = f"{addr1[:6]}...", f"{addr2[:6]}..."
            print(f"Checking Pair {i+1}: {addr1_short} <-> {addr2_short}")

            try:
                # Check balance for address 1
                info1 = await client.get_wallet_info_async(addr1)
                bal1 = info1.balances.get(swap1['give_token'], 0) if info1 and info1.balances else 0
                has_bal1 = bal1 >= swap1['give_amount']
                print(f"  {addr1_short}: Has {bal1} {swap1['give_token']} (Needs {swap1['give_amount']}) -> {'Sufficient' if has_bal1 else 'Insufficient'}")

                # Check balance for address 2
                info2 = await client.get_wallet_info_async(addr2)
                bal2 = info2.balances.get(swap2['give_token'], 0) if info2 and info2.balances else 0
                has_bal2 = bal2 >= swap2['give_amount']
                print(f"  {addr2_short}: Has {bal2} {swap2['give_token']} (Needs {swap2['give_amount']}) -> {'Sufficient' if has_bal2 else 'Insufficient'}")

                if has_bal1 and has_bal2:
                    print(f"  Balances sufficient for Pair {i+1}. Attempting fulfillment...")
                    await fulfill_swap_pair(client, (swap1, swap2), matcher)
                    fulfilled = True
                    break # Stop after fulfilling the first valid pair
                else:
                    print(f"  Skipping Pair {i+1} due to insufficient balance.")

            except Exception as e:
                print(f"  Error checking balances or fulfilling Pair {i+1}: {e}. Skipping.")
                continue

        if not fulfilled:
            print("\nChecked all potential pairs, none had sufficient balances to fulfill.")
    else:
        print("\nNo matching swap pairs found.")

if __name__ == "__main__":
    # Setup asyncio event loop
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExecution cancelled by user.")
