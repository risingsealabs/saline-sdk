from saline_sdk.account import Account
from saline_sdk.transaction.bindings import Counterparty, Lit, NonEmpty, Receive, SetIntent, Token, Transaction, TransferFunds, Intent
from saline_sdk.transaction.tx import prepareSimpleTx, tx_is_accepted, print_tx_errors
from saline_sdk.rpc.client import Client
import asyncio
from saline_sdk.rpc.testnet.faucet import top_up

RPC_URL = "https://node0.try-saline.com"
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
    print(f"Initial wallet balance: {initial_wallet_info.balances}")

    await top_up(account=trusted, client=rpc)
    await top_up(account=untrusted, client=rpc)

    # Set restrictive intent
    restricted_intent = Counterparty(trusted.public_key) & (Receive(Token.SALT) >= 10)
    set_intent = SetIntent(wallet.public_key, restricted_intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    tx_result = await rpc.tx_commit(prepareSimpleTx(wallet, tx))
    print(f"Set intent result: {'ACCEPTED' if tx_is_accepted(tx_result) else 'REJECTED: ' + str(tx_result)}")

    # Verify intent was installed correctly
    wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    installed_intent = wallet_info.parsed_intent

    print(f"Installed intent: {'PRESENT' if installed_intent is not None else 'MISSING'}")

    # Test 1: SALT from trusted sender (should pass)
    print("\n=== Test 1: SALT from trusted sender (should pass) ===")
    transfer1 = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 11}
    )
    tx1 = Transaction(instructions=NonEmpty.from_list([transfer1]))
    result1 = await rpc.tx_commit(prepareSimpleTx(trusted, tx1))
    print(f"Transaction result: {'ACCEPTED' if tx_is_accepted(result1) else f'REJECTED: {print_tx_errors(result1)}'}")

    # Check balance after first transfer
    after_trusted_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Balance after trusted transfer: {after_trusted_info.balances}")

    # Test 2: SALT from untrusted sender (should fail)
    print("\n=== Test 2: SALT from untrusted sender (should fail) ===")
    transfer2 = TransferFunds(
        source=untrusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 10}
    )
    tx2 = Transaction(instructions=NonEmpty.from_list([transfer2]))
    result2 = await rpc.tx_commit(prepareSimpleTx(untrusted, tx2))
    print(f"Transaction result: {'ACCEPTED' if tx_is_accepted(result2) else f'REJECTED: {print_tx_errors(result2)}'}")

    # Check balance after second transfer
    after_untrusted_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Balance after untrusted transfer: {after_untrusted_info.balances}")

    # Test 3: USDC from trusted sender (should fail)
    print("\n=== Test 3: USDC from trusted sender (should fail) ===")
    transfer3 = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"USDC": 10}
    )
    tx3 = Transaction(instructions=NonEmpty.from_list([transfer3]))
    result3 = await rpc.tx_commit(prepareSimpleTx(trusted, tx3))
    print(f"Transaction result: {'ACCEPTED' if tx_is_accepted(result3) else f'REJECTED: {print_tx_errors(result3)}'}")

    # Check final balance
    final_wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Final wallet balance: {final_wallet_info.balances}")

    # Summary
    print("\n=== Summary ===")
    print(f"Test 1 (SALT from trusted): {'ACCEPTED' if tx_is_accepted(result1) else 'REJECTED'} (Expected: ACCEPTED)")
    print(f"Test 2 (SALT from untrusted): {'ACCEPTED' if tx_is_accepted(result2) else 'REJECTED'} (Expected: REJECTED)")
    print(f"Test 3 (USDC from trusted): {'ACCEPTED' if tx_is_accepted(result3) else 'REJECTED'} (Expected: REJECTED)")

if __name__ == "__main__":
    asyncio.run(main())
