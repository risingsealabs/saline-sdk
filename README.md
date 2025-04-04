# Saline SDK

Official Python SDK for interacting with the Saline blockchain network.

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

```bash
pip install saline-sdk
```

## Quick Start

### Initialize the SDK

```python
from saline_sdk import Saline

# Connect to a Saline node
saline = Saline(node_url="http://localhost:26657")

# Check connection
if saline.is_connected():
    print("Connected to Saline node!")
```

### Account Management

```python
# Create a new account
mnemonic = saline.create_account()
print(f"Save this mnemonic: {mnemonic}")

# Load an existing account
saline.load_account("your twelve word mnemonic phrase goes here")

# Create a subaccount
subaccount = saline.account.create_subaccount("my_subaccount")
print(f"Subaccount public key: {subaccount.public_key}")
```

### Using the Testnet Faucet

```python
from saline_sdk.rpc.client import Client
from saline_sdk.rpc.testnet.faucet import top_up_from_faucet
import asyncio

async def get_testnet_tokens():
    # Create a client
    client = Client(http_url="http://localhost:26657")

    # Get tokens for a subaccount directly
    await top_up_from_faucet(account=subaccount, client=client)

    # Or use the root account with default subaccount
    await top_up_from_faucet(account=saline.account, client=client)

# Run the async function
asyncio.run(get_testnet_tokens())
```

### Check Balances

```python
# Get balance of default subaccount
balance = saline.get_balance(currency="USDC")
print(f"USDC Balance: {balance}")

# Get all balances
all_balances = saline.get_all_balances()
for currency, amount in all_balances.items():
    print(f"{currency}: {amount}")
```

### Send Transactions

```python
# Simple transfer
result = saline.transfer(
    to="recipient_public_key",
    amount=100.0,
    currency="USDC"
)
print(f"Transaction hash: {result['hash']}")

# Wait for confirmation
receipt = saline.wait_for_transaction_receipt(result['hash'])
if receipt:
    print("Transaction confirmed!")
```

### Advanced Usage: Create and Sign Transactions

```python
from saline_sdk import transfer, sign, encodeSignedTx
from saline_sdk.transaction.tx import Transaction
import uuid

# Create a transaction with a transfer instruction
tx = Transaction(
    instructions=[
        transfer(
            sender=subaccount.public_key,
            recipient="destination_public_key",
            token="USDC",
            amount=100
        )
    ]
)

# Set the signer
tx.set_signer(subaccount.public_key)

# Generate a nonce
nonce = str(uuid.uuid4())

# Sign the transaction
signed_tx = sign(subaccount, nonce, tx)

# Encode for network submission
encoded_tx = encodeSignedTx(signed_tx)

# Send the signed transaction
result = saline.send_transaction(encoded_tx)
```

### Asynchronous API

```python
import asyncio

async def check_and_transfer():
    # Check balance
    balance = await saline.get_balance_async(currency="USDC")

    if balance >= 100:
        # Send transaction
        result = await saline.send_transaction_async(encoded_tx)

        # Wait for confirmation
        receipt = await saline.wait_for_transaction_receipt_async(result['hash'])
        return receipt

    return None

# Run the async function
receipt = asyncio.run(check_and_transfer())
```

## Documentation

For complete documentation, visit [the Saline SDK documentation](x).

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
