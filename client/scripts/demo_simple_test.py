#!/usr/bin/env python3
"""
Simple Demo Test - Just verify we can activate an existing lease

Usage:
    python client/scripts/demo_simple_test.py
"""

import os
import sys
from dotenv import load_dotenv
from stellar_sdk import Keypair

# Add the scripts directory to the path to import lease_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lease_api import LeaseAPI

# Load environment variables from config.env in the parent directory
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.env')
load_dotenv(config_path, override=True)


def main():
    """Simple test to verify LeaseAPI works"""
    
    registry_id = os.getenv("REGISTRY_ID") or os.getenv("LEASE_CONTRACT_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    leaf_id = int(os.getenv("LEAF_ID", "1"))
    
    print("=" * 60)
    print("Simple Demo Test")
    print("=" * 60)
    print(f"Contract ID: {registry_id}")
    print(f"RPC: {rpc_url}")
    print(f"Leaf ID: {leaf_id}")
    
    if not registry_id:
        print("Error: No contract ID found")
        sys.exit(1)
    
    # Initialize API
    api = LeaseAPI(registry_id, rpc_url)
    
    # Try to get the lease to verify it exists
    print(f"\nQuerying lease {leaf_id}...")
    try:
        lease = api.get_lease(leaf_id)
        print(f"[OK] Lease found:")
        print(f"  ID: {lease['id']}")
        print(f"  Unit: {lease['unit']}")
        print(f"  Lessor: {lease['lessor']}")
        print(f"  Lessee: {lease['lessee']}")
        print(f"  Active: {lease['active']}")
        print(f"  Accepted: {lease['accepted']}")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        print("\nThis means the lease doesn't exist yet.")
        print("You need to either:")
        print("1. Create a lease first, or")
        print("2. Update LEAF_ID to an existing lease ID")
        sys.exit(1)


if __name__ == "__main__":
    main()

