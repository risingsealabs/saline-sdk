# Saline SDK Operator Syntax

The Saline SDK provides a operator-based syntax for defining intent predicates, making it easier to create and understand common patterns like token swaps.

## Basic Operators

The bindings module overloads several Python operators to allow for intuitive expression construction:

| Operator | Description | Example |
|----------|-------------|---------|
| `*` | Multiplication, used for quantities | `Send(...) * 10` |
| `<=` | Less than or equal, used for defining exchanges | `Send(...) <= Receive(...)` |
| `+` | Addition | `expr1 + expr2` |
| `>`, `<`, `>=`, `<=` | Comparison operators | `expr1 > expr2` |


### Basic Swap Pattern

```python
# Define a swap intent: "I want to send X tokens and receive Y tokens"
intent = Send(Flow(None, Token.ETH)) * 2 <= Receive(Flow(None, Token.USDT)) * 100
```

This creates an intent that says: "I'm willing to send 2 ETH in exchange for receiving at least 100 USDT."

### Breaking Down the Pattern

1. `Send(Flow(None, Token.ETH))`: Defines the send operation with ETH as the token
2. `* 2`: Specifies the amount of ETH to send
3. `<=`: Sets up the exchange relationship
4. `Receive(Flow(None, Token.USDT))`: Defines the receive operation with USDT as the token
5. `* 100`: Specifies the amount of USDT to receive

The `None` parameter in the `Flow` constructor means the counterparty can be anyone.

## Example: Creating a Swap Intent


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
result = await client.broadcast_tx_sync_async(signed_tx)
```

## Advantages of Operator Syntax

The operator syntax offers several advantages over the more verbose approach:

1. **Readability**: Intents are expressed in a way that closely resembles natural language
2. **Conciseness**: Fewer lines of code required to express the same intent
3. **Maintainability**: Easier to understand and modify in the future

## Advanced Usage

You can build more complex intents by combining operators:

```python
# More complex intent with multiple conditions
intent = (Send(Flow(None, Token.ETH)) * 5 <= Receive(Flow(None, Token.BTC)) * 0.2) & \
         (Send(Flow(None, Token.USDC)) * 100 <= Receive(Flow(None, Token.SALT)) * 500)
```

This creates an intent that requires both conditions to be satisfied.

