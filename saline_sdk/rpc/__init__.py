"""
RPC client for interacting with Saline nodes.

This package provides utilities for interacting with Saline nodes via RPC.
"""

from saline_sdk.rpc.client import Client
from saline_sdk.rpc.error import RPCError

__all__ = [
    'Client',
    'RPCError',
]
