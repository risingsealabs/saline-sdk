# Whitelist Agents
# This is the code to create agent to submit transaction to user asset address
# There are two agent in the same account, one if the trusted = whitelisted and another is untrusted = address outside whitelist

import asyncio
import json
from typing import Dict, Optional, Any

from saline_sdk.account import Account
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import Transaction, NonEmpty
from saline_sdk.transaction.tx import prepareSimpleTx, print_tx_errors

RPC_URL = "https://node1.try-saline.com"
TEST_MNEMONIC = "exhaust wave soldier analyst angry portion mixed delay true disagree wood smart"
RULE_ADDRESS = "b10bdfc35a171e58911cfb2e672818d163609663a3b324784b6cf5dc90d4b0140c97030a85be3afdb28cc75683e59c35"

def format_balances(balances: Optional[Dict[str, Any]]) -> str:
    if not balances:
        return "Unavailable or no balances"
    return ', '.join(f"{v} {k}" for k, v in balances.items()) or "(Empty)"

async def create_and_submit_tx(rpc: Client, signer: Account, source: str, target: str, amount: Dict[str, int], label: str):
    funds = {source: {target: amount }}
    tx = Transaction(funds=funds, burn={}, intents={}, mint={})
    signed_tx = prepareSimpleTx(signer, tx)

    print(f"Submitting transaction for {label}...")
    try:
        result = await rpc.tx_commit(signed_tx)
        print_tx_errors(result)
        print(f"{label} tx:", json.dumps(result, indent=2))

        updated_balance = await rpc.get_wallet_info_async(target)
        print(f"{label} balance after:", format_balances(updated_balance.balances))
        return result
    except Exception as e:
        print(f"ERROR: Transaction failed for {label}: {e}")

async def main():
    rpc = Client(http_url=RPC_URL)
    root_account = Account.from_mnemonic(TEST_MNEMONIC)

    trusted = root_account.create_subaccount(label="trusted_agent")
    untrusted = root_account.create_subaccount(label="untrusted_agent")

    print("Trusted Agent:", trusted.public_key)
    print("Untrusted Agent:", untrusted.public_key)

    for label, account in [("Trusted Agent", trusted), ("Untrusted Agent", untrusted)]:
        info = await rpc.get_wallet_info_async(account.public_key)
        print(f"{label} balance before:", format_balances(info.balances))

    result1 = await create_and_submit_tx(rpc, trusted, RULE_ADDRESS, trusted.public_key, {"ETH": 3}, "Trusted Agent")
    result2 = await create_and_submit_tx(rpc, untrusted, RULE_ADDRESS, untrusted.public_key, {"ETH": 3}, "Untrusted Agent")

    return result1, result2

if __name__ == "__main__":
    asyncio.run(main())
