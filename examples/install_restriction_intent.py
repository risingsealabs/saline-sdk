from saline_sdk.account import Account
from saline_sdk.transaction.bindings import Counterparty, Lit, NonEmpty, Receive, SetIntent, Token, Transaction, TransferFunds
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client
import asyncio
from saline_sdk.rpc.testnet.faucet import top_up

RPC_URL = "http://localhost:26657"
PERSISTENT_MNEMONIC = "vehicle glue talk scissors away blame film spend visit timber wasp hybrid"

async def main():
    root_account = Account.from_mnemonic(PERSISTENT_MNEMONIC)
    wallet = root_account.create_subaccount(label="restricted_wallet")
    trusted = root_account.create_subaccount(label="trusted_sender")
    untrusted = root_account.create_subaccount(label="untrusted_sender")
    print(wallet.public_key)

    rpc = Client(http_url=RPC_URL)

    # Print initial wallet balance
    initial_wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Initial wallet balance: {initial_wallet_info.get('balances', [])}")

    await top_up(account=trusted, client=rpc)
    await top_up(account=untrusted, client=rpc)

    # Set restrictive intent
    restricted_intent = Counterparty(trusted.public_key) & (Receive(Token.SALT) >= 10)
    set_intent = SetIntent(wallet.public_key, restricted_intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    intent_result = await rpc.tx_commit(prepareSimpleTx(wallet, tx))
    print(f"Set intent result: {'ACCEPTED' if intent_result.get('error') is None else 'REJECTED: ' + str(intent_result.get('error'))}")

    # Verify intent was installed correctly
    installed_intent = await rpc.get_intent_async(wallet.public_key)
    print(f"Installed intent: {'PRESENT' if installed_intent and installed_intent.get('intent') is not None else 'MISSING'}")

    # Test 1: SALT from trusted sender (should pass)
    print("\n=== Test 1: SALT from trusted sender (should pass) ===")
    transfer1 = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 11}
    )
    tx1 = Transaction(instructions=NonEmpty.from_list([transfer1]))
    result1 = await rpc.tx_commit(prepareSimpleTx(trusted, tx1))
    print(f"Transaction result: {'ACCEPTED' if result1.get('error') is None else 'REJECTED: ' + str(result1.get('error'))}")

    # Check balance after first transfer
    after_trusted_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Balance after trusted transfer: {after_trusted_info.get('balances', [])}")

    # Test 2: SALT from untrusted sender (should fail)
    print("\n=== Test 2: SALT from untrusted sender (should fail) ===")
    transfer2 = TransferFunds(
        source=untrusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 10}
    )
    tx2 = Transaction(instructions=NonEmpty.from_list([transfer2]))
    result2 = await rpc.tx_commit(prepareSimpleTx(untrusted, tx2))
    print(f"Transaction result: {'ACCEPTED' if result2.get('error') is None else 'REJECTED: ' + str(result2.get('error'))}")

    # Check balance after second transfer
    after_untrusted_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Balance after untrusted transfer: {after_untrusted_info.get('balances', [])}")

    # Test 3: USDC from trusted sender (should fail)
    print("\n=== Test 3: USDC from trusted sender (should fail) ===")
    transfer3 = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"USDC": 10}
    )
    tx3 = Transaction(instructions=NonEmpty.from_list([transfer3]))
    result3 = await rpc.tx_commit(prepareSimpleTx(trusted, tx3))
    print(result3)
    print(f"Transaction result: {'ACCEPTED' if result3.get('error') is None else 'REJECTED: ' + str(result3.get('error'))}")

    # Check final balance
    final_wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Final wallet balance: {final_wallet_info.get('balances', [])}")

    # Summary
    print("\n=== Summary ===")
    print(f"Test 1 (SALT from trusted): {'ACCEPTED' if result1.get('error') is None else 'REJECTED'} (Expected: ACCEPTED)")
    print(f"Test 2 (SALT from untrusted): {'ACCEPTED' if result2.get('error') is None else 'REJECTED'} (Expected: REJECTED)")
    print(f"Test 3 (USDC from trusted): {'ACCEPTED' if result3.get('error') is None else 'REJECTED'} (Expected: REJECTED)")
    print(f"Intent enforced correctly: {(result1.get('error') is None) and (result2.get('error') is not None) and (result3.get('error') is not None)}")

if __name__ == "__main__":
    asyncio.run(main())
