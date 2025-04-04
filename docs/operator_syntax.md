# Saline SDK Operator Syntax

The Saline SDK provides an operator-based syntax for defining intent predicates, making it easier to create and understand common patterns like token swaps. This document explains the core concepts, primitives, and operators used in Saline intents.

## Core Concepts

### Intent System

Intents are the cornerstone of Saline's authorization system. An intent is a predicate that specifies what actions an account allows to happen. Intents enable powerful patterns like token swaps, multi-signature authorization, time-based restrictions, and more.

#### Key Characteristics of Intents:

- **Declarative**: Intents declare what is permitted rather than how to do it
- **Composable**: Complex authorization rules are built by combining simpler intents
- **Enforceable**: The blockchain enforces intents at transaction execution time
- **Future-proof**: Intents work with transactions that may not exist yet (like future swap matches)

## Intent Primitives

Saline provides several basic primitives that can be combined to build complex intents:

### Flow Primitives

A `Flow` represents a token movement between parties:

```python
Flow(counterparty, token)
```

- `counterparty`: The party involved in the transaction (None means any party)
- `token`: The token type (e.g., Token.BTC, Token.ETH, Token.USDC)

### Action Primitives

Actions represent operations on flows:

| Primitive | Description | Example |
|-----------|-------------|---------|
| `Send()` | Token outflow from your account | `Send(Flow(None, Token.ETH))` |
| `Receive()` | Token inflow to your account | `Receive(Flow(None, Token.USDC))` |
| `Signature()` | Signature requirement | `Signature("public_key")` |
| `Temporary()` | Time-limited condition | `Temporary(condition, expiry_time)` |
| `Finite()` | Usage-limited condition | `Finite(condition, max_uses)` |

### Logical Operators

Logical operators combine intent expressions:

| Operator | Logic | Python Equivalent | Example |
|----------|-------|-------------------|---------|
| `All()` | AND all conditions | `&` operator | `condition1 & condition2` |
| `Any()` | OR conditions | `|` operator | `condition1 | condition2` |
| `Any(n, conditions)` | N-of-M conditions | N/A | `Any(2, [sig1, sig2, sig3])` |

## Basic Operators

The bindings module overloads several Python operators to allow for intuitive expression construction:

| Operator | Description | Example |
|----------|-------------|---------|
| `*` | Multiplication, used for quantities | `Send(...) * 10` |
| `<=`, `>=`, `<`, `>` | Comparison, used for defining value relationships | `Send(...) * 10 <= Receive(...) * 5` |
| `+` | Addition, used to combine expressions | `expr1 + expr2` |
| `&` | Logical AND | `expr1 & expr2` |
| `|` | Logical OR | `expr1 | expr2` |

## Understanding Flows

A `Flow` is a fundamental concept representing token movement between accounts:

```python
Flow(counterparty, token)
```

The flow parameters define:

1. **Counterparty**: The account on the other side of the transaction
   - `None`: Any account (wildcard)
   - `"public_key"`: A specific account
   
2. **Token**: The token type for the flow
   - `Token.BTC`, `Token.ETH`, etc.: Predefined token types
   - `Token["custom_token"]`: Custom token syntax

Examples:

```python
# Flow of ETH to/from any account
eth_flow = Flow(None, Token.ETH)

# Flow of USDT to/from a specific account
usdt_flow = Flow("counterparty_public_key", Token.USDT)
```

## Swap Intent Patterns

### Basic Swap Pattern

```python
# Define a swap intent: "I want to send X tokens and receive Y tokens"
intent = Send(Flow(None, Token.ETH)) * 2 <= Receive(Flow(None, Token.USDT)) * 100
```

This creates an intent that says: "I'm willing to send 2 ETH in exchange for receiving at least 100 USDT."

### Breaking Down the Pattern

1. `Send(Flow(None, Token.ETH))`: Defines the send operation with ETH as the token
2. `* 2`: Specifies the amount of ETH to send
3. `<=`: Sets up the exchange relationship (less than or equal)
4. `Receive(Flow(None, Token.USDT))`: Defines the receive operation with USDT as the token
5. `* 100`: Specifies the amount of USDT to receive

The `None` parameter in the `Flow` constructor means the counterparty can be anyone.

### Precise Exchange Rate Swap Pattern

For a swap with an exact exchange rate:

```python
# Exact exchange rate: 2 ETH for exactly 100 USDT
intent = Send(Flow(None, Token.ETH)) * 2 == Receive(Flow(None, Token.USDT)) * 100
```

### Swap with Specific Counterparty

```python
# Swap only with a specific counterparty
partner = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b"
intent = Send(Flow(partner, Token.ETH)) * 2 <= Receive(Flow(partner, Token.USDT)) * 100
```

## Multi-Signature Intent Patterns

Multi-signature (multisig) intents allow you to require multiple signatures to authorize a transaction. This provides increased security by distributing authority across multiple key holders.

### Basic N-of-M Multisig Pattern

```python
# Define the signers
sig1 = Signature("public_key_1")
sig2 = Signature("public_key_2")
sig3 = Signature("public_key_3")

# Create a 2-of-3 multisig intent
multisig_intent = Any(2, [sig1, sig2, sig3])
```

This intent requires at least 2 signatures from the 3 defined signers to authorize any transaction.

### Multisig with Transaction Size Threshold

A common pattern is to require multiple signatures only for transactions above a certain value:

