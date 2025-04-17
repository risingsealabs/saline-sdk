"""
Simple Swap Intent Example for Saline Protocol

Demonstrates how to create a swap intent using operator syntax.
"""

import asyncio
import json
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent,
    Send, Receive, Token
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client

TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "https://node0.try-saline.com"

async def create_swap_intent():
    root_account = Account.from_mnemonic(TEST_MNEMONIC)
    alice = root_account.create_subaccount(label="alice")
    rpc = Client(http_url=RPC_URL)


    # Define swap parameters
    send_token = "USDT"
    send_amount = 10
    receive_token = "BTC"
    receive_amount = 1


    # Create swap intent using the operator syntax
    intent = Send(Token[send_token]) * send_amount <= Receive(Token[receive_token]) * receive_amount

    # Create the SetIntent instruction and transaction
    set_intent = SetIntent(alice.public_key, intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    encoded_tx = prepareSimpleTx(alice, tx)


    try:
        result = await rpc.tx_broadcast(encoded_tx)
        print(f"\nTransaction result: {json.dumps(result, indent=2)}")

        if result.get('code', 0) == 0:
            print("Swap intent installation successful!")
        else:
            print(f"Transaction failed with code: {result.get('code')}")

        # Display the intent structure
        print("\nSwap intent structure:")
        print(json.dumps(SetIntent.to_json(set_intent), indent=2))

    except Exception as e:
        print(f"Transaction failed: {str(e)}")

async def main():

    await create_swap_intent()

if __name__ == "__main__":
    asyncio.run(main())
