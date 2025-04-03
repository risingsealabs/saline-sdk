"""
RPC module for Saline SDK.

Provides client implementations for interacting with Saline nodes.
"""

from .client import Client
from .error import RPCError

__all__ = [
    'Client',
    'RPCError',
]
