from saline_sdk.account import Account
from saline_sdk.transaction.bindings import Flow, NonEmpty, Receive, SetIntent, Transaction, TransferFunds
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client, Token
import asyncio
from saline_sdk.rpc.testnet.faucet import top_up_from_faucet

RPC_URL = "http://localhost:26657"
PERSISTENT_MNEMONIC = "vehicle glue talk scissors away blame film spend visit timber wasp hybrid"

async def main():
    root_account = Account.from_mnemonic(PERSISTENT_MNEMONIC)
    wallet = root_account.create_subaccount(label="restricted_wallet")
    trusted = root_account.create_subaccount(label="trusted_sender")
    untrusted = root_account.create_subaccount(label="untrusted_sender")
    
    rpc = Client(http_url=RPC_URL)

    await top_up_from_faucet(account=trusted, client=rpc)
    await top_up_from_faucet(account=untrusted, client=rpc)

    # Clear any existing intent
    clear_tx = Transaction(instructions=NonEmpty.from_list([
        SetIntent(wallet.public_key, None)
    ]))
    await rpc.tx_commit(prepareSimpleTx(wallet, clear_tx))
    
    # Set restrictive intent
    restricted_intent = Receive(Flow(trusted.public_key, Token.SALT))
    set_intent = SetIntent(wallet.public_key, restricted_intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    await rpc.tx_commit(prepareSimpleTx(wallet, tx))

    # Test 1: SALT from trusted sender (should pass)
    transfer1 = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 15}
    )
    tx1 = Transaction(instructions=NonEmpty.from_list([transfer1]))
    await rpc.tx_commit(prepareSimpleTx(trusted, tx1))
    
    # Test 2: SALT from untrusted sender (should fail)
    transfer2 = TransferFunds(
        source=untrusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 15}
    )
    tx2 = Transaction(instructions=NonEmpty.from_list([transfer2]))
    await rpc.tx_commit(prepareSimpleTx(untrusted, tx2))
    
    # Test 3: USDC from trusted sender (should fail)
    transfer3 = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"USDC": 10}
    )
    tx3 = Transaction(instructions=NonEmpty.from_list([transfer3]))
    await rpc.tx_commit(prepareSimpleTx(trusted, tx3))

if __name__ == "__main__":
    asyncio.run(main())
