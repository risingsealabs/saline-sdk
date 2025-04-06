"""
Transaction handling module for the Saline SDK.

This module provides functions for creating, signing, and encoding transactions
for submission to the Saline network.
"""

import base64
import binascii
import json
import uuid
from typing import Union
from saline_sdk.account import Account, Subaccount
from .bindings import dumps, NonEmpty, Signed, Transaction


def prepareSimpleTx(signer: Union[Account, Subaccount], tx: Transaction) -> str:
    """
    Prepare a simple transaction by signing it with a generated nonce.
    
    This is a convenience function that generates a nonce, signs the transaction,
    and encodes it in a single step.
    
    Args:
        signer: Account or Subaccount to sign with
        tx: Transaction object to sign
        
    Returns:
        Base64 encoded transaction ready for submission
    """
    new_nonce = str(uuid.uuid4())
    signed = sign(signer, new_nonce, tx)
    return encodeSignedTx(signed)


def encodeSignedTx(signed: Signed) -> str:
    """
    Encode a signed transaction for network submission.
    
    Args:
        signed: Signed transaction object
        
    Returns:
        Base64 encoded transaction string
    """
    serialized_tx = dumps(Signed.to_json(signed)).encode('utf-8')
    b16 = binascii.hexlify(serialized_tx)
    return base64.b64encode(b16).decode('ascii')


def sign(account: Union[Account, Subaccount], nonce: str, tx: Transaction) -> Signed:
    """
    Sign a transaction with the given account and nonce.
    
    Args:
        account: Account or Subaccount to sign with
        nonce: Unique nonce for this signature
        tx: Transaction object to sign
        
    Returns:
        Signed transaction object
        
    Raises:
        AttributeError: If the account does not support signing
    """
    tx_dict = Transaction.to_json(tx)
    msg = json.dumps([nonce, tx_dict], separators=(',', ':')).encode('utf-8')
    
    # Try to sign using sign_message first, then fall back to sign method
    # This ensures compatibility with both Account and Subaccount classes
    if hasattr(account, "sign_message"):
        signature = account.sign_message(msg)
    elif hasattr(account, "sign"):
        signature = account.sign(msg)
    else:
        raise AttributeError("Account does not have a sign or sign_message method")

    # Create signed transaction object
    signed = Signed(nonce, signature.hex(), tx, NonEmpty.from_list([account.public_key]))
    return signed
