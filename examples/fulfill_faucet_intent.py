"""
Intent Fulfillment Example for Saline Protocol

Demonstrates how to fulfill a faucet intent using the Saline SDK.

Supports:
- Simple scenario of a fixed amount of tokens

For a more advanced approach dynamically deriving the faucet bounds, see saline-sdk/rpc/testnet/faucet.py
"""

import asyncio
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, TransferFunds, Intent
)
from saline_sdk.transaction.tx import prepareSimpleTx, tx_is_accepted, print_tx_errors
from saline_sdk.rpc.client import Client

# Faucet address is known and stable
FAUCET_ADDRESS = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b65613d43c496a4e704b71cd5"
TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "https://node0.try-saline.com"

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

    if tx_is_accepted(result):
        print(f"Success! Tokens received.")
    else:
        print("Error occurred during transaction:")
        print_tx_errors(result)

async def main():
    client = Client(http_url=RPC_URL)

    account = Account.from_mnemonic(TEST_MNEMONIC)
    alice = account.create_subaccount(label="alice")

    # Verify faucet exists
    faucet = await client.get_wallet_info_async(FAUCET_ADDRESS)
    if faucet:
        print(Intent.to_json(faucet.parsed_intent))
    if not faucet:
        print(f"Error: Faucet not found at {FAUCET_ADDRESS}")
        return

    print(f"Found faucet at {FAUCET_ADDRESS}")

    # Check initial balance
    initial = await client.get_wallet_info_async(alice.public_key)
    print(f"Initial balance: {initial.balances}")

    await get_tokens_from_faucet(client, alice)

    # Check new balance
    updated = await client.get_wallet_info_async(alice.public_key)
    print(f"New balance: {updated.balances}")

if __name__ == "__main__":
    asyncio.run(main())
