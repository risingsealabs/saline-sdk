======
Intents
======

Understanding the Intent System
==============================

Intents are the cornerstone of Saline. An intent is a predicate or a combination of predicates that specifies what actions an account allows to happen. Intents enable powerful patterns like account abstraction, delegation, token swaps, multi-signature authorization and more.

Key Characteristics of Intents:

- **Declarative**: Intents declare what is permitted rather than how to do it
- **Composable**: Complex authorization rules are built by combining simpler intents
- **Enforceable**: The blockchain enforces intents at transaction execution time
- **Future-proof**: Intents work with transactions that may not exist yet (like future swap matches)

Intents
===============

Saline provides several basic primitives that can be combined to build complex intents:

Primitives
--------------
- ``Restriction()``: Require two expressions be related in a given way
- ``Signature()``: Require signature from a given public key

Modifiers
--------------
- ``Temporary()``: Restrict an intent to a timeframe
- ``Finite()``: Restrict an intent to a maximum number of uses

Composite
--------------
- ``All()``: Requirement that all sub-intents be fulfilled
- ``Any()``: Require all sub-intents be fulfilled


Expressions
===============
- ``Lit()``: A literal value
- ``Balance``: Balance of the account hosting the intent
- ``Receive()``, ``Send()``: Token inflow/outflow from your account
- ``Arithmetic2()``: Elementary arithmetic over expressions

Operator Syntax
=============

The sdk overloads several Python operators to allow for intuitive manipulation of expressions and intents:

- ``&``: shorthand for ``All``
- ``|``: shorthand for ``Any 1``
- ``<=``, ``>=``, ``<``, ``>``: create an intent from two expressions
- ``*``, ``+``, ``-``, ``/``: arithmetically combine two expressions

Examples:

.. code-block:: python

    # Keep at least two USDC for each USDT
    Balance(USDC) >= 2 * Balance(USDT)

    # Prevent USDC dusting
    Receive(Flow(None, Token.USDC)) >= 10

Flow
--------------

A ``Flow`` represents a token movement between parties:

.. code-block:: python

    Flow(counterparty, token)

The flow parameters define:

1. **Counterparty**: The account on the other side of the transaction
  - ``None``: Any account
  - ``"public_key"``: A specific account

2. **Token**: The token type for the flow
  - ``Token.BTC``, ``Token.ETH``, etc.

Examples:

.. code-block:: python

    # Flow of ETH to/from any account
    eth_flow = Flow(None, Token.ETH)

    # Flow of USDT to/from a specific account
    usdt_flow = Flow(Lit("counterparty_public_key"), Token.USDT)

Common Intent Patterns
==================

Swap Intent Pattern
----------------

.. code-block:: python

    # Define a concrete swap intent: I want to swap 2 ETH for 100 USDT
    intent = Send(Flow(None, Token.ETH)) <= 2 & Receive(Flow(None, Token.USDT)) >= 100

    # Define a rate swap intent: I want 100 USDT for each 2 ETH
    intent = Send(Flow(None, Token.ETH)) * 2 <= Receive(Flow(None, Token.USDT)) * 100

Breaking Down the Pattern:

1. ``Send(Flow(None, Token.ETH))``: the amount of sent ETH
2. ``* 2``: multiplies by 2
3. ``<=``: Sets up the exchange relationship (less than or equal)
4. ``Receive(Flow(None, Token.USDT))``: the amount of received USDT
5. ``* 100``: multiplies by 100

Multi-Signature Intent Pattern
--------------------------

This intent requires at least 2 signatures from the 3 defined signers to authorize any transaction.

.. code-block:: python

    # Define the signers
    sig1 = Signature("public_key_1")
    sig2 = Signature("public_key_2")
    sig3 = Signature("public_key_3")

    # Create a 2-of-3 multisig intent
    multisig_intent = Any(2, [sig1, sig2, sig3])

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
    give_token = Token.ETH
    give_amount = 2
    take_token = Token.USDT
    take_amount = 100

    # Create swap intent using operator syntax
    intent = Send(Flow(None, give_token)) * give_amount <= Receive(Flow(None, take_token)) * take_amount

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
    availableAfter = true
    expiry_time = int(time.time()) + (24 * 60 * 60)

    # Create a time-limited intent
    limited_intent = Temporary(expiry_time, availableAfter, base_intent)

Usage-Limited Intent
----------------

Creating an intent that can only be used a specific number of times:

.. code-block:: python

    # Base intent
    base_intent = Send(Flow(None, Token.ETH)) * 0.1 <= Receive(Flow(None, Token.USDT)) * 5

    # Create an intent limited to 5 uses
    limited_intent = Finite(5, base_intent)

Best Practices
===========

1. **Start simple**: Begin with basic swap patterns and gradually build complexity
2. **Use meaningful variable names**: Name your intents according to their purpose
3. **Test extensively**: Verify intents behave as expected with different transaction patterns
4. **Use None for counterparty when possible**: This allows for maximum interoperability
5. **Consider adding time limits**: For sensitive operations, consider adding Temporary constraints
