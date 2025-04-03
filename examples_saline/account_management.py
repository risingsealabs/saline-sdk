#!/usr/bin/env python3
"""
Account Management Example

This example demonstrates how to perform various account management operations
using the Saline high-level interface:
1. Create a new account
2. Load an existing account
3. Create and manage subaccounts
4. Display account information
"""

import os
from saline_sdk import Saline

NODE_URL = "http://localhost:26657"

def main():
    print("Saline SDK Account Management Example")
    print("-" * 50)
    
    saline = Saline(node_url=NODE_URL)
    
    mnemonic = saline.account.mnemonic
    print(f"Generated new wallet with mnemonic (SAVE THIS SECURELY):")
    print(f"{mnemonic}")
    print(f"Master account public key: {saline.account.public_key}")
    print("-" * 50)
    
    print("Creating subaccounts...")
    trading_account = saline.account.create_subaccount("trading")
    savings_account = saline.account.create_subaccount("savings")
    
    print(f"Trading subaccount public key: {trading_account.public_key}")
    print(f"Savings subaccount public key: {savings_account.public_key}")
    print("-" * 50)
    
    print("Loading account from mnemonic...")
    saline2 = Saline(
        node_url=NODE_URL,
        mnemonic=mnemonic
    )
    
    print(f"Loaded account public key: {saline2.account.public_key}")
    if saline2.account.public_key == saline.account.public_key:
        print("Success! Accounts match.")
    else:
        print("Error: Accounts don't match.")
    print("-" * 50)
    
    print("Listing all subaccounts:")
    
    subaccounts = saline2.account.get_all_subaccounts()
    
    print(f"Found {len(subaccounts)} subaccounts:")
    for name, subaccount in subaccounts.items():
        print(f"  - {name}: {subaccount.public_key}")
    
    if "trading" in subaccounts:
        trading = saline2.account.get_subaccount("trading")
        print(f"Retrieved trading account: {trading.public_key}")
    
    print("-" * 50)
    print("Account management operations complete!")

if __name__ == "__main__":
    main() 