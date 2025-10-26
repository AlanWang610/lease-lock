#!/usr/bin/env python3
"""
Terms Hash Generation Example

This script demonstrates how to generate canonical JSON terms and their SHA-256 hash
for use with the lease registry contract.
"""

import json
import sys
import os

# Add the scripts directory to the path to import common
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import generate_terms_hash

def main():
    # Example lease terms matching the canonical terms.json format
    terms = {
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
    
    print("Original terms:")
    print(json.dumps(terms, indent=2))
    print()
    
    print("Canonical JSON:")
    canon = json.dumps(terms, separators=(',', ':'), sort_keys=True)
    print(canon)
    print()
    
    # Generate hash using the common utility
    terms_hash = generate_terms_hash(terms)
    print(f"Terms hash (SHA-256): {terms_hash}")
    print(f"Hash length: {len(terms_hash)} characters")
    print(f"Hash bytes: {len(terms_hash) // 2} bytes")
    
    # Verify it's deterministic
    hash2 = generate_terms_hash(terms)
    print(f"Hash is deterministic: {terms_hash == hash2}")
    
    # Show different terms produce different hash
    terms2 = {
        "currency": "USD",
        "rent_amount": "1500.00",  # Different rent amount
        "due_day": 1,
        "deposit_amount": "1200.00",
        "late_fee_policy": {"percent": 5, "grace_days": 3},
        "utilities_policy": {"electric": "tenant", "gas": "tenant", "water": "tenant"},
        "insurance_required": True,
        "lock_policy": {"auto_revoke_on_delinquent": True},
        "sublease_limit_per_node": 2
    }
    hash3 = generate_terms_hash(terms2)
    print(f"Different terms produce different hash: {terms_hash != hash3}")
    
    # Test JSON ordering invariance
    print("\nTesting JSON ordering invariance:")
    shuffled_terms = {
        "sublease_limit_per_node": 2,
        "currency": "USD",
        "insurance_required": True,
        "rent_amount": "1200.00",
        "lock_policy": {"auto_revoke_on_delinquent": True},
        "due_day": 1,
        "utilities_policy": {"electric": "tenant", "gas": "tenant", "water": "tenant"},
        "deposit_amount": "1200.00",
        "late_fee_policy": {"percent": 5, "grace_days": 3}
    }
    hash4 = generate_terms_hash(shuffled_terms)
    print(f"Shuffled keys produce same hash: {terms_hash == hash4}")

if __name__ == "__main__":
    main()
