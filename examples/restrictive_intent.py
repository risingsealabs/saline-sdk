"""
Restrictive Intent Example for Saline Protocol - Improved
"""

import asyncio
import json
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, TransferFunds, Receive, Flow, Lit, Token
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client
from saline_sdk.rpc.testnet.faucet import top_up_from_faucet

RPC_URL = "http://localhost:26657"
PERSISTENT_MNEMONIC = "vehicle glue talk scissors away blame film spend visit timber wasp hybrid"

async def create_account_with_intent():
    """Create accounts and set up the restrictive intent"""
    print("=== Setting up restrictive intent ===")
    
    # Create accounts with fixed mnemonic
    root_account = Account.from_mnemonic(PERSISTENT_MNEMONIC)
    
    # Create a "dummy" account first to change all subsequent derivation paths
    dummy = root_account.create_subaccount(label="dummy")
    
    # Create the actual accounts we'll use
    wallet = root_account.create_subaccount(label="restricted_wallet")
    trusted = root_account.create_subaccount(label="trusted_sender")
    untrusted = root_account.create_subaccount(label="untrusted_sender")
    
    print(f"Restricted Wallet: {wallet.public_key[:10]}...{wallet.public_key[-8:]}")
    print(f"Trusted Sender:   {trusted.public_key[:10]}...{trusted.public_key[-8:]}")
    print(f"Untrusted Sender: {untrusted.public_key[:10]}...{untrusted.public_key[-8:]}")
    
    # Initialize client
    rpc = Client(http_url=RPC_URL, debug=True)
    
    # Fund sender accounts - now directly using subaccounts
    print("Funding accounts...")
    await top_up_from_faucet(account=trusted, client=rpc)
    await top_up_from_faucet(account=untrusted, client=rpc)
    
    # Check initial wallet balance
    wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"Initial balance: {json.dumps(wallet_info.get('balances', []))}") 
    
    # Create restrictive intent: only accept SALT from trusted sender
    print("\nCreating restrictive intent...")
    
    # Create intent
    restricted_intent = Receive(Flow(Lit(trusted.public_key), Token.SALT)) >= 0

    # Create the SetIntent instruction
    set_intent = SetIntent(wallet.public_key, restricted_intent)
    
    # Create transaction with the SetIntent instruction
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    
    # Sign the transaction
    signed_tx = prepareSimpleTx(wallet, tx)
    
    # Send the transaction
    print("Installing intent...")
    try:
        result = await rpc.tx_commit(signed_tx)
        
        if result.get('error') is None:
            print("✓ Intent successfully installed!")
            print("\nIntent structure (raw):")
            print(json.dumps(SetIntent.to_json(set_intent), indent=2))
        else:
            print(f"✗ Error installing intent: {result.get('error')}")
            
        # Check intent
        await asyncio.sleep(3)  # Wait longer for state propagation
        intent_result = await rpc.get_intent_async(wallet.public_key)
        print(f"Intent from chain: {json.dumps(intent_result)}")
        
    except Exception as e:
        print(f"Transaction failed: {str(e)}")
        return None, None, None
        
    return rpc, wallet, trusted, untrusted

async def test_transactions(rpc, wallet, trusted, untrusted):
    """Test transactions against the restrictive intent"""
    if not all([rpc, wallet, trusted, untrusted]):
        print("Cannot test transactions - account setup failed")
        return
        
    print("\n=== Testing Transactions ===")
    
    # Test 1: SALT from trusted sender (should pass)
    print("\nTest 1: SALT from trusted sender")
    before_balance = await rpc.get_balance_async(wallet.public_key, "SALT") or 0
    print(f"Before balance: {before_balance} SALT")
    
    salt_transfer = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 15}
    )
    tx = Transaction(instructions=NonEmpty.from_list([salt_transfer]))
    result = await rpc.tx_broadcast(prepareSimpleTx(trusted, tx))  # Use tx_broadcast to check validation first
    
    if result.get('code', 0) == 0:
        print("✓ Transaction validation passed")
        # Now commit it
        commit_result = await rpc.tx_commit(prepareSimpleTx(trusted, tx))
        print(f"Transaction commit result: {json.dumps(commit_result, indent=2)}")
    else:
        print(f"✗ Transaction validation failed: {json.dumps(result, indent=2)}")
    
    await asyncio.sleep(2)
    after_balance = await rpc.get_balance_async(wallet.public_key, "SALT") or 0
    print(f"After balance: {after_balance} SALT (change: {after_balance - before_balance})")
    
    # Test 2: USDC from trusted sender (should fail)
    print("\nTest 2: USDC from trusted sender")
    before_balance = await rpc.get_balance_async(wallet.public_key, "USDC") or 0
    print(f"Before balance: {before_balance} USDC")
    
    usdc_transfer = TransferFunds(
        source=trusted.public_key,
        target=wallet.public_key,
        funds={"USDC": 10}
    )
    tx = Transaction(instructions=NonEmpty.from_list([usdc_transfer]))
    result = await rpc.tx_broadcast(prepareSimpleTx(trusted, tx))
    
    if result.get('code', 0) == 0:
        print("✓ Transaction validation passed")
        # Now commit it
        commit_result = await rpc.tx_commit(prepareSimpleTx(trusted, tx))
        print(f"Transaction commit result: {json.dumps(commit_result, indent=2)}")
    else:
        print(f"✗ Transaction validation failed: {json.dumps(result, indent=2)}")
    
    await asyncio.sleep(2)
    after_balance = await rpc.get_balance_async(wallet.public_key, "USDC") or 0
    print(f"After balance: {after_balance} USDC (change: {after_balance - before_balance})")
    
    # Test 3: SALT from untrusted sender (should fail)
    print("\nTest 3: SALT from untrusted sender")
    before_balance = await rpc.get_balance_async(wallet.public_key, "SALT") or 0
    print(f"Before balance: {before_balance} SALT")
    
    untrusted_transfer = TransferFunds(
        source=untrusted.public_key,
        target=wallet.public_key,
        funds={"SALT": 15}
    )
    tx = Transaction(instructions=NonEmpty.from_list([untrusted_transfer]))
    result = await rpc.tx_broadcast(prepareSimpleTx(untrusted, tx))
    
    if result.get('code', 0) == 0:
        print("✓ Transaction validation passed")
        # Now commit it
        commit_result = await rpc.tx_commit(prepareSimpleTx(untrusted, tx))
        print(f"Transaction commit result: {json.dumps(commit_result, indent=2)}")
    else:
        print(f"✗ Transaction validation failed: {json.dumps(result, indent=2)}")
    
    await asyncio.sleep(2)
    after_balance = await rpc.get_balance_async(wallet.public_key, "SALT") or 0
    print(f"After balance: {after_balance} SALT (change: {after_balance - before_balance})")
    
    # Show final wallet balances
    wallet_info = await rpc.get_wallet_info_async(wallet.public_key)
    print(f"\nFinal wallet balance: {json.dumps(wallet_info.get('balances', []))}")

async def main():
    print("=== Saline SDK Restrictive Intent Example ===\n")
    
    rpc, wallet, trusted, untrusted = await create_account_with_intent()
    await test_transactions(rpc, wallet, trusted, untrusted)

if __name__ == "__main__":
    asyncio.run(main()) 