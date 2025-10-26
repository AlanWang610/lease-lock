#!/usr/bin/env python3
"""
Demo: Pay Rent and Activate Lease

This script demonstrates:
1. Paying rent (XLM) from tenant to landlord
2. Activating the lease (which triggers UNLOCK event)

Usage:
    python client/scripts/demo_pay_rent.py
"""

import os
import sys
import time
from dotenv import load_dotenv
from stellar_sdk import Server, Keypair, TransactionBuilder, Asset, Payment

# Add the scripts directory to the path to import common and lease_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import ensure_funded
from lease_api import LeaseAPI

# Load environment variables from config.env in the parent directory
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.env')
load_dotenv(config_path, override=True)


def pay_rent(amount="3.5"):
    """
    Send rent payment from tenant to landlord
    """
    horizon_url = os.getenv("HORIZON_URL")
    network_passphrase = os.getenv("NETWORK_PASSPHRASE")
    tenant_secret = os.getenv("TENANT_SECRET")
    landlord_secret = os.getenv("LANDLORD_SECRET")
    
    server = Server(horizon_url)
    tenant = Keypair.from_secret(tenant_secret)
    landlord = Keypair.from_secret(landlord_secret)
    
    # Ensure both accounts are funded
    ensure_funded(tenant.public_key)
    ensure_funded(landlord.public_key)
    
    # Load tenant account
    account = server.load_account(tenant.public_key)
    
    # Build payment transaction
    tx = (TransactionBuilder(account, network_passphrase=network_passphrase, base_fee=100)
          .add_text_memo("rent")
          .append_operation(Payment(destination=landlord.public_key, asset=Asset.native(), amount=amount))
          .set_timeout(60)
          .build())
    
    tx.sign(tenant)
    resp = server.submit_transaction(tx)
    print(f"[OK] Payment sent: {amount} XLM")
    print(f"  Transaction hash: {resp['hash']}")
    return resp['hash']


def activate_leaf():
    """
    Activate the leaf lease (after payment)
    """
    registry_id = os.getenv("REGISTRY_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    lessor_secret = os.getenv("LESSOR_SECRET")
    leaf_id = int(os.getenv("LEAF_ID"))
    
    # Initialize API
    api = LeaseAPI(registry_id, rpc_url)
    lessor = Keypair.from_secret(lessor_secret)
    
    # Set the lease to active
    print(f"\nActivating leaf lease {leaf_id}...")
    result = api.set_active(lessor, leaf_id)
    print(f"[OK] Lease activated")
    print(f"  Transaction: {result}")
    return result


def main():
    print("=" * 60)
    print("DEMO: Payment + Activation")
    print("=" * 60)
    
    # Step 1: Pay rent
    print("\nStep 1: Paying rent...")
    pay_rent("3.5")
    
    # Wait for transaction to be confirmed
    print("\nWaiting for transaction confirmation...")
    time.sleep(3)
    
    # Step 2: Activate lease
    print("\nStep 2: Activating lease...")
    activate_leaf()
    
    print("\n" + "=" * 60)
    print("Demo complete! Check your lock daemon for UNLOCK event.")
    print("=" * 60)


if __name__ == "__main__":
    main()

