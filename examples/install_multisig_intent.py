"""
Multisig Intent Example for Saline Protocol

This example demonstrates how to:
1. Create a multisig intent that requires N-of-M signatures
2. Install the intent on an account
3. Demonstrate how to use the intent
"""

import asyncio
import json
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, Any, 
    Signature, Send, Flow, Token
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client

TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
RPC_URL = "http://localhost:26657"

async def create_and_install_multisig_intent():
    print("=== Creating a Multisig Intent using Operator Syntax ===\n")

    root = Account.from_mnemonic(TEST_MNEMONIC)

    # Create 3 signers for the multisig
    signer1 = root.create_subaccount(name="signer1")
    signer2 = root.create_subaccount(name="signer2")
    signer3 = root.create_subaccount(name="signer3")
    
    # Create a multisig wallet subaccount that will have the intent
    multisig_wallet = root.create_subaccount(name="multisig_wallet")

    print("Multisig Participants:")
    print(f"Signer 1: {signer1.public_key[:10]}...{signer1.public_key[-8:]}")
    print(f"Signer 2: {signer2.public_key[:10]}...{signer2.public_key[-8:]}")
    print(f"Signer 3: {signer3.public_key[:10]}...{signer3.public_key[-8:]}")
    print(f"Multisig Wallet: {multisig_wallet.public_key[:10]}...{multisig_wallet.public_key[-8:]}")

    # Define the multisig intent
    # This creates an intent that requires either:
    # 1. The transaction only sends <= 1 BTC (small transaction limit), OR
    # 2. The transaction has at least 2 of 3 signatures from the signers
    
    # First part: restriction for small amounts (<=1 BTC)
    small_tx_restriction = Send(Flow(None, Token.BTC)) <= 1
    
    # Second part: 2-of-3 multisignature requirement
    signatures = [
        Signature(signer1.public_key),
        Signature(signer2.public_key),
        Signature(signer3.public_key)
    ]
    multisig_requirement = Any(2, signatures)
    
    # Combine the two conditions with OR (using the Any operator with threshold 1)
    multisig_intent = Any(1, [small_tx_restriction, multisig_requirement])
    
    # Create a SetIntent instruction to install the intent on the multisig wallet
    set_intent_instruction = SetIntent(multisig_wallet.public_key, multisig_intent)
    
    print("\nCreating SetIntent transaction to install the multisig intent")
    
    tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))

    signed_tx = prepareSimpleTx(multisig_wallet, tx)
    
    print("\nMultisig Intent Structure:")
    print(json.dumps(SetIntent.to_json(set_intent_instruction), indent=2))

    rpc = Client(http_url=RPC_URL)
    try:
        print("\nSubmitting to network...")
        result = await rpc.tx_commit(signed_tx)
        print(f"Intent installation result: {json.dumps(result, indent=2)}")
        
        if result.get("error") is None:
            print("\nMultisig intent successfully installed!")
            print(f"The account {multisig_wallet.public_key[:10]}...{multisig_wallet.public_key[-8:]} now has a multisig intent.")
            print("This intent allows:")
            print("1. Small transactions (<=1 BTC) without multiple signatures")
            print("2. Any transaction with at least 2-of-3 signatures from the designated signers")
        else:
            print(f"\nError installing intent: {result.get('error')}")
    except Exception as e:
        print(f"Transaction submission failed: {str(e)}")

    return multisig_wallet

async def main():
    await create_and_install_multisig_intent()

if __name__ == "__main__":
    asyncio.run(main()) 