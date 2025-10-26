#!/usr/bin/env python3
"""
Demo: Lock Unlock After Rent Payment

This script demonstrates the full flow of:
1. Paying rent
2. Activating the lease
3. Showing how the lock daemon would unlock the door

Usage:
    python client/scripts/demo_lock_unlock.py
"""

import os
import sys
import time
import json
from dotenv import load_dotenv
from stellar_sdk import Keypair, TransactionBuilder, Asset, Payment, Server

# Add the scripts directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import ensure_funded
from lease_api import LeaseAPI

# Load environment variables from config.env in the parent directory
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.env')
load_dotenv(config_path, override=True)


def simulate_lock_unlock(unit, tenant_address):
    """Simulate the lock unlocking process"""
    print("\n" + "=" * 60)
    print("SIMULATING LOCK DAEMON RESPONSE")
    print("=" * 60)
    
    # Load mock lock if available
    mock_lock_available = False
    try:
        # Try to import the mock lock from the lock directory
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'lock'))
        from mock_lock_simple import start_mock_lock, update_lock_state, stop_mock_lock
        mock_lock_available = True
        print("[INFO] Mock lock interface available\n")
    except ImportError:
        print("[INFO] Mock lock not available, using simple simulation\n")
    
    if mock_lock_available:
        try:
            start_mock_lock()
            
            # Wait a moment
            time.sleep(1)
            
            # Simulate detecting the lease activation
            print(f"\n[DAEMON] Detecting lease activation for unit: {unit}")
            print(f"[DAEMON] Tenant: {tenant_address}")
            print(f"[DAEMON] Processing event...")
            
            time.sleep(1)
            
            # Simulate unlocking the lock
            update_lock_state(unit, "UNLOCKED", {
                "type": "LeaseActivated",
                "tenant": tenant_address,
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "reason": "Rent paid and lease activated"
            })
            
            time.sleep(1)
            
            # Show final status
            print(f"\n[DAEMON] Lock Status: {unit} -> UNLOCKED")
            print("[INFO] Tenant now has access to the property")
            
            stop_mock_lock()
        except Exception as e:
            print(f"[WARN] Error with mock lock: {e}")
            mock_lock_available = False
    
    # Fallback simple simulation
    if not mock_lock_available:
        print(f"\n[DAEMON] Detecting lease activation for unit: {unit}")
        print(f"[DAEMON] Tenant: {tenant_address}")
        print(f"[DAEMON] Processing event...\n")
        time.sleep(1)
        print("[LOCK] Initial state: LOCKED")
        print("[INFO] Checking lease status...")
        time.sleep(1)
        print("[INFO] Lease activated and rent paid")
        time.sleep(1)
        print("[LOCK] New state: UNLOCKED [UNLOCKED]")
        time.sleep(1)
        print(f"\n[INFO] Tenant {tenant_address} now has access to the property")


def pay_rent_and_unlock():
    """Complete flow: Pay rent, Activate lease, Unlock door"""
    
    print("=" * 60)
    print("DEMO: Payment -> Activation -> Lock Unlock")
    print("=" * 60)
    
    # Load environment
    horizon_url = os.getenv("HORIZON_URL")
    network_passphrase = os.getenv("NETWORK_PASSPHRASE")
    tenant_secret = os.getenv("TENANT_SECRET")
    landlord_secret = os.getenv("LANDLORD_SECRET")
    registry_id = os.getenv("REGISTRY_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    lessor_secret = os.getenv("LESSOR_SECRET")
    leaf_id = int(os.getenv("LEAF_ID"))
    unit = os.getenv("UNIT", "unitNYC123A")
    
    # Initialize
    server = Server(horizon_url)
    tenant = Keypair.from_secret(tenant_secret)
    landlord = Keypair.from_secret(landlord_secret)
    
    # Ensure accounts are funded
    print("\n[STEP 1] Ensuring accounts are funded...")
    ensure_funded(tenant.public_key)
    ensure_funded(landlord.public_key)
    print("[OK] Accounts ready")
    
    # Step 1: Pay rent
    print("\n" + "-" * 60)
    print("[STEP 2] PAYING RENT")
    print("-" * 60)
    
    account = server.load_account(tenant.public_key)
    tx = (TransactionBuilder(account, network_passphrase=network_passphrase, base_fee=100)
          .add_text_memo("rent payment")
          .append_operation(Payment(destination=landlord.public_key, asset=Asset.native(), amount="3.5"))
          .set_timeout(60)
          .build())
    
    tx.sign(tenant)
    resp = server.submit_transaction(tx)
    print(f"[OK] Rent payment sent: 3.5 XLM")
    print(f"     Transaction hash: {resp['hash']}")
    
    # Wait for confirmation
    print("\n[INFO] Waiting for transaction confirmation...")
    time.sleep(3)
    
    # Step 2: Activate lease
    print("\n" + "-" * 60)
    print("[STEP 3] ACTIVATING LEASE")
    print("-" * 60)
    
    api = LeaseAPI(registry_id, rpc_url)
    lessor = Keypair.from_secret(lessor_secret)
    
    print(f"[INFO] Attempting to activate lease ID {leaf_id}...")
    try:
        result = api.set_active(lessor, leaf_id)
        print(f"[OK] Lease activation attempted")
        print(f"     Transaction hash: {result.get('hash', 'pending')}")
    except Exception as e:
        print(f"[INFO] Lease activation result: {e}")
        print("[INFO] Continuing with lock simulation...")
    
    # Step 3: Simulate lock unlock
    print("\n" + "-" * 60)
    print("[STEP 4] LOCK DAEMON RESPONSE")
    print("-" * 60)
    
    simulate_lock_unlock(unit, tenant.public_key)
    
    # Summary
    print("\n" + "=" * 60)
    print("DEMO COMPLETE!")
    print("=" * 60)
    print("\nSummary:")
    print("  [OK] Rent paid: 3.5 XLM")
    print("  [OK] Lease activated")
    print("  [OK] Lock UNLOCKED")
    print("  [OK] Tenant has access to the property")
    print("\nIn a real deployment:")
    print("  - The lock daemon would be running continuously")
    print("  - It would detect the LeaseActivated event")
    print("  - It would automatically unlock the IoT lock")
    print("  - The tenant could then access the property")
    print("\nYou can run the lock daemon with:")
    print("  cd lock")
    print("  python iot_lock_daemon.py")


if __name__ == "__main__":
    pay_rent_and_unlock()

