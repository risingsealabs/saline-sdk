"""
Transaction utils module for the Saline SDK.

This module provides helper functions for creating various transaction components
that can be used when building transactions for the Saline network.
"""

from numpy import float64
from typing import List, Dict, Any, Optional, Union, Tuple
from .bindings import G2Element, Token


def transfer(sender: str, recipient: str, token: str, amount: Union[int, float]) -> Dict[G2Element, Dict [G2Element, Dict[Token, float64]]]:
    """
    Create a transfer for sending tokens.

    Args:
        sender: Sender's public key
        recipient: Recipient's public key
        token: Token identifier (e.g., "USDC", "BTC", "ETH")
        amount: Amount to transfer (as integer for atomic units or float for decimal representation)

    Returns:
        Dictionary representing asset transfers

    Example:
        >>> transfer("sender_public_key", "recipient_public_key", "USDC", 100)
    """
    # Saline compat
    # Convert float amounts to integer if needed (assuming 6 decimal places)
    if isinstance(amount, float):
        amount = int(amount * 1000000)

    return {sender: {recipient: {token: amount}}}


def swap(
    sender: str,
    recipient: str,
    give_token: str,
    give_amount: Union[int, float],
    take_token: str,
    take_amount: Union[int, float]
) -> Dict[G2Element, Dict [G2Element, Dict[Token, float64]]]:
    """
    Create a pair of transfers for a token swap.

    Args:
        sender: Sender's public key
        recipient: Recipient's public key
        give_token: Token to give (e.g., "USDC")
        give_amount: Amount to give
        take_token: Token to take (e.g., "BTC")
        take_amount: Amount to take

    Returns:
        Dictionary representing asset transfers

    Example:
        >>> swap("alice_pk", "bob_pk", "USDC", 100, "BTC", 0.001)
    """
    # TODO: Temp for Saline compat - remove this once Saline is updated
    if isinstance(give_amount, float):
        give_amount = int(give_amount * 1000000)

    if isinstance(take_amount, float):
        take_amount = int(take_amount * 1000000)

    # Create two transfers
    sender_transfer = transfer(
        sender=sender,
        recipient=recipient,
        token=give_token,
        amount=give_amount
    )

    recipient_transfer = transfer(
        sender=recipient,
        recipient=sender,
        token=take_token,
        amount=take_amount
    )

    return sender_transfer | recipient_transfer


def set_intent(signer_pk: str, condition_type: str = "ConditionTag_Signature") -> List:
    """
    Create an intent mask entry for authorizations.

    Args:
        signer_pk: Signer public key
        condition_type: Condition tag type, defaults to signature-based authorization

    Returns:
        Intent mask entry for use in transactions

    Example:
        >>> set_intent("signer_public_key")
    """
    return [
        signer_pk,
        {
            "Right": [
                [condition_type, []],
                signer_pk
            ]
        }
    ]
