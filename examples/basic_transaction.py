import asyncio
import json
from saline_sdk.account import Account
from saline_sdk.rpc.client import Client
from saline_sdk.transaction.instructions import transfer
from saline_sdk.transaction.bindings import NonEmpty, Transaction
from saline_sdk.transaction.tx import prepareSimpleTx

TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "https://node1.try-saline.com"

async def main():
    # Create the root account from mnemonic
    account = Account.from_mnemonic(TEST_MNEMONIC)

    # Derive subaccounts for sender and receiver
    sender = account.create_subaccount(label="sender")
    receiver = account.create_subaccount(label="receiver")

    transfer_instruction = transfer(
        sender=sender.public_key,
        recipient=receiver.public_key,
        token="USDC",
        amount=20
    )

    tx = Transaction(
        instructions=NonEmpty.from_list([transfer_instruction]),
    )

    rpc = Client(http_url=RPC_URL)
    # Submit transaction and wait for validation
    result = await rpc.tx_broadcast(prepareSimpleTx(sender,tx))
    print(f"\nRPC response: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())
