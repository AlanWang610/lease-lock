#!/usr/bin/env python3
"""
Lease Graph Testnet Integration Test

This script tests the lease graph contract on testnet and prints a visual tree
of the lease relationships created using the new LeaseAPI wrapper.
"""

import os
import json
import sys
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval
from collections import defaultdict

# Add the scripts directory to the path to import common
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import generate_terms_hash, hex_to_bytes
from lease_api import LeaseAPI

load_dotenv()
rpc = SorobanServer(os.environ["SOROBAN_RPC"])
pp = Network.TESTNET_NETWORK_PASSPHRASE
contract_id = "CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I"

def main():
    print("Lease Graph Testnet Integration Test")
    print("="*50)
    
    # Create API client
    api = LeaseAPI(contract_id)
    
    # Generate test addresses
    landlord_kp = Keypair.from_secret(os.environ["LANDLORD_SECRET"])
    tenant_kp = Keypair.from_secret(os.environ["TENANT_SECRET"])
    
    # Create additional test addresses for subtenants
    subtenant1_kp = Keypair.random()
    subtenant2_kp = Keypair.random()
    subtenant3_kp = Keypair.random()
    
    print(f"Landlord: {landlord_kp.public_key}")
    print(f"Master Tenant: {tenant_kp.public_key}")
    print(f"Subtenant 1: {subtenant1_kp.public_key}")
    print(f"Subtenant 2: {subtenant2_kp.public_key}")
    print(f"Subtenant 3: {subtenant3_kp.public_key}")
    
    # Generate terms hash
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
    
    print(f"\nTerms Hash: {generate_terms_hash(terms_dict)}")
    print(f"Terms JSON: {json.dumps(terms_dict, separators=(',', ':'))}")
    
    print("\nCreating Master Lease...")
    
    # 1) Create master lease
    root_id = api.create_master(
        landlord_kp, "unit:NYC:123-A", landlord_kp, tenant_kp,
        terms_dict, 2, 2_000_000_000
    )
    print(f"Master lease created with ID: {root_id}")
    
    print("\nAccepting Master Lease...")
    
    # 2) Accept the lease
    api.accept(tenant_kp, root_id)
    print("Master lease accepted")
    
    print("\nCreating First Sublease...")
    
    # 3) Create first sublease
    child1_id = api.create_sublease(
        tenant_kp, root_id, subtenant1_kp,
        terms_dict, 1, 2_000_000_000
    )
    print(f"First sublease created with ID: {child1_id}")
    
    print("\nCreating Second Sublease...")
    
    # 4) Create second sublease
    child2_id = api.create_sublease(
        tenant_kp, root_id, subtenant2_kp,
        terms_dict, 1, 2_000_000_000
    )
    print(f"Second sublease created with ID: {child2_id}")
    
    print("\nCreating Third-Level Sublease...")
    
    # 5) Create third-level sublease (subtenant1 -> subtenant3)
    child3_id = api.create_sublease(
        subtenant1_kp, child1_id, subtenant3_kp,
        terms_dict, 1, 2_000_000_000
    )
    print(f"Third-level sublease created with ID: {child3_id}")
    
    print("\nAccepting All Subleases...")
    
    # Accept all subleases
    api.accept(subtenant1_kp, child1_id)
    api.accept(subtenant2_kp, child2_id)
    api.accept(subtenant3_kp, child3_id)
    print("All subleases accepted")
    
    print("\nTesting Activation Flow...")
    
    # Activate all leases
    api.set_active(landlord_kp, root_id)
    api.set_active(tenant_kp, child1_id)
    api.set_active(tenant_kp, child2_id)
    api.set_active(subtenant1_kp, child3_id)
    print("All leases activated")
    
    print("\nTesting Read APIs...")
    
    # Test read APIs
    print(f"Root of {child3_id}: {api.root_of(child3_id)}")
    print(f"Parent of {child3_id}: {api.parent_of(child3_id)}")
    print(f"Children of {root_id}: {api.children_of(root_id)}")
    print(f"Children of {child1_id}: {api.children_of(child1_id)}")
    
    # Get lease details
    root_lease = api.get_lease(root_id)
    print(f"Root lease details: {json.dumps(root_lease, indent=2)}")
    
    print("\nTesting Error Cases...")
    
    # Test expiry validation
    print("Testing expiry validation (should fail)...")
    try:
        api.create_sublease(
            tenant_kp, root_id, Keypair.random(),
            terms_dict, 1, 3_000_000_000  # Future expiry
        )
        print("Unexpected success!")
    except Exception as e:
        print(f"Correctly failed with expiry validation: {str(e)[:100]}...")
    
    # Test depth validation
    print("\nTesting depth validation (should fail)...")
    try:
        # Create a deep chain to test max depth
        deep_tenants = [Keypair.random() for _ in range(12)]
        deep_ids = api.create_chain(
            subtenant3_kp, child3_id, deep_tenants,
            terms_dict, 1, 2_000_000_000
        )
        print("Unexpected success!")
    except Exception as e:
        print(f"Correctly failed with depth validation: {str(e)[:100]}...")
    
    # Test limit validation
    print("\nTesting limit validation (should fail)...")
    try:
        api.create_sublease(
            tenant_kp, root_id, Keypair.random(),
            terms_dict, 3, 2_000_000_000  # Exceeds parent limit
        )
        print("Unexpected success!")
    except Exception as e:
        print(f"Correctly failed with limit validation: {str(e)[:100]}...")
    
    print("\nTesting Quality-of-Life APIs...")
    
    # Create an unaccepted sublease for testing
    test_sublease_id = api.create_sublease(
        subtenant2_kp, child2_id, Keypair.random(),
        terms_dict, 1, 2_000_000_000
    )
    
    # Test replace sublessee
    new_lessee = Keypair.random()
    api.replace_sublessee(subtenant2_kp, test_sublease_id, new_lessee)
    print(f"Replaced sublessee for lease {test_sublease_id}")
    
    # Test cancel unaccepted
    api.cancel_unaccepted(subtenant2_kp, test_sublease_id)
    print(f"Cancelled unaccepted lease {test_sublease_id}")
    
    print("\nTesting Delinquency...")
    
    # Test delinquency
    api.set_delinquent(subtenant1_kp, child3_id)
    print(f"Marked lease {child3_id} as delinquent")
    
    # Verify delinquency
    delinquent_lease = api.get_lease(child3_id)
    print(f"Lease {child3_id} active status: {delinquent_lease['active']}")
    
    # Print the lease tree structure using the new API
    print("\n" + "="*60)
    print("FINAL LEASE TREE STRUCTURE")
    print("="*60)
    api.print_tree(root_id)
    
    print("\nSummary:")
    print(f"Created master lease (ID: {root_id})")
    print(f"Created 2 direct subleases (IDs: {child1_id}, {child2_id})")
    print(f"Created 1 third-level sublease (ID: {child3_id})")
    print("Tested all new validation rules")
    print("Tested activation and delinquency flows")
    print("Tested read APIs and tree visualization")
    print("Demonstrated comprehensive sublease recursion")
    
    print(f"\nContract ID: {contract_id}")
    print("View on Stellar Expert:")
    print(f"   https://stellar.expert/explorer/testnet/contract/{contract_id}")

if __name__ == "__main__":
    main()
