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

Intent Primitives and Composites
===============================

Saline provides several basic building blocks that can be combined to create complex intents:

Primitives
--------------
- ``Restriction()``: Require two expressions be related in a given way
- ``Signature()``: Require signature from a given public key

Composites
--------------
- ``All(conditions: list)``: Requires that **all** sub-intents/conditions in the list are fulfilled (logical AND).
- ``Any(threshold: int, conditions: list)``: Requires that **at least `threshold`** sub-intents/conditions in the list are fulfilled (logical OR or M-of-N).

Modifiers
--------------
- ``Temporary(expiry_timestamp: int, available_after: bool, intent)``: Restricts an intent to be valid only up to a specific Unix timestamp.
- ``Finite(max_uses: int, intent)``: Restricts an intent to a maximum number of uses.

Expressions
=============
Expressions are used within ``Restriction`` intents to evaluate conditions based on transaction details or account state:

- ``Lit(value)``: Represents a literal value (e.g., number, string).
- ``Balance(token: str)``:Balance of the specified token for the account hosting the intent.
- ``Receive(token: Token)``: Represents the amount of a token received.
- ``Send(token: Token)``: Represents the amount of a token sent.
- ``Arithmetic2(op: ArithOp, lhs, rhs)``: Elementary arithmetic operations (Add, Sub, Mul, Div) over expressions.

Operator Syntax (Optional Shorthands)
=====================================

For convenience, the SDK *may* overload some Python operators as shorthands for common intent constructions. However, using the explicit binding classes (`Restriction`, `All`, `Any`, `Arithmetic2`, etc.) is generally recommended for clarity, especially for complex intents. The examples below primarily use the explicit bindings.

*Potential* Shorthands (Check SDK source or specific examples for current support):
- ``&``: Shorthand for ``All([...])``
- ``|``: Shorthand for ``Any(1, [...])`` (logical OR)
- ``<=``, ``>=``, ``<``, ``>``: Create a ``Restriction`` between two expressions.
- ``*``, ``+``, ``-``, ``/``: Create an ``Arithmetic2`` expression.

1. **Counterparty**: The account on the other side of the transaction
  - ``None``: Any account
  - ``"public_key"``: A specific account

2. **Token**: The token type for the flow
  - ``Token.BTC``, ``Token.ETH``, etc.


Common Intent Patterns
==================

Swap Intent Pattern
----------------

.. code-block:: python

    # Define a concrete swap intent: I want to swap 2 ETH for 100 USDT
    intent = Send(Token.ETH) <= 2 & Receive(Token.USDT) >= 100

    # Define a rate swap intent: I want 100 USDT for each 2 ETH
    intent = Send(Token.ETH) * 2 <= Receive(Token.USDT) * 100

Breaking Down the Pattern:

1. ``Send(Token.ETH)``: the amount of sent ETH
2. ``* 2``: multiplies by 2
3. ``<=``: Sets up the exchange relationship (less than or equal)
4. ``Receive(Token.USDT)``: the amount of received USDT
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
        NonEmpty, Transaction, SetIntent, Token,
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
    intent = Send(give_token) * give_amount <= Receive(take_token) * take_amount

    # Create a SetIntent instruction and transaction
    set_intent = SetIntent(account.public_key, intent)
    tx = Transaction(instructions=NonEmpty.from_list([set_intent]))
    signed_tx = prepareSimpleTx(account, tx)

    # Submit to blockchain
    client = Client()
    result = await client.tx_commit(signed_tx)

Advanced Intent Patterns (Coming Soon)
====================

Time-Limited Intent
---------------

Creating an intent that expires after a specific time:

.. code-block:: python

    # Base intent (e.g., token swap)
    base_intent = Send(Token.ETH) * 1 <= Receive(Token.USDT) * 50

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
    base_intent = Send(Token.ETH) * 0.1 <= Receive(Token.USDT) * 5

    # Create an intent limited to 5 uses
    limited_intent = Finite(5, base_intent)

Best Practices
===========

1. **Use Explicit Bindings**: Prefer `Restriction`, `All`, `Any` for clarity over operator shorthands, especially for non-trivial intents.
2. **Start Simple**: Begin with basic patterns (like fixed swaps) and gradually add complexity (`Any`, `Temporary`, `Finite`).
3. **Test Extensively**: Verify intents behave as expected with various transaction patterns.
4. **Consider Modifiers**: For sensitive operations, consider adding `Temporary` or `Finite` constraints.
