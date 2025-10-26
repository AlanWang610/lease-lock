#!/usr/bin/env python3
"""
Simple Lease Graph Testnet Test

This script tests the lease graph contract on testnet with error debugging.
"""

import os
import json
import hashlib
import binascii
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval
from stellar_sdk import xdr

load_dotenv()
rpc = SorobanServer(os.environ["SOROBAN_RPC"])
pp = Network.TESTNET_NETWORK_PASSPHRASE
contract_id = "CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I"

def generate_terms_hash(terms_dict):
    """Generate SHA-256 hash of canonical JSON terms"""
    canon = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True).encode()
    h = hashlib.sha256(canon).digest()
    return binascii.hexlify(h).decode()

def decode_error_result(error_result_xdr):
    """Decode error result XDR to get more details"""
    try:
        error_result = xdr.TransactionResult.from_xdr(error_result_xdr)
        return str(error_result)
    except Exception as e:
        return f"Could not decode error: {e}"

def main():
    print("Lease Graph Testnet Test")
    print("="*40)
    
    # Generate test addresses
    landlord_kp = Keypair.from_secret(os.environ["LANDLORD_SECRET"])
    tenant_kp = Keypair.from_secret(os.environ["TENANT_SECRET"])
    
    print(f"Landlord: {landlord_kp.public_key}")
    print(f"Master Tenant: {tenant_kp.public_key}")
    
    # Generate terms hash
    terms_dict = {
        "rent": "500.00",
        "due_day": 1,
        "notice_days": 30,
        "penalty": "0.02"
    }
    terms_hash_hex = generate_terms_hash(terms_dict)
    terms_bytes = bytes.fromhex(terms_hash_hex)
    
    print(f"Terms Hash: {terms_hash_hex}")
    
    # Load accounts
    landlord_account = rpc.load_account(landlord_kp.public_key)
    tenant_account = rpc.load_account(tenant_kp.public_key)
    
    print("\nTesting contract info first...")
    try:
        # Get contract info
        contract_info = rpc.get_contract_data(contract_id)
        print(f"Contract exists: {contract_info is not None}")
    except Exception as e:
        print(f"Contract info error: {e}")
    
    print("\nCreating Master Lease...")
    
    # 1) Create master lease
    tx1 = TransactionBuilder(landlord_account, network_passphrase=pp, base_fee=100) \
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="create_master",
            parameters=[
                scval.to_symbol("unit"),
                scval.to_address(Address(landlord_kp.public_key)),
                scval.to_address(Address(tenant_kp.public_key)),
                scval.to_bytes(terms_bytes),
                scval.to_uint32(2),  # limit: max 2 direct children
                scval.to_uint64(2000000000)  # expiry_ts: far future
            ]
        ).build()
    
    # Simulate first to see what happens
    print("Simulating transaction...")
    try:
        sim_result = rpc.simulate_transaction(tx1)
        print(f"Simulation result: {sim_result}")
    except Exception as e:
        print(f"Simulation error: {e}")
    
    tx1.sign(landlord_kp)
    result1 = rpc.send_transaction(tx1)
    print(f"Transaction result: {result1}")
    
    if hasattr(result1, 'error_result_xdr') and result1.error_result_xdr:
        print(f"Error details: {decode_error_result(result1.error_result_xdr)}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    main()
