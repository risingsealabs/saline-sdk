# Whitelist Agents
# This is the code using SDK to install whitelist of counterparty to the asset address , alternative method to the UI

from saline_sdk.account import Account
from saline_sdk.transaction.bindings import Counterparty, Lit, NonEmpty, Receive, SetIntent, Token, Transaction, TransferFunds, Intent, Balance
from saline_sdk.transaction.tx import prepareSimpleTx, tx_is_accepted, print_tx_errors
from saline_sdk.rpc.client import Client
import asyncio
from saline_sdk.rpc.testnet.faucet import top_up

RPC_URL = "https://node0.try-saline.com"
PERSISTENT_MNEMONIC = "vehicle glue talk scissors away blame film spend visit timber wasp hybrid"
trusted_address = "a4af253e817ce3dea6aa59d44ba7990d3bdc5e775a11957d1d5d956d865e847169169c387becf63a1e74d1e5b81d0f53"

async def main():
    root_account = Account.from_mnemonic(PERSISTENT_MNEMONIC)
    wallet = root_account.create_subaccount(label="whitelist_wallet")
    rpc = Client(http_url=RPC_URL)

    # Print initial wallet balance
    initial_wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Initial wallet balance: {initial_wallet_info.balances}")

    # Whitelist trusted_address
    restricted_intent = Counterparty(trusted_address)
    set_intent = SetIntent(wallet.public_key, restricted_intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    tx_result = await rpc.tx_commit(prepareSimpleTx(wallet, tx))
    print(f"Set intent result: {'ACCEPTED' if tx_is_accepted(tx_result) else 'REJECTED: ' + print_tx_errors(tx_result)}")

    # Verify intent was installed correctly
    wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    installed_intent = wallet_info.parsed_intent
    print(Intent.to_json(installed_intent))
    print(f"Installed intent: {'PRESENT' if installed_intent is not None else 'MISSING'}")

if __name__ == "__main__":
    asyncio.run(main())