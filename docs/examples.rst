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
            status = await client.get_status()
            print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Could not connect to RPC @ {RPC_URL}. ({e})")
            return

        # Fund the sender account (necessary for the transfer)
        print("Funding sender account via faucet...")
        try:
            from saline_sdk.rpc.testnet.faucet import top_up
            await top_up(account=sender, client=client, tokens={"USDC": 50})
            print("Faucet funding successful.")
            await asyncio.sleep(3)  # Small delay for faucet transaction processing
        except Exception as e:
            print(f"WARN: Faucet top-up failed: {e}")
            # Optional: return here if funding is required
            # return

        # Sign and submit the transaction
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
            status = await client.get_status()
            print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']}")
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
            return  # Stop if faucet fails - accounts need funds for swaps

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

        # --- Check Balances Before Proceeding ---
        alice_info = await client.get_wallet_info_async(alice.public_key)
        bob_info = await client.get_wallet_info_async(bob.public_key)

        # Verify Alice has enough USDC to fulfill her part
        alice_usdc = alice_info.balances.get("USDC", 0) if alice_info.balances else 0
        has_alice_funds = alice_usdc >= 100

        # Verify Bob has enough BTC to fulfill his part
        bob_btc = bob_info.balances.get("BTC", 0) if bob_info.balances else 0
        has_bob_funds = bob_btc >= 1

        if not has_alice_funds or not has_bob_funds:
            print("Insufficient funds to complete swap - aborting")
            return

        # --- Matcher Logic ---
        print("Both parties have sufficient funds. Proceeding with swap...")
        fulfillment_instruction1 = TransferFunds(source=alice.public_key, target=bob.public_key, funds={"USDC": 100})
        fulfillment_instruction2 = TransferFunds(source=bob.public_key, target=alice.public_key, funds={"BTC": 1})
        fulfillment_tx = Transaction(instructions=NonEmpty.from_list([fulfillment_instruction1, fulfillment_instruction2]))

        # Matcher signs and submits
        print("Submitting fulfillment transaction...")
        try:
            signed_fulfillment_tx = prepareSimpleTx(matcher, fulfillment_tx)
            result = await client.tx_commit(signed_fulfillment_tx)
            print(f"Swap completed successfully. Hash: {result.get('hash')}")
        except Exception as e:
            print(f"ERROR: Fulfillment failed: {e}")

        # Verify final balances
        print("Verifying final balances...")
        alice_after = await client.get_wallet_info_async(alice.public_key)
        bob_after = await client.get_wallet_info_async(bob.public_key)
        print(f"Alice final: {alice_after.balances}")
        print(f"Bob final: {bob_after.balances}")

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
        # 1. The transaction only sends <= 1 BTC
        # 2. The transaction has at least 2 of 3 signatures

        small_tx_restriction = Restriction(
            Send(Token["BTC"]),
            Relation.LE,
            Lit(1)
        )

        signatures = [
            Signature(signer1.public_key),
            Signature(signer2.public_key),
            Signature(signer3.public_key)
        ]
        multisig_requirement = Any(2, signatures)

        # Combine with OR logic
        multisig_intent = Any(1, [small_tx_restriction, multisig_requirement])

        # Create and submit SetIntent transaction
        set_intent_instruction = SetIntent(multisig_wallet.public_key, multisig_intent)
        tx = Transaction(instructions=NonEmpty.from_list([set_intent_instruction]))

        client = Client(http_url=RPC_URL)
        try:
            status = await client.get_status()
            print(f"Connected to node: {status['node_info']['moniker']} @ {status['node_info']['network']} (Block: {status['sync_info']['latest_block_height']})")
        except Exception as e:
            print(f"ERROR: Could not connect to RPC @ {RPC_URL}. ({e})")
            return

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
2. ``query.py`` - Querying and parsing intents from the blockchain with detailed structure analysis
3. ``simple_matcher.py`` - Implementing a matching engine for swap intents with balance verification
4. ``fulfill_faucet_intent.py`` - Interacting with faucet intents to obtain tokens
5. ``install_restriction_intent.py`` - Creating a wallet with specific transfer restrictions
6. ``install_multisig_intent.py`` - Setting up multi-signature requirements for an account

