========
Examples
========

This section provides detailed examples of using the Saline SDK for various blockchain operations.
These examples correspond to the scripts found in the ``examples/`` directory of the project.

Examples Defined in SRC
=================

The SDK repository contains additional example files demonstrating more advanced use cases:

1. `install_swap_intent.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/install_swap_intent.py>`_ – Setting up an intent to enable automated swaps
2. `query.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/query.py>`_ – Querying and parsing intents from the blockchain with detailed structure analysis
3. `simple_matcher.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/simple_matcher.py>`_ – Implementing a matching engine for swap intents with balance verification
4. `fulfill_faucet_intent.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/fulfill_faucet_intent.py>`_ – Interacting with the faucet intent directly to obtain tokens
5. `install_restriction_intent.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/install_restriction_intent.py>`_ – Creating a wallet with specific transfer restrictions  
6. `install_multisig_intent.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/install_multisig_intent.py>`_ – Setting up multi-signature requirements for an account  
Basic Transaction
===============

This example demonstrates how to create and submit a basic transfer transaction.
See the `basic_transaction.py GitHub <https://github.com/risingsealabs/saline-sdk/blob/main/examples/basic_transaction.py>`_.

.. code-block:: python

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
See `install_multisig_intent.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/install_multisig_intent.py>`.

.. code-block:: python

    import asyncio
    import json
    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Transaction, SetIntent, Any,
        Signature, Send, Token
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client

    TEST_MNEMONIC = "excuse ozone east canoe duck tortoise dentist approve bid wagon area funny"
    RPC_URL = "https://node0.try-saline.com"

    async def create_and_install_multisig_intent():
        print("=== Creating a Multisig Intent using Operator Syntax ===\n")

        root = Account.from_mnemonic(TEST_MNEMONIC)

        # Create 3 signers for the multisig
        signer1 = root.create_subaccount(label="signer1")
        signer2 = root.create_subaccount(label="signer2")
        signer3 = root.create_subaccount(label="signer3")

        # Create a multisig wallet subaccount that will have the intent
        multisig_wallet = root.create_subaccount(label="multisig_wallet")

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
        small_tx_restriction = Send(Token.BTC) <= 1

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




Restrictive Intent
==================

This simplified example demonstrates how to create a restrictive intent that only allows receiving SALT tokens
from a specific trusted sender address. This creates a highly restricted wallet for secure custody. This pattern is useful for security-sensitive wallets or accounts that need tight control over incoming transfers.
See `install_restriction_intent.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/install_restriction_intent.py>`.

.. code-block:: python

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


Console output as parsed and prettified by helpers in ``saline-sdk.transaction.tx``:

.. code-block:: console

    > python examples/install_restriction_intent.py

    85065d52efa38d0234796712342de02285cd4e75db7ad8cf505e982ef17c6bd020ab5af40051b97afc31df9517893e94
    Initial wallet balance: {'BTC': 10, 'SALT': 143}
    Set intent result: ACCEPTED
    Installed intent: PRESENT

    === Test 1: SALT from trusted sender (should pass) ===
    Transaction result: ACCEPTED
    Balance after trusted transfer: {'BTC': 10, 'SALT': 154}

    === Test 2: SALT from untrusted sender (should fail) ===
    Transaction - CHECK_TX failed with code 1
    Decoded message:
    Rejected by
    nacl:0x85065d…893e94 requires:
        All of
        Counterparty is nacl:0xa92ba3…26876e

    Transaction result: REJECTED: None
    Balance after untrusted transfer: {'BTC': 10, 'SALT': 154}

    === Test 3: USDC from trusted sender (should fail) ===
    Transaction - CHECK_TX failed with code 1
    Decoded message:
    Rejected by
    nacl:0x85065d…893e94 requires:
        All of
        Constraint not met: Incoming SALT >= 10.0

    Transaction result: REJECTED: None
    Final wallet balance: {'BTC': 10, 'SALT': 154}

    === Summary ===
    Test 1 (SALT from trusted): ACCEPTED (Expected: ACCEPTED)
    Test 2 (SALT from untrusted): REJECTED (Expected: REJECTED)
    Test 3 (USDC from trusted): REJECTED (Expected: REJECTED)

Querying Intents
============

The `query.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/query.py>` example demonstrates how to fetch and parse intents from the blockchain:

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
            return False # Heuristic: Top level must be All - the intent logical equivalent of boolean AND

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

The `simple_matcher.py <https://github.com/risingsealabs/saline-sdk/blob/main/examples/simple_matcher.py>` example illustrates a complete swap matching workflow:

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
