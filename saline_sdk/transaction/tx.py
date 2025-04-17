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

def tx_is_accepted(result):
    """
    Determine if a Tendermint transaction was accepted.

    A transaction is considered accepted if both 'check_tx' and 'deliver_tx'
    phases have a 'code' of 0, indicating success.

    check_tx -> pre-flight - transaction is rejectd
    deliver_tx -> state changed - Transaction is recorded with failure status

    Parameters:
        result (dict): The transaction result dictionary containing 'check_tx'
                       and 'deliver_tx' entries.

    Returns:
        bool: True if both phases succeeded; False otherwise.
    """
    return result['check_tx']['code'] == 0 and result['deliver_tx']['code'] == 0


def print_tx_errors(result, label="Transaction"):
    """
    Print error details from a Tendermint transaction result.

    This function checks the 'check_tx' and 'deliver_tx' phases of a transaction
    result. If either phase has a non-zero 'code', it prints the phase, error code,
    and attempts to decode the 'data' field from Base64 to provide a human-readable
    error message.

    Parameters:
        result (dict): The transaction result dictionary containing 'check_tx'
                       and 'deliver_tx' entries.
        label (str): A label to identify the transaction in the output.
                     Defaults to "Transaction".

    Returns:
        None
    """
    import base64
    for phase in ['check_tx', 'deliver_tx']:
        tx = result.get(phase, {})
        code = tx.get('code', 0)
        if code != 0:
            print(f"{label} - {phase.upper()} failed with code {code}")
            data = tx.get('data')
            if data:
                try:
                    # Decode Base64-encoded data
                    decoded_bytes = base64.b64decode(data)
                    decoded_message = decoded_bytes.decode('utf-8', errors='replace')
                    print("Decoded message:")
                    print(decoded_message)
                except Exception as e:
                    print(f"Failed to decode message: {e}")
            else:
                print("No data field to decode.")
