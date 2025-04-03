"""
Token Swap Example for Saline Protocol

Demonstrates how to create a token swap transaction that is signed by both parties.
"""

import asyncio
import json
import uuid
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import NonEmpty, Signed, Transaction
from saline_sdk.transaction.tx import encodeSignedTx
from saline_sdk.transaction.instructions import transfer
from saline_sdk.rpc.client import Client
from saline_sdk.crypto.bls import BLS

TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "http://localhost:26657"

async def create_and_submit_swap():
    """Create and submit a token swap transaction between two parties"""
    print("=== Saline SDK Token Swap Example ===\n")

    # Create accounts for the swap participants
    root = Account.from_mnemonic(TEST_MNEMONIC)
    alice = root.create_subaccount(name="alice")
    bob = root.create_subaccount(name="bob")

    print("Swap Participants:")
    print(f"Alice: {alice.public_key[:10]}...{alice.public_key[-8:]}")
    print(f"Bob: {bob.public_key[:10]}...{bob.public_key[-8:]}")

    # Define swap parameters
    alice_token = "USDC"
    alice_amount = 100
    bob_token = "BTC"
    bob_amount = 1
    
    print(f"\nSwap Terms:")
    print(f"Alice sends: {alice_amount} {alice_token}")
    print(f"Bob sends:   {bob_amount} {bob_token}")

    # Create the transfer instructions for both sides of the swap
    alice_instruction = transfer(
        sender=alice.public_key,
        recipient=bob.public_key,
        token=alice_token,
        amount=alice_amount
    )

    bob_instruction = transfer(
        sender=bob.public_key,
        recipient=alice.public_key,
        token=bob_token,
        amount=bob_amount
    )

    # Combine the instructions into a single transaction
    tx = Transaction(instructions=NonEmpty.from_list([alice_instruction, bob_instruction]))

    # In a real-world scenario, the transaction would be passed between parties
    # Here we simulate the process for demonstration purposes
    
    # Generate a unique nonce for the transaction
    nonce = str(uuid.uuid4())
    
    # Prepare the message to sign (this would be shared between parties)
    msg = json.dumps([nonce, Transaction.to_json(tx)], separators=(',', ':')).encode('utf-8')

    print("\nMulti-party signing process:")

    # Each party signs the same message
    print("Alice signs the transaction...")
    alice_sig = alice.sign(msg)

    print("Bob signs the transaction...")
    bob_sig = bob.sign(msg)

    # Aggregate the signatures into a single BLS signature
    print("Aggregating signatures...")
    aggregate_signature = BLS.aggregate_signatures([alice_sig, bob_sig])

    # Create the final signed transaction
    signed_tx = Signed(
        nonce=nonce,
        signature=aggregate_signature.hex(),
        signee=tx,
        signers=NonEmpty.from_list([alice.public_key, bob.public_key])
    )

    print("\nSwap Transaction Summary:")
    tx_summary = {
        "signature": f"{signed_tx.signature[:10]}...{signed_tx.signature[-8:]}",
        "signers": [f"{s[:10]}...{s[-8:]}" for s in signed_tx.signers.list],
        "instructions": [
            {
                "sender": instr.source[:10] + "..." + instr.source[-8:],
                "recipient": instr.target[:10] + "..." + instr.target[-8:],
                "token": list(instr.funds.keys())[0],
                "amount": list(instr.funds.values())[0]
            }
            for instr in tx.instructions.list
        ]
    }
    print(json.dumps(tx_summary, indent=2))

    # Submit the transaction to the network
    rpc = Client(http_url=RPC_URL)
    try:
        print("\nSubmitting transaction to the network...")
        result = await rpc.tx_commit(encodeSignedTx(signed_tx))
        
        if result.get("error") is None:
            print("✓ Swap transaction successful!")
        else:
            print(f"✗ Swap transaction failed: {result.get('error')}")
            
        print(f"\nTransaction result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"✗ Transaction submission failed: {str(e)}")

async def main():
    await create_and_submit_swap()

if __name__ == "__main__":
    asyncio.run(main())
