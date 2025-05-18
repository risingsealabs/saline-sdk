# Create Swap + Counterparty + 1 time mandates
# This is the code to create agent to submit transaction to user asset address that try to swap. There are 2 agent, here one is
# the agent that is whitelisted in the user mandate the other aren't. Both trying to submit the same swap transaction.
# [Alternative) You could also trying testing this with 1 trusted agent but submitted different kind of transactions to the user address

import asyncio
import json
from typing import Dict, Optional, Any

from saline_sdk.account import Account
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.bindings import Transaction, NonEmpty
from saline_sdk.transaction.instructions import swap
from saline_sdk.transaction.tx import prepareSimpleTx, print_tx_errors
from saline_sdk.rpc.testnet.faucet import top_up

RPC_URL = "https://node1.try-saline.com"
TEST_MNEMONIC = "exhaust wave soldier analyst angry portion mixed delay true disagree wood smart"
## Agent interacting with the rule_address address, this is where mandates is installed
RULE_ADDRESS = "85065d52efa38d0234796712342de02285cd4e75db7ad8cf505e982ef17c6bd020ab5af40051b97afc31df9517893e94"

def format_balances(balances: Optional[Dict[str, Any]]) -> str:
    if not balances:
        return "Unavailable or no balances"
    return ', '.join(f"{v} {k}" for k, v in balances.items()) or "(Empty)"

async def submit_swap_tx(rpc: Client, signer: Account, sender_address: str, label: str):
    # Create a manual swap transaction: send ETH, receive BTC
    funds = swap(
        sender = sender_address,
        recipient = RULE_ADDRESS,
        give_token = "ETH",
        give_amount = 11,
        take_token = "BTC",
        take_amount = 0.5
    )

    tx = Transaction(funds=funds, burn={}, intents={}, mint={})
    signed_tx = prepareSimpleTx(signer, tx)

    print(f"\nSubmitting swap for {label}...")
    try:
        result = await rpc.tx_commit(signed_tx)
        print_tx_errors(result)
        print(f"{label} swap result:\n", json.dumps(result, indent=2))

        updated_balance = await rpc.get_wallet_info_async(sender_address)
        print(f"{label} balance after:", format_balances(updated_balance.balances))
        return result
    except Exception as e:
        print(f"❌ ERROR: Swap failed for {label}: {e}")

async def main():
    rpc = Client(http_url=RPC_URL)
    root_account = Account.from_mnemonic(TEST_MNEMONIC)

    trusted = root_account.create_subaccount(label="trusted_agent")
    untrusted = root_account.create_subaccount(label="untrusted_agent")

    print("Trusted Agent:", trusted.public_key)
    print("Untrusted Agent:", untrusted.public_key)

    print("\nTopping up faucet for both agents...")
    await top_up(trusted, rpc)
    await top_up(untrusted, rpc)

    # Show initial balances
    for label, account in [("Trusted Agent", trusted), ("Untrusted Agent", untrusted)]:
        info = await rpc.get_wallet_info_async(account.public_key)
        print(f"{label} balance before:", format_balances(info.balances))

    # Submit swap attempts
    result_trusted = await submit_swap_tx(rpc, trusted, trusted.public_key, "Trusted Agent")
    # result_untrusted = await submit_swap_tx(rpc, untrusted, untrusted.public_key, "Untrusted Agent")

    return result_trusted
    # return result_untrusted

if __name__ == "__main__":
    asyncio.run(main())