```python
# Small transaction limit - single signature for transactions <= 1 BTC
small_tx_limit = Send(Flow(None, Token.BTC)) <= 1

# Multiple signatures required for larger transactions
signatures = [Signature("signer1"), Signature("signer2"), Signature("signer3")]
multisig_requirement = Any(2, signatures)  # 2-of-3 signature requirement

# Combined intent: Either small BTC transactions OR larger ones with multiple signatures
intent = small_tx_limit | multisig_requirement
```

This intent allows:
1. Transactions sending up to 1 BTC without requiring multiple signatures
2. Transactions of any size if they have at least 2 of the 3 signatures

### Role-Based Multisig

You can create more complex multisig schemes with different roles:

```python
# Define roles
admin_signatures = [Signature("admin1"), Signature("admin2")]
user_signatures = [Signature("user1"), Signature("user2"), Signature("user3")]

# At least one admin AND at least two users must sign
admin_approval = Any(1, admin_signatures)
user_approval = Any(2, user_signatures)

# Combined requirement using AND (&)
intent = admin_approval & user_approval
```

This intent requires at least one admin signature AND at least two user signatures to authorize a transaction.

## Restrictive Intent Patterns

Intents can also be used to place restrictions on an account, protecting it from unwanted activity.

### Restricting Incoming Transfers

A highly protective wallet that only accepts BTC from a specific counterparty:

```python
# Define the trusted counterparty
trusted_sender = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b"

# Allow receiving BTC only from this specific address
receive_btc_from_trusted = Receive(Flow(trusted_sender, Token.BTC))

# Block ALL other incoming transfers using the Restriction primitive
restrictive_intent = receive_btc_from_trusted
```

This intent only allows receiving BTC from the specified counterparty and blocks all other incoming transfers.

If you want to explicitly block all other incoming transfers, you can use a more explicit pattern:

```python
# Allow BTC from trusted sender
receive_btc_from_trusted = Receive(Flow(trusted_sender, Token.BTC))

# Block ALL other incoming transfers
block_all_other = ~Receive(Flow(None, None))  # The NOT (~) operator blocks all receives

# Combine: Allow BTC from trusted, block everything else
restrictive_intent = receive_btc_from_trusted | block_all_other
```

### Restricting Outgoing Transfers

Similarly, you can create an intent that restricts outgoing transfers:

```python
# Allow sending USDT to a specific address
allowed_recipient = "826e40d74167b3dcf957b55ad2fee7ba3a76b0d8fdace469d31540b016697c012578352b"
send_usdt_to_allowed = Send(Flow(allowed_recipient, Token.USDT))

# Block all other outgoing transfers
restrictive_intent = send_usdt_to_allowed
```

## Complete Swap Intent Example

```python
from saline_sdk.account import Account
from saline_sdk.transaction.bindings import (
    NonEmpty, Transaction, SetIntent, Flow, Token,
    Send, Receive
)
from saline_sdk.transaction.tx import prepareSimpleTx
from saline_sdk.rpc.client import Client

# Create account
account = Account.from_mnemonic("your mnemonic here").create_subaccount(name="swap_account")

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
```

## Advanced Intent Patterns

### Multi-Signature Authorization

Creating a 2-of-3 multi-signature requirement:

```python
# Define the signers
sig1 = Signature("public_key_1")
sig2 = Signature("public_key_2")
sig3 = Signature("public_key_3")

# Create a 2-of-3 multisig intent
multisig_intent = Any(2, [sig1, sig2, sig3])
```

### Time-Limited Intent

Creating an intent that expires after a specific time:

```python
# Base intent (e.g., token swap)
base_intent = Send(Flow(None, Token.ETH)) * 1 <= Receive(Flow(None, Token.USDT)) * 50

# Set expiry time (Unix timestamp) - e.g., 1 day from now
import time
expiry_time = int(time.time()) + (24 * 60 * 60)

# Create a time-limited intent
limited_intent = Temporary(base_intent, expiry_time)
```

### Usage-Limited Intent

Creating an intent that can only be used a specific number of times:

```python
# Base intent
base_intent = Send(Flow(None, Token.ETH)) * 0.1 <= Receive(Flow(None, Token.USDT)) * 5

# Create an intent limited to 5 uses
limited_intent = Finite(base_intent, 5)
```

### Complex Combined Intents

Combining multiple conditions with logical operators:

```python
# Define component intents
swap_intent = Send(Flow(None, Token.ETH)) * 1 <= Receive(Flow(None, Token.USDT)) * 50
multisig_intent = Any(2, [sig1, sig2, sig3])
small_tx_limit = Send(Flow(None, Token.ETH)) <= 0.1  # Small transaction limit

# Combined intent: Either small ETH transactions (<=0.1) OR
# larger transactions that need multisig AND match the swap rate
combined_intent = small_tx_limit | (multisig_intent & swap_intent)
```

## Advantages of Operator Syntax

The operator syntax offers several advantages over the more verbose approach:

1. **Readability**: Intents are expressed in a way that closely resembles natural language
2. **Conciseness**: Fewer lines of code required to express the same intent
3. **Maintainability**: Easier to understand and modify in the future
4. **Expressive Power**: Complex authorization rules can be expressed clearly

## Best Practices

1. **Start simple**: Begin with basic swap patterns and gradually build complexity
2. **Use meaningful variable names**: Name your intents according to their purpose
3. **Test extensively**: Verify intents behave as expected with different transaction patterns
4. **Use None for counterparty when possible**: This allows for maximum interoperability
5. **Consider adding time limits**: For sensitive operations, consider adding Temporary constraints

