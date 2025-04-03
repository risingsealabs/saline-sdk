"""
BLS signature implementation for Saline SDK.

This module provides BLS signature functionality using the BLS12-381 curve,
following the IETF BLS signature standard draft v4 (basic scheme).

This implementation matches the Haskell implementation in Saline exactly:
- Uses raw message bytes for signing (no pre-hashing)
- Uses BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_ as domain parameter
- Follows the same serialization format
"""

import logging
from typing import Optional, Union
from blspy import (
    BasicSchemeMPL,
    G1Element,
    G2Element,
    PrivateKey
)

logger = logging.getLogger(__name__)



class BLS:
    """BLS signature implementation using the basic scheme."""

    PrivateKey = PrivateKey


    @staticmethod
    def _encode_point(point: G1Element) -> bytes:
        """Encode a G1 point in compressed form."""
        return bytes(point)

    @staticmethod
    def _decode_point(data: bytes) -> G1Element:
        """Decode a G1 point from compressed form."""
        return G1Element.from_bytes(data)

    @staticmethod
    def _encode_signature(sig: G2Element) -> bytes:
        """Encode a G2 signature point in compressed form."""
        return bytes(sig)

    @staticmethod
    def _decode_signature(data: bytes) -> G2Element:
        """Decode a G2 signature from compressed form."""
        return G2Element.from_bytes(data)

    @staticmethod
    def sk_to_pk(sk: Union[bytes, PrivateKey]) -> bytes:
        """
        Convert private key to public key bytes.

        Args:
            sk: Private key (bytes or PrivateKey object)

        Returns:
            bytes: Public key in compressed form

        Raises:
            ValueError: If conversion fails
        """
        try:
            # If already a PrivateKey object, use it directly
            if isinstance(sk, PrivateKey):
                pk = sk.get_g1()
            else:
                sk_obj = PrivateKey.from_bytes(sk)
                pk = sk_obj.get_g1()

            # Return compressed form
            return bytes(pk)

        except Exception as e:
            raise ValueError(f"Failed to convert private key to public key: {str(e)}")

    @staticmethod
    def sign(sk: Union[bytes, PrivateKey], message: bytes, dst: Optional[bytes] = None) -> G2Element:
        """
        Sign a message using BLS signature scheme.

        Args:
            sk: Private key (bytes or PrivateKey object)
            message: Message to sign (raw bytes, NOT pre-hashed)
            dst: Domain separation tag (default: SALINE_DOMAIN)

        Returns:
            Signature in compressed form

        Raises:
            ValueError: If signing fails

        Note:
            This matches the Haskell implementation exactly:
            - Signs raw message bytes directly (no pre-hashing)
            - Uses BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_ domain parameter
        """
        try:
            if isinstance(sk, PrivateKey):
                sk_obj = sk
            else:
                sk_obj = PrivateKey.from_bytes(sk)


            sig = BasicSchemeMPL.sign(sk_obj, message)
            return BLS._encode_signature(sig)

        except Exception as e:
            logger.error(f"Failed to sign message: {str(e)}")
            raise ValueError(f"Failed to sign message: {str(e)}")

    @staticmethod
    def verify(pk_bytes: bytes, message: bytes, signature_bytes: bytes) -> bool:
        """
        Verify a message signature using a public key.

        Args:
            pk_bytes: Public key bytes to verify with
            message: Message that was signed
            signature_bytes: Signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            pk_point = G1Element.from_bytes(pk_bytes)
            sig_point = G2Element.from_bytes(signature_bytes)
            return BasicSchemeMPL.verify(pk_point, message, sig_point)
        except Exception as e:
            logger.error(f"Signature verification error: {str(e)}")
            return False

    @staticmethod
    def aggregate_signatures(signatures: list[bytes]) -> bytes:
        """
        Aggregate multiple BLS signatures.

        Args:
            signatures: List of signatures in compressed form

        Returns:
            Aggregated signature in compressed form

        Raises:
            ValueError: If aggregation fails
        """
        try:
            sig_points = [BLS._decode_signature(sig) for sig in signatures]
            agg_sig = BasicSchemeMPL.aggregate(sig_points)
            return BLS._encode_signature(agg_sig)

        except Exception as e:
            raise ValueError(f"Failed to aggregate signatures: {str(e)}")

    @staticmethod
    def verify_aggregate(
        signature: bytes,
        messages: list[bytes],
        public_keys: list[bytes],

    ) -> bool:
        """
        Verify an aggregate signature.

        Args:
            signature: Aggregate signature in compressed form
            messages: List of original messages (raw bytes, NOT pre-hashed)
            public_keys: List of public keys in compressed form

        Returns:
            True if aggregate signature is valid

        Note:
            BasicSchemeMPL.aggregate_verify() internally uses the domain parameter
            "BLS_SIG_BLS12381G2_XMD:SHA-256_SSWU_RO_NUL_" which matches Saline's.
        """
        try:
            if len(public_keys) != len(messages):
                logger.error(f"Number of public keys ({len(public_keys)}) does not match number of messages ({len(messages)})")
                return False

            pk_points = [G1Element.from_bytes(pk) for pk in public_keys]
            sig_point = G2Element.from_bytes(signature)

            all_same_message = all(m == messages[0] for m in messages)

            if all_same_message:
                agg_pk = pk_points[0]
                for pk in pk_points[1:]:
                    agg_pk = agg_pk + pk

                return BasicSchemeMPL.verify(agg_pk, messages[0], sig_point)
            else:
                return BasicSchemeMPL.aggregate_verify(pk_points, messages, sig_point)

        except Exception as e:
            logger.error(f"Aggregate signature verification error: {e}")
            return False

    