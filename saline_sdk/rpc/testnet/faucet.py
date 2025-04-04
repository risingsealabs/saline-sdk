"""
Testnet faucet utilities.

This module provides utilities for interacting with the Saline testnet faucet
to obtain test tokens.
"""

import logging
import asyncio
from typing import Dict, Optional, Union, Any

from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, TransferFunds
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client

# Default faucet address for the testnet - this is known and stable
FAUCET_ADDRESS = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b65613d43c496a4e704b71cd5"

# Standard token list
DEFAULT_TOKENS = {
    "BTC": 1,
    "ETH": 10,
    "USDC": 1000,
    "USDT": 1000,
    "SALT": 1000
}

logger = logging.getLogger(__name__)

async def top_up_from_faucet(
    account: Any,
    client: Optional[Client] = None,
    tokens: Optional[Dict[str, Union[int, float]]] = None,
    rpc_url: str = "http://localhost:26657",
    use_dynamic_amounts: bool = True
) -> Dict[str, float]:
    """
    Request tokens from the testnet faucet for the given account.
    
    Args:
        account: The Account or Subaccount to receive tokens
        client: Optional Client instance (created if not provided)
        tokens: Optional dictionary of token amounts to request (uses faucet defaults if not provided)
        rpc_url: RPC URL for the testnet (used only if client is not provided)
        use_dynamic_amounts: Whether to use the amounts defined in the faucet intent (True) or use hardcoded amounts (False)
        
    Returns:
        Dictionary of the new balances after the faucet transfer
        
    Raises:
        RuntimeError: If the faucet transfer fails
    """
    # Use provided client or create a new one
    if client is None:
        client = Client(http_url=rpc_url)
    
    # Determine the account to use - handle both Account and Subaccount objects
    if hasattr(account, "__len__") and callable(getattr(account, "__len__")):  # It's an Account with subaccounts
        # Use primary account or first subaccount
        if len(account) == 0:
            # Create a subaccount if there are none
            default_account = account.create_subaccount(label="default")
        else:
            # Use default subaccount
            default_account = account[account.default_subaccount] if account.default_subaccount else account[list(account)[0]]
    else:  # It's likely a Subaccount
        # Use it directly if it has a public_key attribute
        if hasattr(account, "public_key"):
            default_account = account
        else:
            raise ValueError("Account must be either an Account with subaccounts or a Subaccount")
    
    # Get account public key
    account_address = default_account.public_key
    
    # Get initial balance for comparison
    initial_wallet_info = await client.get_wallet_info_async(account_address)
    initial_balances = initial_wallet_info.get('balances', [])
    logger.debug(f"Initial balances: {initial_balances}")
    
    # First, verify that the faucet exists
    faucet_intent = await client.get_intent_async(FAUCET_ADDRESS)
    if not faucet_intent:
        raise RuntimeError(f"Faucet not found at {FAUCET_ADDRESS}")
    
    if use_dynamic_amounts:
        # Parse the faucet intent to determine how much we can request
        funds = {}
        
        # The faucet intent has a structure with children (restrictions) for each token
        if "children" in faucet_intent:
            for restriction in faucet_intent["children"]:
                if (restriction.get("tag") == "Restriction" and
                    restriction.get("lhs", {}).get("tag") == "Send" and
                    restriction.get("relation") == "EQ"):
                    
                    # Extract the token and amount
                    token = restriction.get("lhs", {}).get("flow", {}).get("token")
                    amount = restriction.get("rhs", {}).get("value")
                    
                    if token and amount is not None:
                        # Convert float amounts to integers
                        if isinstance(amount, float):
                            amount = int(amount)
                        funds[token] = amount
        
        if not funds:
            raise RuntimeError("Could not extract token amounts from faucet intent")
    else:
        # Use provided tokens or default tokens
        funds = tokens or DEFAULT_TOKENS
    
    logger.debug(f"Requesting tokens: {funds}")
    
    # Create a transfer instruction
    instruction = TransferFunds(
        source=FAUCET_ADDRESS,
        target=account_address,
        funds=funds
    )
    
    # Create and sign transaction
    tx = Transaction(instructions=NonEmpty.from_list([instruction]))
    signed_tx = prepareSimpleTx(default_account, tx)
    
    # Submit transaction
    result = await client.tx_commit(signed_tx)
    
    if result.get("error") is not None:
        raise RuntimeError(f"Faucet request failed: {result.get('error')}")
    
    # Wait a brief moment to allow the blockchain to update
    await asyncio.sleep(1)
    
    # Get updated balances
    updated_wallet_info = await client.get_wallet_info_async(account_address)
    updated_balances = updated_wallet_info.get('balances', [])
    logger.debug(f"Updated balances: {updated_balances}")
    
    # Convert the balances list to a dictionary for easier use
    balance_dict = {}
    for balance_item in updated_balances:
        if isinstance(balance_item, list) and len(balance_item) >= 2:
            token, amount = balance_item[0], balance_item[1]
            balance_dict[token] = amount
        elif isinstance(balance_item, dict):
            token = balance_item.get('token')
            amount = balance_item.get('amount')
            if token and amount is not None:
                balance_dict[token] = amount
    
    return balance_dict 