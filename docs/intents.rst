======
Intents
======

Understanding the Intent System
==============================

Intents are the cornerstone of Saline's authorization system. An intent is a predicate that specifies what actions an account allows to happen. Intents enable powerful patterns like token swaps, multi-signature authorization, time-based restrictions, and more.

Key Characteristics of Intents:

- **Declarative**: Intents declare what is permitted rather than how to do it
- **Composable**: Complex authorization rules are built by combining simpler intents
- **Enforceable**: The blockchain enforces intents at transaction execution time
- **Future-proof**: Intents work with transactions that may not exist yet (like future swap matches)

Intent Primitives
===============

Saline provides several basic primitives that can be combined to build complex intents:

Flow Primitives
--------------

A ``Flow`` represents a token movement between parties:

.. code-block:: python

    Flow(counterparty, token)

- ``counterparty``: The party involved in the transaction (None means any party)
- ``token``: The token type (e.g., Token.BTC, Token.ETH, Token.USDC)

Action Primitives
---------------

Actions represent operations on flows:

- ``Send()``: Token outflow from your account
- ``Receive()``: Token inflow to your account
- ``Signature()``: Signature requirement
- ``Temporary()``: Time-limited condition
- ``Finite()``: Usage-limited condition

Example:

.. code-block:: python

    # Define a send operation for ETH to any counterparty
    Send(Flow(None, Token.ETH))
    
    # Define a receive operation for USDC from a specific counterparty
    Receive(Flow("counterparty_public_key", Token.USDC))

Operator Syntax
=============

The Saline SDK provides an operator-based syntax for defining intent predicates, making it easier to create and understand common patterns like token swaps.

Basic Operators
-------------

The bindings module overloads several Python operators to allow for intuitive expression construction:

- ``*``: Multiplication, used for quantities
- ``<=``, ``>=``, ``<``, ``>``: Comparison, used for defining value relationships
- ``+``: Addition, used to combine expressions
- ``&``: Logical AND
- ``|``: Logical OR

Understanding Flows
----------------

A ``Flow`` is a fundamental concept representing token movement between accounts:

.. code-block:: python

    Flow(counterparty, token)

The flow parameters define:

1. **Counterparty**: The account on the other side of the transaction
   - ``None``: Any account (wildcard)
   - ``"public_key"``: A specific account
   
2. **Token**: The token type for the flow
   - ``Token.BTC``, ``Token.ETH``, etc.: Predefined token types
   - ``Token["custom_token"]``: Custom token syntax

Examples:

.. code-block:: python

    # Flow of ETH to/from any account
    eth_flow = Flow(None, Token.ETH)

    # Flow of USDT to/from a specific account
    usdt_flow = Flow("counterparty_public_key", Token.USDT)

Common Intent Patterns
==================

Swap Intent Pattern
----------------

.. code-block:: python

    # Define a swap intent: "I want to send X tokens and receive Y tokens"
    intent = Send(Flow(None, Token.ETH)) * 2 <= Receive(Flow(None, Token.USDT)) * 100

This creates an intent that says: "I'm willing to send 2 ETH in exchange for receiving at least 100 USDT."

Breaking Down the Pattern:

1. ``Send(Flow(None, Token.ETH))``: Defines the send operation with ETH as the token
2. ``* 2``: Specifies the amount of ETH to send
3. ``<=``: Sets up the exchange relationship (less than or equal)
4. ``Receive(Flow(None, Token.USDT))``: Defines the receive operation with USDT as the token
5. ``* 100``: Specifies the amount of USDT to receive

Multi-Signature Intent Pattern
--------------------------

.. code-block:: python

    # Define the signers
    sig1 = Signature("public_key_1")
    sig2 = Signature("public_key_2")
    sig3 = Signature("public_key_3")

    # Create a 2-of-3 multisig intent
    multisig_intent = Any(2, [sig1, sig2, sig3])

This intent requires at least 2 signatures from the 3 defined signers to authorize any transaction.

Restrictive Intent Pattern
----------------------

A protective wallet that only accepts tokens from a specific sender:

.. code-block:: python

    # Define the trusted counterparty
    trusted_sender = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b"

    # Allow receiving SALT only from this specific address
    restrictive_intent = Receive(Flow(trusted_sender, Token.SALT))

Complete Swap Intent Example
------------------------

.. code-block:: python

    from saline_sdk.account import Account
    from saline_sdk.transaction.bindings import (
        NonEmpty, Transaction, SetIntent, Flow, Token,
        Send, Receive
    )
    from saline_sdk.transaction.tx import prepareSimpleTx
    from saline_sdk.rpc.client import Client

    # Create account
    account = Account.from_mnemonic("your mnemonic here").create_subaccount(label="swap_account")

    # Define swap parameters
    give_token = "ETH"
    give_amount = 2
    take_token = "USDT"
    take_amount = 100

    # Create swap intent using operator syntax
    intent = Send(Flow(None, Token[give_token])) * give_amount <= Receive(Flow(None, Token[take_token])) * take_amount

    # Create a SetIntent instruction and transaction
    set_intent = SetIntent(account.public_key, intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    signed_tx = prepareSimpleTx(account, tx)

    # Submit to blockchain
    client = Client()
    result = await client.tx_commit(signed_tx)

Advanced Intent Patterns
====================

Time-Limited Intent
---------------

Creating an intent that expires after a specific time:

.. code-block:: python

    # Base intent (e.g., token swap)
    base_intent = Send(Flow(None, Token.ETH)) * 1 <= Receive(Flow(None, Token.USDT)) * 50

    # Set expiry time (Unix timestamp) - e.g., 1 day from now
    import time
    expiry_time = int(time.time()) + (24 * 60 * 60)

    # Create a time-limited intent
    limited_intent = Temporary(base_intent, expiry_time)

Usage-Limited Intent
----------------

Creating an intent that can only be used a specific number of times:

.. code-block:: python

    # Base intent
    base_intent = Send(Flow(None, Token.ETH)) * 0.1 <= Receive(Flow(None, Token.USDT)) * 5

    # Create an intent limited to 5 uses
    limited_intent = Finite(base_intent, 5)

Complex Combined Intents
--------------------

Combining multiple conditions with logical operators:

.. code-block:: python

    # Define component intents
    swap_intent = Send(Flow(None, Token.ETH)) * 1 <= Receive(Flow(None, Token.USDT)) * 50
    multisig_intent = Any(2, [sig1, sig2, sig3])
    small_tx_limit = Send(Flow(None, Token.ETH)) <= 0.1  # Small transaction limit

    # Combined intent: Either small ETH transactions (<=0.1) OR
    # larger transactions that need multisig AND match the swap rate
    combined_intent = small_tx_limit | (multisig_intent & swap_intent)

Best Practices
===========

1. **Start simple**: Begin with basic swap patterns and gradually build complexity
2. **Use meaningful variable names**: Name your intents according to their purpose
3. **Test extensively**: Verify intents behave as expected with different transaction patterns
4. **Use None for counterparty when possible**: This allows for maximum interoperability
5. **Consider adding time limits**: For sensitive operations, consider adding Temporary constraints

For full details on intent operators and syntax, see :download:`Operator Syntax <operator_syntax.md>`. 