#!/usr/bin/env python3
"""
Setup Test Data for Demo

This script creates test lease data and reports the IDs needed for the demo.

Usage:
    python client/scripts/demo_setup_test_data.py
"""

import os
import sys
from dotenv import load_dotenv
from stellar_sdk import Keypair

# Add the scripts directory to the path to import lease_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lease_api import LeaseAPI
from common import generate_terms_hash

# Load environment variables from config.env in the parent directory
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.env')
load_dotenv(config_path, override=True)


def setup_test_data():
    """Create test lease chain for demo"""
    
    registry_id = os.getenv("REGISTRY_ID") or os.getenv("LEASE_CONTRACT_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    
    if not registry_id:
        print("Error: REGISTRY_ID or LEASE_CONTRACT_ID not found in environment")
        print("Please set one of these in client/config.env")
        sys.exit(1)
    
    print("=" * 60)
    print("Setting up test data for demo")
    print("=" * 60)
    print(f"Contract ID: {registry_id}")
    print(f"RPC: {rpc_url}")
    
    # Initialize API
    api = LeaseAPI(registry_id, rpc_url)
    
    # Get keypairs
    landlord = Keypair.from_secret(os.getenv("LANDLORD_SECRET"))
    master = Keypair.from_secret(os.getenv("TENANT_SECRET"))
    sub1 = Keypair.random()
    
    print(f"\nKeypairs:")
    print(f"  Landlord: {landlord.public_key}")
    print(f"  Master: {master.public_key}")
    print(f"  Subtenant: {sub1.public_key}")
    
    # Define terms
    terms_dict = {
        "currency": "USD",
        "rent_amount": "1200.00",
        "due_day": 1,
        "deposit_amount": "1200.00",
        "late_fee_policy": {"percent": 5, "grace_days": 3},
        "utilities_policy": {"electric": "tenant", "gas": "tenant", "water": "tenant"},
        "insurance_required": True,
        "lock_policy": {"auto_revoke_on_delinquent": True},
        "sublease_limit_per_node": 2
    }
    
    print(f"\nCreating master lease...")
    root_id = api.create_master(
        landlord, "unitNYC123A", landlord, master,
        terms_dict, 2, 2_000_000_000
    )
    print(f"[OK] Master lease created: ID={root_id}")
    
    print(f"\nAccepting master lease...")
    api.accept(master, root_id)
    print("[OK] Master lease accepted")
    
    print(f"\nCreating sublease...")
    try:
        child_id = api.create_sublease(
            master, root_id, sub1,
            terms_dict, 1, 2_000_000_000
        )
        print(f"[OK] Sublease created: ID={child_id}")
        
        print(f"\nAccepting sublease...")
        api.accept(sub1, child_id)
        print("[OK] Sublease accepted")
        
        print(f"\nActivating sublease...")
        api.set_active(master, child_id)
        print("[OK] Sublease activated")
    except Exception as e:
        print(f"[SKIP] Sublease creation failed: {e}")
        print("Continuing with master lease only...")
    
    print(f"\nActivating master lease...")
    api.set_active(landlord, root_id)
    print("[OK] Master lease activated")
    
    print("\n" + "=" * 60)
    print("Test data setup complete!")
    print("=" * 60)
    print(f"\nUpdate your client/config.env with these values:")
    print(f"  ROOT_ID={root_id}")
    print(f"  LEAF_ID={root_id}")  # Use root_id as leaf_id since sublease failed
    print(f"\nCurrent configuration:")
    print(f"  UNIT=unitNYC123A")
    print(f"  PERIOD=2025-10")
    print(f"  LESSOR_SECRET={master.secret}")
    
    print("\nNote: You may need to update LESSOR_SECRET if you want")
    print("to use a different account as the lessor.")


if __name__ == "__main__":
    setup_test_data()

