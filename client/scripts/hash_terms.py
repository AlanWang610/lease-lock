#!/usr/bin/env python3
"""
Terms Hash Generation Utility

This script generates canonical JSON terms and their SHA-256 hash
for use with the lease registry contract.
"""

import json
import hashlib
import sys
import argparse

def terms_hash(terms_dict):
    """
    Generate SHA-256 hash of canonical JSON terms.
    
    Args:
        terms_dict: Dictionary containing lease terms
        
    Returns:
        str: Hex-encoded SHA-256 hash (64 characters)
    """
    # Create canonical JSON: sorted keys, no whitespace, UTF-8 encoding
    canon = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True).encode('utf-8')
    
    # Generate SHA-256 hash
    h = hashlib.sha256(canon).digest()
    
    # Return as hex string
    return h.hex()

def terms_hash_from_file(file_path):
    """
    Generate terms hash from a JSON file.
    
    Args:
        file_path: Path to JSON file containing terms
        
    Returns:
        str: Hex-encoded SHA-256 hash (64 characters)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        terms_dict = json.load(f)
    return terms_hash(terms_dict)

def main():
    parser = argparse.ArgumentParser(description='Generate SHA-256 hash of canonical JSON terms')
    parser.add_argument('file', help='Path to JSON file containing terms')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show canonical JSON output')
    
    args = parser.parse_args()
    
    try:
        # Generate hash
        terms_hash_hex = terms_hash_from_file(args.file)
        
        if args.verbose:
            # Load and show canonical JSON
            with open(args.file, 'r', encoding='utf-8') as f:
                terms_dict = json.load(f)
            canon_json = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True)
            print("Canonical JSON:")
            print(canon_json)
            print()
        
        print(terms_hash_hex)
        
    except FileNotFoundError:
        print(f"Error: File '{args.file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{args.file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
