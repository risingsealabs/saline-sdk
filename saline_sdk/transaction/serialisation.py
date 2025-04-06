"""
Transaction encoding for Saline SDK.

This module handles transaction serialization for both network transmission
and signature generation, specifically designed to match Saline's
implementation's expectations.
"""

import json
import base64
import binascii
import logging
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


def serialize_for_network(tx: dict) -> bytes:
    """
    Serialize transaction for network submission.

    Saline requires a hexadecimal encoding with fields in a specific order:
    1. Sort all nested dictionaries for deterministic output
    2. Convert to JSON with field ordering preserved
    3. Encode as hex (base16)

    Args:
        tx: Transaction dictionary

    Returns:
        Hex-encoded transaction bytes
    """
    def sort_nested_dict(d):
        """Recursively sort all nested dictionaries by key."""
        if isinstance(d, dict):
            return {k: sort_nested_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [sort_nested_dict(x) for x in d]
        else:
            return d

    sorted_tx = sort_nested_dict(tx)
    ordered_tx = OrderedDict()

    if "signature" in sorted_tx:
        ordered_tx["signature"] = sorted_tx["signature"]

    if "signers" in sorted_tx:
        ordered_tx["signers"] = sorted_tx["signers"]

    if "signee" in sorted_tx:
        ordered_tx["signee"] = sorted_tx["signee"]

    if "nonce" in sorted_tx:
        ordered_tx["nonce"] = sorted_tx["nonce"]

    for key in sorted_tx:
        if key not in ["signature", "signers", "signee", "nonce"]:
            ordered_tx[key] = sorted_tx[key]

    json_bytes = json.dumps(ordered_tx, separators=(',', ':')).encode('utf-8')
    hex_bytes = binascii.hexlify(json_bytes)
    return hex_bytes


def decode_network_tx(data: bytes) -> Dict[str, Any]:
    """
    Decode a transaction received from the network.

    Args:
        data: The encoded transaction bytes

    Returns:
        Decoded transaction dictionary

    Raises:
        ValueError: If data is invalid
    """
    try:
        json_data = binascii.unhexlify(data)
        tx_dict = json.loads(json_data.decode())

        if not isinstance(tx_dict, dict):
            raise ValueError("Transaction must be a dictionary")


        required_fields = ['signature', 'signers']
        for field in required_fields:
            if field not in tx_dict:
                raise ValueError(f"Missing required field: {field}")

        return tx_dict
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")
    except Exception as e:
        raise ValueError(f"Failed to decode transaction: {str(e)}")


def encode_base64(data: bytes) -> str:
    """
    Encode binary data as base64 string.

    Args:
        data: Binary data to encode

    Returns:
        Base64 encoded string
    """
    return base64.b64encode(data).decode('ascii')


def decode_base64(data: str) -> bytes:
    """
    Decode base64 string to binary data.

    Args:
        data: Base64 encoded string

    Returns:
        Decoded binary data

    Raises:
        ValueError: If input is not valid base64
    """
    try:
        return base64.b64decode(data)
    except Exception as e:
        raise ValueError(f"Invalid base64 data: {str(e)}")
