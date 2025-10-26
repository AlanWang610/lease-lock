#!/usr/bin/env python3
"""
Demo: Mark Lease as Delinquent

This script demonstrates marking a lease as delinquent,
which triggers a LOCK event in the lock daemon.

Usage:
    python client/scripts/demo_mark_delinquent.py
"""

import os
import sys
from dotenv import load_dotenv
from stellar_sdk import Keypair

# Add the scripts directory to the path to import lease_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lease_api import LeaseAPI

load_dotenv(override=True)


def mark_delinquent():
    """
    Mark the leaf lease as delinquent
    """
    registry_id = os.getenv("REGISTRY_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    lessor_secret = os.getenv("LESSOR_SECRET")
    leaf_id = int(os.getenv("LEAF_ID"))
    
    # Initialize API
    api = LeaseAPI(registry_id, rpc_url)
    lessor = Keypair.from_secret(lessor_secret)
    
    print(f"\nMarking leaf lease {leaf_id} as delinquent...")
    result = api.set_delinquent(lessor, leaf_id)
    print(f"✓ Lease marked delinquent")
    print(f"  Transaction: {result}")
    return result


def main():
    print("=" * 60)
    print("DEMO: Mark Lease as Delinquent")
    print("=" * 60)
    
    mark_delinquent()
    
    print("\n" + "=" * 60)
    print("Demo complete! Check your lock daemon for LOCK event.")
    print("=" * 60)


if __name__ == "__main__":
    main()

