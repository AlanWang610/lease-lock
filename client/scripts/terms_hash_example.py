#!/usr/bin/env python3
"""
Terms Hash Generation Example

This script demonstrates how to generate canonical JSON terms and their SHA-256 hash
for use with the lease registry contract.
"""

import json
import hashlib
import binascii

def generate_terms_hash(terms_dict):
    """
    Generate SHA-256 hash of canonical JSON terms.
    
    Args:
        terms_dict: Dictionary containing lease terms
        
    Returns:
        str: Hex-encoded SHA-256 hash (64 characters)
    """
    # Create canonical JSON: sorted keys, no whitespace
    canon = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True).encode()
    
    # Generate SHA-256 hash
    h = hashlib.sha256(canon).digest()
    
    # Return as hex string
    return binascii.hexlify(h).decode()

def main():
    # Example lease terms
    terms = {
        "rent": "500.00",
        "due_day": 1,
        "notice_days": 30,
        "penalty": "0.02"
    }
    
    print("Original terms:")
    print(json.dumps(terms, indent=2))
    print()
    
    print("Canonical JSON:")
    canon = json.dumps(terms, separators=(',', ':'), sort_keys=True)
    print(canon)
    print()
    
    # Generate hash
    terms_hash = generate_terms_hash(terms)
    print(f"Terms hash (SHA-256): {terms_hash}")
    print(f"Hash length: {len(terms_hash)} characters")
    print(f"Hash bytes: {len(terms_hash) // 2} bytes")
    
    # Verify it's deterministic
    hash2 = generate_terms_hash(terms)
    print(f"Hash is deterministic: {terms_hash == hash2}")
    
    # Show different terms produce different hash
    terms2 = {
        "rent": "600.00",  # Different rent
        "due_day": 1,
        "notice_days": 30,
        "penalty": "0.02"
    }
    hash3 = generate_terms_hash(terms2)
    print(f"Different terms produce different hash: {terms_hash != hash3}")

if __name__ == "__main__":
    main()