Querying Intents
============

The ``query.py`` example demonstrates how to fetch and parse intents from the blockchain:

.. code-block:: python

    import asyncio
    from saline_sdk.rpc.client import Client
    import saline_sdk.transaction.bindings as bindings
    from saline_sdk.rpc.query_responses import (
        ParsedAllIntentsResponse,
        ParsedIntentInfo,
        contains_binding_type
    )

    RPC_URL = "https://node0.try-saline.com"

    # --- Intent Analysis Helper ---
    def is_likely_swap(intent: Optional[bindings.Intent]) -> bool:
        """Check if an intent matches a simple swap heuristic (All containing Send and Receive)."""
        if not isinstance(intent, bindings.All):
            return False # Heuristic: Top level must be All

        # Check if Send and Receive expressions exist anywhere within the 'All' structure
        has_send = contains_binding_type(intent, bindings.Send)
        has_receive = contains_binding_type(intent, bindings.Receive)

        return has_send and has_receive

    # --- Intent Structure Visualization ---
    def print_intent_structure(intent: Optional[Union[bindings.Intent, bindings.Expr]], indent: int = 0) -> None:
        """Print the structure of an Intent or Expr from bindings.py."""
        if intent is None:
            print(f"{' ' * indent}None")
            return

        # Get class name for the tag/type
        intent_name = intent.__class__.__name__
        print(f"{' ' * indent}{intent_name}", end="")

        # Print specific attributes based on the class
        if isinstance(intent, bindings.Counterparty):
            print(f" (address={intent.address})")
        elif isinstance(intent, bindings.Signature):
            print(f" (signer={intent.signer})")
        elif isinstance(intent, bindings.Lit):
            print(f" (value={intent.value!r})")
        elif isinstance(intent, (bindings.Receive, bindings.Send, bindings.Balance)):
            print(f" (token={intent.token.name})") # Access enum name
        else:
            print() # Newline for non-leaf nodes

        # Recursively print nested components
        if isinstance(intent, (bindings.All, bindings.Any)):
            for i, child in enumerate(intent.children):
                print(f"{' ' * (indent+2)}Child {i+1}:")
                print_intent_structure(child, indent + 4)
        elif isinstance(intent, bindings.Restriction):
            print(f"{' ' * indent}  LHS:")
            print_intent_structure(intent.lhs, indent + 4)
            print(f"{' ' * indent}  RHS:")
            print_intent_structure(intent.rhs, indent + 4)
            print(f"{' ' * indent}  Relation: {intent.relation.name}")

    async def main():
        client = Client(http_url=RPC_URL)

        all_intents_response = await client.get_all_intents()
        print(f"Found {len(all_intents_response.intents)} intent entries")

        intent_types = {}
        parsing_errors = 0
        likely_swaps = 0

        for intent_info in all_intents_response.intents.values():
            if intent_info.error:
                print(f"Parsing error for intent {intent_info.intent_id}: {intent_info.error}")
                parsing_errors += 1
                continue

            if intent_info.parsed_intent:
                intent_type = intent_info.parsed_intent.__class__.__name__
                intent_types[intent_type] = intent_types.get(intent_type, 0) + 1

                if is_likely_swap(intent_info.parsed_intent):
                    likely_swaps += 1
                    print(f"\nIntent {intent_info.intent_id[:8]}... appears to be a swap:")
                    print_intent_structure(intent_info.parsed_intent)

        print(f"\nSummary: Found {likely_swaps} swap intents out of {len(all_intents_response.intents)} total")
        print(f"Failed to parse {parsing_errors} intent entries")

    if __name__ == "__main__":
        asyncio.run(main())

Intent Matching with Balance Verification
==========================

The ``simple_matcher.py`` example illustrates a complete swap matching workflow:

1. Creating accounts with matching swap intents (Alice wants BTC, Bob wants USDC)
2. Funding these accounts via the testnet faucet
3. Querying the blockchain for all existing intents
4. Extracting and analyzing swap details from the parsed intent structures
5. Finding matching swap pairs based on the give/want parameters
6. Verifying the balances of both parties before attempting to execute the swap
7. Executing the swap as a matcher between accounts with sufficient funds

