========
Examples
========

This section provides detailed examples of using the Saline SDK for various blockchain operations.
These examples correspond to the scripts found in the ``examples/`` directory of the project.

Basic Transaction
===============

This example demonstrates how to create and submit a basic transfer transaction.
See ``examples/basic_transaction.py``.

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.rpc.client import Client
    from saline_sdk.transaction.bindings import NonEmpty, Transaction, TransferFunds
    from saline_sdk.transaction.tx import prepareSimpleTx

    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    RPC_URL = "https://node0.try-saline.com"

    async def main():
        # Create a temporary root account for this run
        root_account = Account.create()
        print("root account mnemonic:", root_account._mnemonic)


        # Derive subaccounts for sender and receiver
        sender = root_account.create_subaccount(label="sender")
        receiver = root_account.create_subaccount(label="receiver")

        # Create a TransferFunds instruction
        transfer_instruction = TransferFunds(
            source=sender.public_key,
            target=receiver.public_key,
            funds={"USDC": 20}
        )

        tx = Transaction(
            instructions=NonEmpty.from_list([transfer_instruction]),
        )

        # Connect to the Saline node
        client = Client(http_url=RPC_URL)
        try:
            status = client.get_status()
                    print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Could not connect to RPC @ {RPC_URL}. ({e})")
            return

        # Fund the sender account (necessary for the transfer)
        print("Funding sender account via faucet...")
        try:
            # Import top_up function
            from saline_sdk.rpc.testnet.faucet import top_up
            await top_up(account=sender, client=client, tokens={"USDC": 50})
            print("Faucet funding successful.")
            # Add a small delay for faucet transaction processing
            await asyncio.sleep(3)
        except Exception as e:
            print(f"WARN: Faucet top-up failed: {e}")
            # Decide whether to continue or return based on faucet requirement
            # return # Example: stop if faucet fails

        # Sign the transaction using the sender's account and submit
        print("Submitting transfer transaction...")
        try:
            signed_tx = prepareSimpleTx(sender, tx)
            result = await client.tx_commit(signed_tx)
            print(f"RPC response: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"ERROR: Transaction submission failed: {e}")

    if __name__ == "__main__":
        asyncio.run(main())

Token Swap (Intent-Based)
=========================

This example shows how to set up matching swap intents and have a matcher fulfill them.
This is the recommended way to perform swaps in Saline.
See ``examples/simple_matcher.py`` (this example is simplified from the script).

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Transaction, SetIntent, TransferFunds,
        Send, Receive, Token, Restriction, Relation, All, Lit
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client
    from saline_sdk.rpc.testnet.faucet import top_up

    RPC_URL = "https://node0.try-saline.com"
    WAIT_SECONDS = 5 # Wait for intents to process

    async def setup_and_match_swap():
        # Create accounts for the swap participants and a matcher
        root = Account.create()
        alice = root.create_subaccount(label="alice")
        bob = root.create_subaccount(label="bob")
        matcher = root.create_subaccount(label="matcher")

        # Connect to the node
        client = Client(http_url=RPC_URL)
        try:
            status = client.get_status()
                    print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Could not connect to RPC @ {RPC_URL}. ({e})")
            return

        # Fund Alice and Bob
        print("Funding Alice and Bob via faucet...")
        try:
            await asyncio.gather(
                top_up(account=alice, client=client, tokens={"USDC": 150}),
                top_up(account=bob, client=client, tokens={"BTC": 2})
            )
            print("Faucet funding complete. Waiting for tx processing...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"WARN: Faucet top-up failed: {e}")
            # return # Optionally stop if faucet fails

        # Alice wants 1 BTC for 100 USDC
        alice_intent = All([
            Restriction(Send(Token["USDC"]), Relation.EQ, Lit(100)),
            Restriction(Receive(Token["BTC"]), Relation.EQ, Lit(1))
        ])
        # Bob wants 100 USDC for 1 BTC
        bob_intent = All([
            Restriction(Send(Token["BTC"]), Relation.EQ, Lit(1)),
            Restriction(Receive(Token["USDC"]), Relation.EQ, Lit(100))
        ])

        # Set intents
        print("Setting swap intents...")
        alice_set_intent_tx = Transaction(instructions=NonEmpty.from_list([SetIntent(alice.public_key, alice_intent)]))
        bob_set_intent_tx = Transaction(instructions=NonEmpty.from_list([SetIntent(bob.public_key, bob_intent)]))
        try:
            await asyncio.gather(
                client.tx_commit(prepareSimpleTx(alice, alice_set_intent_tx)),
                client.tx_commit(prepareSimpleTx(bob, bob_set_intent_tx))
            )
            print(f"Intents submitted. Waiting {WAIT_SECONDS}s for propagation...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"ERROR: Failed to set intents: {e}")
            return

        # --- Matcher Logic (Simplified - see simple_matcher.py for full implementation) ---
        # In a real scenario, the matcher would query intents (client.get_all_intents())
        # find the matching pair (alice_intent matches bob_intent), and extract addresses.
        # Here we assume the matcher found Alice and Bob.

        print("Matcher found pair: Alice <=> Bob. Preparing fulfillment transaction...")
        fulfillment_instruction1 = TransferFunds(source=alice.public_key, target=bob.public_key, funds={"USDC": 100})
        fulfillment_instruction2 = TransferFunds(source=bob.public_key, target=alice.public_key, funds={"BTC": 1})
        fulfillment_tx = Transaction(instructions=NonEmpty.from_list([fulfillment_instruction1, fulfillment_instruction2]))

        # Matcher signs and submits
        print("Submitting fulfillment transaction...")
        try:
            signed_fulfillment_tx = prepareSimpleTx(matcher, fulfillment_tx)
            result = await client.tx_commit(signed_fulfillment_tx)
            print(f"Fulfillment Result: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"ERROR: Fulfillment failed: {e}")

    if __name__ == "__main__":
        asyncio.run(setup_and_match_swap())

Multi-Signature Intent
=========================

This example demonstrates creating and installing a multi-signature intent on an account.
See ``examples/install_multisig_intent.py``.

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Transaction, SetIntent, Any,
        Signature, Send, Token, Restriction, Relation, Lit
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client

    RPC_URL = "https://node0.try-saline.com"

    async def create_and_install_multisig_intent():
        # Use Account.create() for temporary accounts in examples
        root = Account.create()

        # Create 3 signers for the multisig
        signer1 = root.create_subaccount(label="signer1")
        signer2 = root.create_subaccount(label="signer2")
        signer3 = root.create_subaccount(label="signer3")

        # Create a multisig wallet subaccount that will have the intent
        multisig_wallet = root.create_subaccount(label="multisig_wallet")

        # Define the multisig intent
        # Requires either:
        # 1. The transaction only sends <= 1 BTC (using Restriction binding)
        # 2. The transaction has at least 2 of 3 signatures (using Signature binding)

        # Part 1: Restriction for small amounts (<=1 BTC)
        small_tx_restriction = Restriction(
            Send(Token["BTC"]),
            Relation.LE,
            Lit(1)
        )

        # Part 2: 2-of-3 multisignature requirement
        signatures = [
            Signature(signer1.public_key),
            Signature(signer2.public_key),
            Signature(signer3.public_key)
        ]
        # Any(threshold, list_of_conditions) - requires threshold conditions to be met
        multisig_requirement = Any(2, signatures)

        # Combine the two conditions with OR (using Any with threshold 1)
        # Any(1, [...]) means: Is condition 1 OR condition 2 true?
        multisig_intent = Any(1, [small_tx_restriction, multisig_requirement])

        # Create a SetIntent instruction to install the intent on the multisig wallet
        set_intent_instruction = SetIntent(multisig_wallet.public_key, multisig_intent)

        tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))

        # Connect to the node
        client = Client(http_url=RPC_URL)
        try:
            status = client.get_status()
                    print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Could not connect to RPC @ {RPC_URL}. ({e})")
            return

        # Sign with the wallet being modified and submit
        print("Submitting SetIntent transaction...")
        try:
            signed_tx = prepareSimpleTx(multisig_wallet, tx)
            result = await client.tx_commit(signed_tx)
            print(f"SetIntent Result: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"ERROR: SetIntent failed: {e}")

    if __name__ == "__main__":
        asyncio.run(create_and_install_multisig_intent())

Restrictive Intent
===============

This example demonstrates creating a restrictive intent that only allows receiving BTC from a specific counterparty.
This pattern is useful for security-sensitive wallets or accounts that need tight control over incoming transfers.
See ``examples/restrictive_intent.py``.

Simple Restriction Example
==================

This simplified example demonstrates how to create a restrictive intent that only allows receiving SALT tokens
from a specific trusted sender address. This creates a highly restricted wallet for secure custody.
See ``examples/restrictive_intent.py``.

.. code-block:: python

    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Receive, SetIntent, Transaction, TransferFunds, Token
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client
    import asyncio
    from saline_sdk.rpc.testnet.faucet import top_up

    RPC_URL = "https://node0.try-saline.com"
    WAIT_SECONDS = 3 # Wait for transactions

    async def main():
        # Use Account.create() for example clarity
        root_account = Account.create()
        wallet = root_account.create_subaccount(label="restricted_wallet")
        trusted = root_account.create_subaccount(label="trusted_sender")
        untrusted = root_account.create_subaccount(label="untrusted_sender")

        client = Client(http_url=RPC_URL)
        try:
            status = client.get_status()
            print(f"Connected: {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Connection failed: {e}")
            return

        # Fund the test accounts
        print("Funding accounts via faucet...")
        try:
            await asyncio.gather(
                top_up(account=trusted, client=client, tokens={"SALT": 50, "USDC": 50}),
                top_up(account=untrusted, client=client, tokens={"SALT": 50})
            )
            print("Funding complete. Waiting {WAIT_SECONDS}s...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"WARN: Faucet funding failed: {e}")
            # return # Optionally stop

        # Clear any existing intent (optional, good practice for testing)
        print("Clearing existing intent on wallet...")
        clear_tx = Transaction(instructions=NonEmpty.from_list([
            SetIntent(wallet.public_key, None)
        ]))
        try:
            await client.tx_commit(prepareSimpleTx(wallet, clear_tx))
            print("Clear intent submitted. Waiting {WAIT_SECONDS}s...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"WARN: Failed to clear intent: {e}")

        # Set restrictive intent - only allow receiving SALT from trusted sender
        print("Setting restrictive intent on wallet...")
        restricted_intent = Counterparty(trusted.public_key) & (Receive(Token.SALT) >= 10)
        set_intent = SetIntent(wallet.public_key, restricted_intent)
        tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
        try:
            await client.tx_commit(prepareSimpleTx(wallet, tx))
            print("Restrictive intent set. Waiting {WAIT_SECONDS}s...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"ERROR: Failed to set restrictive intent: {e}")
            return # Stop if intent setting fails

        # Test transactions against the intent:
        print("\nTesting transfers against intent...")
        import json

        # Test 1: SALT from trusted sender (should pass)
        print("Test 1: Sending SALT from TRUSTED sender (EXPECT PASS)...")
        transfer1 = TransferFunds(source=trusted.public_key, target=wallet.public_key, funds={"SALT": 15})
        tx1 = Transaction(instructions=NonEmpty.from_list([transfer1]))
        try:
            result1 = await client.tx_commit(prepareSimpleTx(trusted, tx1))
            print(f"  Result: {json.dumps(result1)}")
        except Exception as e:
            print(f"  ERROR: {e}")
        await asyncio.sleep(WAIT_SECONDS)

        # Test 2: SALT from untrusted sender (should fail)
        print("Test 2: Sending SALT from UNTRUSTED sender (EXPECT FAIL)...")
        transfer2 = TransferFunds(source=untrusted.public_key, target=wallet.public_key, funds={"SALT": 15})
        tx2 = Transaction(instructions=NonEmpty.from_list([transfer2]))
        try:
            result2 = await client.tx_commit(prepareSimpleTx(untrusted, tx2))
            print(f"  Result: {json.dumps(result2)}")
        except Exception as e:
            print(f"  ERROR: {e}")
        await asyncio.sleep(WAIT_SECONDS)

        # Test 3: USDC from trusted sender (should fail)
        print("Test 3: Sending USDC from TRUSTED sender (EXPECT FAIL)...")
        transfer3 = TransferFunds(source=trusted.public_key, target=wallet.public_key, funds={"USDC": 10})
        tx3 = Transaction(instructions=NonEmpty.from_list([transfer3]))
        try:
            result3 = await client.tx_commit(prepareSimpleTx(trusted, tx3))
            print(f"  Result: {json.dumps(result3)}")
        except Exception as e:
            print(f"  ERROR: {e}")

    if __name__ == "__main__":
        asyncio.run(main())

Testnet Faucet with Swap Intent
==============================

This example demonstrates requesting tokens from the testnet faucet and creating matching swap intents, similar to the `simple_matcher.py` flow.
See ``examples/faucet_and_swap_intent.py`` (this is a conceptual reconstruction).

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Transaction, SetIntent, TransferFunds,
        Send, Receive, Token, Restriction, Relation, All, Lit
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client
    from saline_sdk.rpc.testnet.faucet import top_up

    RPC_URL = "https://node0.try-saline.com"
    WAIT_SECONDS = 5

    async def faucet_and_swap_example():
        # Create accounts
        root_account = Account.create()
        alice = root_account.create_subaccount(label="alice")
        bob = root_account.create_subaccount(label="bob")
        matcher = root_account.create_subaccount(label="matcher")

        # Connect to client
        client = Client(http_url=RPC_URL)
        try:
            status = client.get_status()
            print(f"Connected: {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Connection failed: {e}")
            return

        # Request tokens for Alice and Bob directly
        print("Requesting tokens from the faucet...")
        try:
            await asyncio.gather(
                top_up(account=alice, client=client, tokens={"USDT": 15}),
                top_up(account=bob, client=client, tokens={"BTC": 0.002})
            )
            print("Faucet funding complete. Waiting {WAIT_SECONDS}s...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"WARN: Faucet funding failed: {e}")
            # return # Optionally stop

        # Create matching swap intents (Alice: 10 USDT for 0.001 BTC; Bob: 0.001 BTC for 10 USDT)
        print("Setting swap intents...")
        alice_intent = All([
            Restriction(Send(Token["USDT"]), Relation.EQ, Lit(10)),
            Restriction(Receive(Token["BTC"]), Relation.EQ, Lit(0.001))
        ])
        bob_intent = All([
            Restriction(Send(Token["BTC"]), Relation.EQ, Lit(0.001)),
            Restriction(Receive(Token["USDT"]), Relation.EQ, Lit(10))
        ])

        # Set intents on the blockchain
        alice_set_tx = Transaction(instructions=NonEmpty.from_list([SetIntent(alice.public_key, alice_intent)]))
        bob_set_tx = Transaction(instructions=NonEmpty.from_list([SetIntent(bob.public_key, bob_intent)]))
        try:
            await asyncio.gather(
                client.tx_commit(prepareSimpleTx(alice, alice_set_tx)),
                client.tx_commit(prepareSimpleTx(bob, bob_set_tx))
            )
            print(f"Intents set. Waiting {WAIT_SECONDS}s...")
            await asyncio.sleep(WAIT_SECONDS)
        except Exception as e:
            print(f"ERROR: Failed to set intents: {e}")
            return

        # Execute the swap match using the matcher account
        print("Matcher fulfilling swap...")
        fulfill_tx = Transaction(instructions=NonEmpty.from_list([
            TransferFunds(source=alice.public_key, target=bob.public_key, funds={"USDT": 10}),
            TransferFunds(source=bob.public_key, target=alice.public_key, funds={"BTC": 0.001})
        ]))
        try:
            signed_fulfill = prepareSimpleTx(matcher, fulfill_tx)
            result = await client.tx_commit(signed_fulfill)
            print(f"Fulfillment Result: {json.dumps(result, indent=2)}")
        except Exception as e:
            print(f"ERROR: Fulfillment failed: {e}")

        # Optional: Show balances before and after the swap (Add similar logic from simple_matcher)

    if __name__ == "__main__":
        asyncio.run(faucet_and_swap_example())

Additional Examples
=================

The SDK repository contains additional example files demonstrating more advanced use cases:

1. ``install_swap_intent.py`` - Setting up an intent to enable automated swaps
2. ``intent_queries_example.py`` - Querying the blockchain for intent information
3. ``simple_matcher.py`` - Implementing a matching engine for swap intents
4. ``fulfill_faucet_intent.py`` - Interacting with faucet intents to obtain tokens
5. ``restrictive_intent.py`` - Creating a wallet that only accepts BTC from specific sources
6. ``faucet_and_swap_intent.py`` - Requesting testnet tokens and creating swap intents

Using the Testnet Module
=================

The Saline SDK includes a testnet module for development purposes. The faucet functionality is available via ``saline_sdk.rpc.testnet.faucet.top_up``:

.. code-block:: python

    import asyncio
    from saline_sdk.account import Account
    from saline_sdk.rpc.client import Client
    from saline_sdk.rpc.testnet.faucet import top_up

    RPC_URL = "https://node0.try-saline.com"

    async def request_testnet_tokens():
        # Create an account
        account = Account.create()
        alice = account.create_subaccount(label="alice")

        # Create a client
        client = Client(http_url=RPC_URL)
        try:
            status = client.get_status()
            print(f"Connected: {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Connection failed: {e}")
            return

        # Request tokens from the testnet faucet
        print("Requesting default faucet tokens for Alice...")
        try:
            # The function accepts Account or Subaccount objects
            # use_dynamic_amounts=True gets the amounts defined in the faucet's own intent
            new_balances = await top_up(
                account=alice,
                client=client,
                use_dynamic_amounts=True
            )
            print(f"Balances after default top-up: {new_balances}")
        except Exception as e:
            print(f"WARN: Default top_up failed: {e}")

        # Or request specific amounts
        print("Requesting specific token amounts for Alice...")
        try:
            custom_balances = await top_up(
                account=alice,
                client=client,
                tokens={"BTC": 0.5, "ETH": 5, "USDC": 500},
                use_dynamic_amounts=False
            )
            print(f"Balances after custom top-up: {custom_balances}")
        except Exception as e:
            print(f"WARN: Custom top_up failed: {e}")

    if __name__ == "__main__":
        asyncio.run(request_testnet_tokens())
