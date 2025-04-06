#!/usr/bin/env python3

import hashlib
import hmac
from typing import List

# Constants as per EIP-2333
HKDF_SALT = b"BLS-SIG-KEYGEN-SALT-"
# BLS12-381 curve order
r = 52435875175126190479447740508185965837690552500527637822603658699938581184513

DEBUG = False

def debug_print(*args, **kwargs):
    """Helper function for debug printing"""
    if DEBUG:
        print(*args, **kwargs)

def hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """HKDF-Extract (RFC5869) using SHA-256."""
    if not salt:
        salt = bytes([0] * hashlib.sha256().digest_size)
    h = hmac.HMAC(salt, digestmod=hashlib.sha256)
    h.update(ikm)
    result = h.digest()
    debug_print(f"DEBUG: hkdf_extract: salt: {salt.hex()}, ikm: {ikm.hex()}, result: {result.hex()}")
    return result

def hkdf_expand(prk: bytes, info: bytes, length: int = 32) -> bytes:
    """HKDF-Expand (RFC5869) using SHA-256."""
    hash_len = hashlib.sha256().digest_size
    n = (length + hash_len - 1) // hash_len
    if n > 255:
        raise ValueError("Cannot expand to more than 255 blocks")
    
    t = b""
    okm = b""
    for i in range(1, n + 1):
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        debug_print(f"DEBUG: hkdf_expand: iteration {i}, t: {t.hex()}")
        okm += t
    return okm[:length]

def derive_master_SK(seed: bytes) -> bytes:
    """Derive master secret key from seed."""
    input_bytes = seed + b"\x00"  # Append trailing zero per spec
    salt = HKDF_SALT
    info = b"\x00\x30"  # 48 bytes in big-endian
    
    sk_int = 0
    iteration = 0
    while sk_int == 0:
        iteration += 1
        salt = hashlib.sha256(salt).digest()
        debug_print(f"[Master] Iteration {iteration}:")
        debug_print(f"  Salt: {salt.hex()}")
        prk = hkdf_extract(salt, input_bytes)
        okm = hkdf_expand(prk, info, 48)
        sk_int = int.from_bytes(okm, "big") % r
        debug_print(f"  OKM: {okm.hex()}")
        debug_print(f"  SK (int): {hex(sk_int)}")
    
    # Return in big-endian format (I2OSP)
    return sk_int.to_bytes(32, "big")

def parent_SK_to_lamport_PK(parent_SK: bytes, index: int) -> bytes:
    """Generate compressed Lamport public key from parent SK."""
    # parent_SK is already in big-endian format (I2OSP)
    ikm = parent_SK
    salt = index.to_bytes(4, "big")  # I2OSP(index, 4)
    
    debug_print(f"DEBUG: parent_SK_to_lamport_PK:")
    debug_print(f"  parent_SK (big-endian): {parent_SK.hex()}")
    debug_print(f"  ikm (big-endian): {ikm.hex()}")
    debug_print(f"  index: {index}")
    debug_print(f"  salt: {salt.hex()}")
    
    # Step 1: Generate first set of Lamport private keys using IKM_to_lamport_SK
    prk_0 = hkdf_extract(salt, ikm)
    lamport_0 = hkdf_expand(prk_0, b"", 32 * 255)
    
    # Step 2: Generate second set using NOT of ikm
    not_ikm = bytes(~b & 0xFF for b in ikm)
    debug_print(f"  not_ikm: {not_ikm.hex()}")
    prk_1 = hkdf_extract(salt, not_ikm)
    lamport_1 = hkdf_expand(prk_1, b"", 32 * 255)
    
    # Step 3: Split into blocks and hash each block
    lamport_0_blocks = [lamport_0[i*32:(i+1)*32] for i in range(255)]
    lamport_1_blocks = [lamport_1[i*32:(i+1)*32] for i in range(255)]
    
    # Step 4: Hash each block with SHA-256
    hashed_0 = []
    hashed_1 = []
    for i in range(255):
        h0 = hashlib.sha256(lamport_0_blocks[i]).digest()
        h1 = hashlib.sha256(lamport_1_blocks[i]).digest()
        hashed_0.append(h0)
        hashed_1.append(h1)
        debug_print(f"  Block {i:3d}: hash0={h0.hex()}, hash1={h1.hex()}")

    # Step 5: Concatenate all hashes in order (lamport_0 then lamport_1) and compress
    all_hashes = b"".join(hashed_0 + hashed_1)
    lamport_PK = hashlib.sha256(all_hashes).digest()
    debug_print(f"DEBUG: lamport_PK: {lamport_PK.hex()}")
    return lamport_PK

