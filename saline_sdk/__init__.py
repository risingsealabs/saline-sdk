"""
Saline SDK: Official Python library for interacting with the Saline blockchain.

This package provides comprehensive tools and interfaces for developers to interact
with the Saline blockchain network, including account management, transaction
construction, and RPC communication.

Basic usage:
    from saline_sdk import Saline

    # Initialize with node URL
    saline = Saline(node_url="http://localhost:26657")

    # Create a new account
    mnemonic = saline.create_account()

    # Or load an existing account
    saline.load_account("your twelve word mnemonic phrase goes here")
"""

# Core components
from .account import Account, Subaccount
from .rpc.client import Client
from .rpc.error import RPCError

# Transaction components
from .transaction.tx import sign, encodeSignedTx
from .transaction.instructions import transfer, swap, set_intent

# Common token enum
from .rpc.client import Token

# Testnet utilities - New import location
from .rpc.testnet.faucet import top_up

__all__ = [
    # Core interfaces
    'Account',      # Account management
    'Subaccount',   # Individual account/keypair
    'Client',       # RPC client
    'Token',        # Token types
    'RPCError',     # RPC error


    'sign',         # Transaction signing
    'encodeSignedTx', # Transaction encoding
    'transfer',     # Transfer instruction
    'swap',         # Swap instruction
    'set_intent',   # Intent creation

    # Testnet utilities
    'top_up',         # Async faucet utility
]

__version__ = '0.1.0'
