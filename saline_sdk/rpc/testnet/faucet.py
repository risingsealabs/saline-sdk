"""
Testnet faucet utilities.

This module provides utilities for interacting with the Saline testnet faucet
to obtain test tokens.
"""

import logging
import asyncio
from typing import Dict, Optional, Any, List

from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, TransferFunds,
    Restriction, Send, Receive, Lit, Relation
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client
from saline_sdk.rpc.error import RPCError
from saline_sdk.rpc.query_responses import ParsedWalletInfo

# Default faucet address for the testnet - this is known and stable
FAUCET_ADDRESS = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b65613d43c496a4e704b71cd5"

DEFAULT_TOKEN_AMOUNTS = {
    "BTC": 1,
    "ETH": 10,
    "USDC": 1000,
    "USDT": 1000,
    "SALT": 1000
}

logger = logging.getLogger(__name__)

async def top_up(
    account: Any,
    client: Client,
    use_dynamic_amounts: bool = True,
    wait_seconds: int = 3
) -> Dict[str, int]:
    """
    Requests tokens from the testnet faucet for the given account. Waits briefly, then returns the updated balances.

    This function fetches the faucet's intent to determine dynamic token amounts
    (if requested) and then creates/submits a transaction signed by the *target account*
    to trigger the faucet transfer. After submission, it waits for `wait_seconds`
    and queries the account's new balances.

    Args:
        account: The Account or Subaccount object that will receive tokens and sign the request.
        client: An initialized Client instance.
        use_dynamic_amounts: Whether to use the amounts defined in the faucet intent (True) or use hardcoded amounts (False).
        wait_seconds: Seconds to wait after submitting the transaction before querying balances.

    Returns:
        A dictionary representing the account's balances (token -> amount) after the faucet request.
        Returns an empty dictionary if balance retrieval fails.

    Raises:
        RPCError: If querying the faucet, parsing its intent (for dynamic amounts),
                  or submitting the transaction fails.
        ValueError: If the input account object is invalid.
        KeyError: If an invalid token name is used (relevant for dynamic amounts).
    """
    if not hasattr(account, "public_key") or not account.public_key:
         raise ValueError("Input 'account' must have a valid 'public_key' attribute.")
    account_address = account.public_key

    # Fetch faucet wallet info - raises exceptions on network/RPC errors
    try:
        faucet_wallet_info: ParsedWalletInfo = await client.get_wallet_info_async(FAUCET_ADDRESS)
    except Exception as e:
         logger.error(f"Failed to query faucet wallet info at {FAUCET_ADDRESS}: {e}", exc_info=True)
         raise RPCError(f"Failed to query faucet wallet info at {FAUCET_ADDRESS}: {e}")

    # Check if the query result itself contains an error (e.g., parsing error within get_wallet_info)
    if faucet_wallet_info.error:
         logger.error(f"Faucet wallet info query at {FAUCET_ADDRESS} returned an error: {faucet_wallet_info.error}. Raw data: {faucet_wallet_info.raw_wallet_data}")
         raise RPCError(f"Faucet wallet info query returned error: {faucet_wallet_info.error}")
    if not faucet_wallet_info.parsed_intent and use_dynamic_amounts:
        # Only raise if we need the parsed intent for dynamic amounts
         logger.error(f"Faucet wallet info at {FAUCET_ADDRESS} missing parsed intent needed for dynamic amounts. Raw data: {faucet_wallet_info.raw_wallet_data}")
         raise RPCError("Faucet intent missing or could not be parsed, required for dynamic amounts.")

    faucet_intent = faucet_wallet_info.parsed_intent

    if use_dynamic_amounts:
        if not faucet_intent:
             # This case should theoretically be caught above
             raise RPCError("Assertion failed: Faucet intent is None but needed for dynamic amounts.")

        # Parse the faucet intent to determine how much we can request
        funds = {}
        # Safely check for children attribute and iterate
        if hasattr(faucet_intent, 'children') and faucet_intent.children:
            children: List[Any] = faucet_intent.children
            for restriction in children:
                if isinstance(restriction, Restriction):
                    details = _extract_restriction_details(restriction)
                    if details and details['type'] == 'send':
                        token = details['token']
                        amount = details['amount']
                        # Convert float amounts to integers if necessary (should already be int from _extract)
                        if isinstance(amount, float):
                            amount = int(amount)
                        funds[token] = amount
        else:
             logger.error(f"Parsed faucet intent at {FAUCET_ADDRESS} lacks 'children' or has empty children. Intent: {faucet_intent}")
             raise RPCError(f"Faucet intent at {FAUCET_ADDRESS} has no children structure to determine dynamic amounts.")

        if not funds:
            logger.error(f"Could not extract any send amounts from faucet intent children: {faucet_intent.children}")
            raise RPCError("Could not extract token amounts from faucet intent")
    else:
        funds = DEFAULT_TOKEN_AMOUNTS

    # Create a transfer instruction
    instruction = TransferFunds(
        source=FAUCET_ADDRESS,
        target=account_address,
        funds=funds
    )


    tx = Transaction(instructions=NonEmpty.from_list([instruction]))
    signed_tx = prepareSimpleTx(account, tx)


    try:
        result = await client.tx_commit(signed_tx)
    except Exception as e:
        logger.error(f"Exception during faucet tx_commit: {e}", exc_info=True)
        raise RPCError(f"Faucet request failed during submission: {e}")

    if result.get("error") is not None:
        err_msg = result.get('error')
        logger.error(f"Faucet tx_commit returned error: {err_msg}")


    tx_hash = result.get('hash')


    await asyncio.sleep(wait_seconds)


    try:
        updated_wallet_info = await client.get_wallet_info_async(account_address)
        if updated_wallet_info.error:
            logger.warning(f"Error retrieving wallet info after faucet call for {account_address[:10]}: {updated_wallet_info.error}")
            return {}

        balances = updated_wallet_info.balances
        return balances

    except Exception as e:
        logger.error(f"Failed to get updated balances for {account_address[:10]} after faucet call: {e}", exc_info=True)
        return {}

def _extract_restriction_details(restriction_node: Restriction) -> Optional[Dict]:
    """Helper to extract token/amount from Send/Receive Restriction nodes using bindings."""
    if restriction_node.relation != Relation.EQ:
        return None
    if not isinstance(restriction_node.rhs, Lit):
        return None
    if not isinstance(restriction_node.lhs, (Send, Receive)):
        return None

    amount = restriction_node.rhs.value
    token = restriction_node.lhs.token

    try:
        details = {'token': token.name, 'amount': int(amount)}
        if isinstance(restriction_node.lhs, Send):
            return {'type': 'send', **details}
        else:
            return None
    except (TypeError, ValueError):
        return None
