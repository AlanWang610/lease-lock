#!/usr/bin/env python3
"""
Check account balances and contract status
"""

import os
from dotenv import load_dotenv
from stellar_sdk import Keypair, Server

load_dotenv()

def check_account_balance(secret_key, name):
    """Check account balance"""
    try:
        kp = Keypair.from_secret(secret_key)
        server = Server("https://horizon-testnet.stellar.org")
        account = server.accounts().account_id(kp.public_key).call()
        
        print(f"{name}: {kp.public_key}")
        for balance in account["balances"]:
            if balance["asset_type"] == "native":
                print(f"  XLM Balance: {balance['balance']}")
            else:
                print(f"  {balance['asset_code']}: {balance['balance']}")
        print()
    except Exception as e:
        print(f"{name} error: {e}")

def main():
    print("Account Balance Check")
    print("="*30)
    
    check_account_balance(os.environ["LANDLORD_SECRET"], "Landlord")
    check_account_balance(os.environ["TENANT_SECRET"], "Master Tenant")

if __name__ == "__main__":
    main()
