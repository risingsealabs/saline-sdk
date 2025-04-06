# Saline SDK

Official Python SDK for interacting with the Saline blockchain network.

This is under active development. Both bugs and breaking changes can occur.

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

The Saline SDK provides a comprehensive, Web3-like interface for building applications on the Saline blockchain. It simplifies account management, transaction creation, signing, and interaction with Saline nodes.

## Features

- **Comprehensive Account Management**: Create, import, and manage accounts with BLS key pairs
- **Transaction Management**: Create, sign, and send transactions with ease
- **RPC Client**: Interact with Saline nodes via secure JSON-RPC
- **Async Support**: Full asynchronous API for high-performance applications
- **Token Support**: Built-in support for USDC, BTC, ETH, and other tokens
- **Web3-like Interface**: Familiar API for blockchain developers

## Installation

Requires Python 3.12+

```bash
# Install using pip
pip install saline-sdk

# Or install using Poetry
poetry add saline-sdk
```

See the :doc:`docs/installation` guide for development setup.

## Quick Start

This provides a brief overview. See the :doc:`docs/quickstart` guide and :doc:`docs/examples` for more details.

### 1. Initialize the Client

Connect to a running Saline node.

```python
from saline_sdk.rpc.client import Client

rpc_url = \"https://node0.try-saline.com\" # Your node's RPC endpoint
client = Client(http_url=rpc_url)

try:
    status = client.get_status()
    print(f\"Connected to Saline node: {status['node_info']['network']}!\")
except Exception as e:
    print(f\"Connection failed: {e}\")
```

### 2. Manage Accounts

Create or load accounts to manage keys.

```python
from saline_sdk.account import Account

# Create a new root account
root_account = Account.create()
print(f\"IMPORTANT: Save this mnemonic securely: {root_account.mnemonic}\")

# Load an existing account
# saved_mnemonic = \"your twelve word mnemonic phrase...\"
# root_account = Account.from_mnemonic(saved_mnemonic)

# Derive subaccounts (wallets)
wallet1 = root_account.create_subaccount(label=\"wallet1\")
print(f\"Created wallet1 with public key: {wallet1.public_key}\")
```

### 3. Check Balances

Query the balance of a specific account (requires `async`).

```python
import asyncio

# Assume 'client' and 'wallet1' are initialized from previous steps

async def check_wallet_balance(client: Client, wallet: Account):
    address = wallet.public_key
    print(f\"Checking balance for {address[:10]}...\")
    try:
        wallet_info = await client.get_wallet_info_async(address)
        balances = wallet_info.get('balances', []) if wallet_info else []
        print(f\"Balances: {balances}\")
    except Exception as e:
        print(f\"Could not get balance: {e}\")

# To run:
# asyncio.run(check_wallet_balance(client, wallet1))
```

### 4. Use the Testnet Faucet

Obtain test tokens on a test network (requires `async`).

```python
import asyncio
from saline_sdk.rpc.testnet.faucet import top_up

# Assume 'client' and 'wallet1' are initialized

async def fund_wallet(client: Client, wallet: Account):
    print(f\"Requesting testnet tokens for {wallet.public_key[:10]}...\")
    try:
        await top_up(account=wallet, client=client)
        print(\"Faucet request submitted. Check balance after a few seconds.\")
    except Exception as e:
        print(f\"Faucet top_up failed: {e}\")

# To run:
# asyncio.run(fund_wallet(client, wallet1))
```

### 5. Create and Send a Transaction

Build, sign, and submit a transaction (requires `async`).

```python
import asyncio
import json
from saline_sdk.transaction.bindings import Transaction, TransferFunds, NonEmpty
from saline_sdk.transaction.tx import prepareSimpleTx

# Assume 'client' and 'wallet1' (sender) are initialized and funded

async def send_funds(client: Client, sender_wallet: Account, recipient_pk: str, token: str, amount: int):
    print(f\"Preparing to send {amount} {token} from {sender_wallet.public_key[:10]}... to {recipient_pk[:10]}...\")
    instruction = TransferFunds(
        source=sender_wallet.public_key,
        target=recipient_pk,
        funds={token: amount}
    )
    tx = Transaction(instructions=NonEmpty.from_list([instruction]))

    # Sign using the sender's wallet
    signed_tx = prepareSimpleTx(sender_wallet, tx)

    # Submit
    try:
        result = await client.tx_commit(signed_tx)
        print(f\"Transaction submitted! Result: {json.dumps(result)}\")
    except Exception as e:
        print(f\"Transaction submission failed: {e}\")

# Example Run (replace recipient_pk)
# recipient_public_key = \"pk_of_recipient_wallet...\"
# asyncio.run(send_funds(client, wallet1, recipient_public_key, \"USDC\", 50))
```

## Documentation

For complete documentation, including advanced topics like Intents, visit [the Saline SDK documentation](https://saline-sdk.readthedocs.io/). (Ensure this link is correct)

## Development

### Setup for Development

```bash
# Clone the repository
git clone https://github.com/risingsealabs/saline-sdk.git
cd saline-sdk

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
poetry install
```

### Running Tests

```bash
# Run all tests
poetry run pytest -v

# Run specific test modules
poetry run pytest -v tests/unit/transaction/test_simple_transfer.py

# Run tests with coverage report
poetry run pytest -v --cov=saline_sdk
```

### Building Documentation
```bash
cd docs
poetry run make html
```
Repl:
```bash
poetry run sphinx-autobuild . _build/html --port 8001 --open-browser
```


### Auto-generated Modules

The `bindings.py` module is auto-generated from the Saline codebase and should not be modified directly. To provide documentation for this module, we use a separate file `bindings_docstrings.py` that contains docstrings that are applied at documentation build time.

This approach allows us to maintain proper documentation without modifying the auto-generated code. When `bindings.py` is regenerated, only the `bindings_docstrings.py` file needs to be updated to reflect any changes in the API.

To update the documentation for the bindings module:

1. Update the docstrings in `saline_sdk/transaction/bindings_docstrings.py`
2. The Sphinx extension in `docs/conf.py` will automatically apply these docstrings when generating documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Security

If you discover a security vulnerability within Saline SDK, please send an e-mail to security@risingsealabs.com.