The matching algorithm in ``simple_matcher.py`` consists of several key components:

1. **Intent structure analysis**: Using recursive functions to extract swap parameters from complex intent trees
   with code like:

.. code-block:: python

    def _find_swap_intent(intent_node: Optional[Intent]) -> Optional[Tuple[Dict, Dict]]:
        """Recursively searches bindings structure for a Send/Receive pair under an 'All' node."""
        if isinstance(intent_node, All):
            send_details, receive_details = None, None
            for child in intent_node.children:
                if isinstance(child, Restriction):
                    details = _extract_restriction_details(child)
                    if details:
                        if details['type'] == 'send':
                            send_details = details
                        elif details['type'] == 'receive':
                            receive_details = details
            if send_details and receive_details:
                return send_details, receive_details
        # [... additional recursive search logic ...]

2. **Matching logic**: Finding pairs of complementary intents where one party's "give" matches another's "want":

.. code-block:: python

    # Find matching pairs (simple exact match)
    matching_pairs = []
    for i, swap1 in enumerate(swaps):
        for j, swap2 in enumerate(swaps):
            if i == j: continue  # Skip self-matches

            is_match = (
                swap1["give_token"] == swap2["want_token"] and
                swap1["want_token"] == swap2["give_token"] and
                swap1["give_amount"] == swap2["want_amount"] and
                swap1["want_amount"] == swap2["give_amount"]
            )
            if is_match:
                matching_pairs.append((swap1, swap2))
                break

3. **Balance verification**: Checking if both parties have sufficient funds before attempting the swap:

.. code-block:: python

    # Check balance for address 1
    info1 = await client.get_wallet_info_async(addr1)
    bal1 = info1.balances.get(swap1['give_token'], 0) if info1 and info1.balances else 0
    has_bal1 = bal1 >= swap1['give_amount']

    # Check balance for address 2
    info2 = await client.get_wallet_info_async(addr2)
    bal2 = info2.balances.get(swap2['give_token'], 0) if info2 and info2.balances else 0
    has_bal2 = bal2 >= swap2['give_amount']

    # Only proceed if both parties have sufficient funds
    if has_bal1 and has_bal2:
        # Execute the swap transaction

4. **Swap execution**: The matcher (a third party) executes the transaction between accounts that have sufficient funds:

.. code-block:: python

    # Prepare Swap Transaction
    instruction1 = TransferFunds(source=addr1, target=addr2, funds={swap1["give_token"]: swap1["give_amount"]})
    instruction2 = TransferFunds(source=addr2, target=addr1, funds={swap2["give_token"]: swap2["give_amount"]})
    tx = Transaction(instructions=NonEmpty.from_list([instruction1, instruction2]))
    signed_tx = prepareSimpleTx(matcher_account, tx)

    # Submit and verify results
    result = await client.tx_commit(signed_tx)
    # [... check result and print balances after the swap ...]

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

RPC Query Response Bindings
===============================

The module ``saline_sdk.rpc.query_responses`` provides structured parsing and analysis of blockchain data:

.. code-block:: python

    from saline_sdk.rpc.query_responses import (
        ParsedIntentInfo,        # Information about a single intent
        ParsedAllIntentsResponse,  # Collection of all intents from the blockchain
        ParsedWalletInfo,        # Account balance and intent information
        contains_binding_type,   # Helper to analyze intent structure -> check if intent contains
        parse_dict_to_binding_intent  # Converts raw JSON to bindings.py object
    )

These bindings make it easier to:

1. Parse raw intent data from the blockchain into structured Python objects
2. Query and analyze intent structures with helper functions
3. Process wallet information including balances and active intents
4. Identify specific patterns like swaps in complex intent structures

Example of using the helper function:

.. code-block:: python

    # Check if an intent contains both Send and Receive components (likely a swap)
    def is_likely_swap(intent: Optional[bindings.Intent]) -> bool:
        return (intent is not None and
                contains_binding_type(intent, bindings.Send) and
                contains_binding_type(intent, bindings.Receive))

    # Check the ParsedIntentInfo returned from get_all_intents
    if is_likely_swap(intent_info.parsed_intent):
        print(f"Intent {intent_info.intent_id} appears to be a swap intent")
