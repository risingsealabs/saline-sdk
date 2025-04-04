"""
Simple Faucet Example for Saline Protocol

Supports both the simple scenario of a fixed amount of tokens, and the more complex scenario of a dynamic amount of tokens based on the intent.
"""

import asyncio
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, TransferFunds
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client

# Faucet address is known and stable
FAUCET_ADDRESS = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b65613d43c496a4e704b71cd5"
TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "http://localhost:26657"

async def get_tokens_from_faucet(client, account):
    """Request tokens from the faucet using hardcoded amounts"""
    
    # Create a transfer instruction for standard faucet amounts
    instruction = TransferFunds(
        source=FAUCET_ADDRESS,  # Faucet address
        target=account.public_key,  # Recipient
        funds={
            "BTC": 1,
            "ETH": 10, 
            "USDC": 1000,
            "USDT": 1000,
            "SALT": 1000
        }
    )
    
    # Create transaction with the instruction
    tx = Transaction(instructions=NonEmpty.from_list([instruction]))
    signed_tx = prepareSimpleTx(account, tx)
    
    result = await client.tx_commit(signed_tx)

    if result.get("error") is None:
        print(f"Success! Tokens received.")
    else:
        print(f"Error: {result.get('error')}")

async def get_tokens_from_faucet_dynamic(client, account, faucet_intent):
    """Request tokens from the faucet with amounts derived from the faucet intent"""

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
        print("Error: Could not extract token amounts from faucet intent.")
        return
    
    print(f"Requesting tokens: {funds}")
    
    # Create a transfer instruction with the extracted amounts
    instruction = TransferFunds(
        source=FAUCET_ADDRESS,
        target=account.public_key,
        funds=funds
    )
    
    tx = Transaction(instructions=NonEmpty.from_list([instruction]))
    signed_tx = prepareSimpleTx(account, tx)

    result = await client.tx_commit(signed_tx)
    
    if result.get("error") is None:
        print(f"Success! Tokens received.")
    else:
        print(f"Error: {result.get('error')}")

async def main():
    client = Client(http_url=RPC_URL)

    account = Account.from_mnemonic(TEST_MNEMONIC)
    alice = account.create_subaccount(label="alice")
    
    # Verify faucet exists
    faucet = await client.get_intent_async(FAUCET_ADDRESS)
    if not faucet:
        print(f"Error: Faucet not found at {FAUCET_ADDRESS}")
        return
        
    print(f"Found faucet at {FAUCET_ADDRESS}")
    
    # Check initial balance
    initial = await client.get_wallet_info_async(alice.public_key)
    print(f"Initial balance: {initial.get('balances', [])}")
    
    # Choose approach: set to True for dynamic, False for hardcoded
    use_dynamic_approach = True
    
    if use_dynamic_approach:
        await get_tokens_from_faucet_dynamic(client, alice, faucet)
    else:
        await get_tokens_from_faucet(client, alice)
    
    # Check new balance
    updated = await client.get_wallet_info_async(alice.public_key)
    print(f"New balance: {updated.get('balances', [])}")

if __name__ == "__main__":
    asyncio.run(main())
