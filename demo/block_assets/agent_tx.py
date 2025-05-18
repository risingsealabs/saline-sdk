# Block assets
# This is the code to create agent to submit transaction to user asset address

import asyncio
import json
from saline_sdk.account import Account
from typing import Dict, List, Tuple, Optional, Any, TypedDict
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import Counterparty, Lit, NonEmpty, Receive, SetIntent, Token, Transaction
from saline_sdk.transaction.bindings import NonEmpty, Transaction
from saline_sdk.transaction.instructions import transfer
from saline_sdk.transaction.tx import prepareSimpleTx, print_tx_errors

RPC_URL = "https://node1.try-saline.com"
TEST_MNEMONIC = "exhaust wave soldier analyst angry portion mixed delay true disagree wood smart"

RULE_ADDRESS = "b10bdfc35a171e58911cfb2e672818d163609663a3b324784b6cf5dc90d4b0140c97030a85be3afdb28cc75683e59c35"

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


async def main():
    # Create a temporary root account for this run
    # root_account = Account.create()
    rpc = Client(http_url=RPC_URL)

    root_account = Account.from_mnemonic(TEST_MNEMONIC)
    # print("root account mnemonic:", root_account._mnemonic)

    sender = root_account.create_subaccount(label="Agent_address")
    print("Agent public key:",sender.public_key)

    account_balance1 = await rpc.get_wallet_info_async(sender.public_key)
    print("Agent balance after:",format_balances(account_balance1.balances))

    # Create a transaction from agent to RULE_ADDRESS (with rules)
    funds = transfer(
        sender=RULE_ADDRESS,
        recipient=sender.public_key,
        token="BTC",
        amount=3
    )

    tx = Transaction(funds=funds, burn={}, intents={}, mint={})
    signed_tx = prepareSimpleTx(sender, tx)



    # Sign and submit
    print("Submitting transfer to rule address...")
    try:
        result = await rpc.tx_commit(signed_tx)
        print_tx_errors(result)
        print(json.dumps(result, indent=2))
        account_balance2 = await rpc.get_wallet_info_async(sender.public_key)
        print("Agent balance after:",format_balances(account_balance2.balances))
        return result
    except Exception as e:
        print(f"ERROR: Transaction failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