def derive_child_SK(parent_SK: bytes, index: int) -> bytes:
    """
    Derive a child secret key from a parent secret key and index.
    parent_SK is in big-endian format (I2OSP).
    """
    # Debug info
    debug_print(f"DEBUG: derive_child_SK - parent_SK: {parent_SK.hex()}, index: {index}")
    
    # Generate Lamport PK
    lamport_PK = parent_SK_to_lamport_PK(parent_SK, index)
    debug_print(f"DEBUG: lamport_PK: {lamport_PK.hex()}")
    
    # Derive child SK using HKDF
    input_bytes = lamport_PK + b"\x00"  # Append trailing zero per spec
    salt = HKDF_SALT
    info = b"\x00\x30"  # 48 bytes in big-endian
    
    sk_int = 0
    iteration = 0
    while sk_int == 0:
        iteration += 1
        salt = hashlib.sha256(salt).digest()
        debug_print(f"[Child] Deriving key:")
        debug_print(f"  Input bytes: {input_bytes.hex()}")
        debug_print(f"  Salt: {salt.hex()}")
        debug_print(f"  Info: {info.hex()}")
        prk = hkdf_extract(salt, input_bytes)
        okm = hkdf_expand(prk, info, 48)  # Use 48 bytes for the OKM
        sk_int = int.from_bytes(okm, "big") % r
        debug_print(f"  OKM: {okm.hex()}")
        debug_print(f"  SK (int): {hex(sk_int)}")
        debug_print(f"  SK (decimal): {sk_int}")
        debug_print(f"  Result (big-endian): {sk_int.to_bytes(32, 'big').hex()}")
    
    # Return in big-endian format (I2OSP)
    return sk_int.to_bytes(32, "big")

def derive_key_from_path(seed: bytes, path: str = "m/0") -> bytes:
    """
    Derive a key from a seed and path.
    Path format: "m/0" for first child of master key.
    """
    # Validate the path
    if not path.startswith("m/"):
        raise ValueError("Path must start with 'm/'")
    
    # If path is just "m", this is a special case for the master key
    if path == "m":
        return derive_master_SK(seed)
        
    # Validate path components
    path_components = path.split("/")
    
    # Check that path has at least 3 segments, for example m/coin_type/account
    if len(path_components) < 3:
        raise ValueError(f"Path too short: {path} (must have at least coin_type and account components)")
    
    # Check that path doesn't have too many segments (BIP44 has at most 5 components including 'm')
    if len(path_components) > 6:
        raise ValueError(f"Path too deep: {path} (maximum 5 path segments after 'm/')")
    
    # Validate that each component is numeric except for the first 'm'
    for component in path_components[1:]:
        # Remove any hardened key notation (')
        component = component.rstrip("'")
        if not component.isdigit():
            raise ValueError(f"Path component '{component}' is not numeric")
    
    # Get master key
    sk = derive_master_SK(seed)
    debug_print(f"DEBUG: Master SK (big-endian): {sk.hex()}")
    
    # If path is just "m", return master key (already handled above but kept for clarity)
    if path == "m":
        return sk
    
    # Process each index in path
    indices = []
    for comp in path_components[1:]:
        idx = int(comp.rstrip("'"))  # Remove quote if present
        indices.append(idx)
    
    debug_print(f"DEBUG: Indices for path {path}: {indices}")
    for idx in indices:
        sk = derive_child_SK(sk, idx)
        debug_print(f"DEBUG: Derived key at m/{idx} (big-endian): {sk.hex()}")
    
    return sk

def main():
    # Test Case 0 from EIP-2333
    seed = bytes.fromhex("33cf293da195153012ca09209c08e5c515a74261e0cb9621d99fe36022c5db81d6262197869c44c1cb65e28891bf822cb9fc9cbe0be976840c72e9f5d564f867")
    
    # Derive master key
    master_sk = derive_master_SK(seed)
    print(f"Seed: {seed.hex()}")
    print(f"Master SK (big-endian): {master_sk.hex()}")
    
    # Derive key at path "m/0"
    derived_key = derive_key_from_path(seed, "m/0")
    print(f"Derived key at m/0 (big-endian): {derived_key.hex()}")

if __name__ == "__main__":
    DEBUG = True  # Enable debug prints for main execution
    main() 