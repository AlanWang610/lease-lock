#!/usr/bin/env python3
"""
Working Lease Graph Testnet Test

This script tests the lease graph contract on testnet with proper fees and auth.
"""

import os
import json
import hashlib
import binascii
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

load_dotenv()
rpc = SorobanServer(os.environ["SOROBAN_RPC"])
pp = Network.TESTNET_NETWORK_PASSPHRASE
contract_id = "CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I"

def generate_terms_hash(terms_dict):
    """Generate SHA-256 hash of canonical JSON terms"""
    canon = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True).encode()
    h = hashlib.sha256(canon).digest()
    return binascii.hexlify(h).decode()

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
    
    print("\nCreating Master Lease...")
    
    # 1) Create master lease with higher fee
    tx1 = TransactionBuilder(landlord_account, network_passphrase=pp, base_fee=100000) \
        .add_time_bounds(0, 300) \
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
    
    tx1.sign(landlord_kp)
    result1 = rpc.send_transaction(tx1)
    print(f"Master lease result: {result1}")
    
    if result1.status.value == "SUCCESS":
        print("SUCCESS: Master lease created!")
        
        print("\nAccepting Master Lease...")
        
        # 2) Accept the lease
        tx2 = TransactionBuilder(tenant_account, network_passphrase=pp, base_fee=100000) \
            .add_time_bounds(0, 300) \
            .append_invoke_contract_function_op(
                contract_id=contract_id,
                function_name="accept",
                parameters=[
                    scval.to_uint64(1)  # lease ID
                ]
            ).build()
        
        tx2.sign(tenant_kp)
        result2 = rpc.send_transaction(tx2)
        print(f"Accept result: {result2}")
        
        if result2.status.value == "SUCCESS":
            print("SUCCESS: Master lease accepted!")
            
            print("\nCreating Sublease...")
            
            # 3) Create sublease
            subtenant_kp = Keypair.random()
            tx3 = TransactionBuilder(tenant_account, network_passphrase=pp, base_fee=100000) \
                .add_time_bounds(0, 300) \
                .append_invoke_contract_function_op(
                    contract_id=contract_id,
                    function_name="create_sublease",
                    parameters=[
                        scval.to_uint64(1),  # parent_id
                        scval.to_address(Address(subtenant_kp.public_key)),
                        scval.to_bytes(terms_bytes),  # same terms as parent
                        scval.to_uint32(1),  # limit: max 1 direct child
                        scval.to_uint64(2000000000)  # expiry_ts: far future
                    ]
                ).build()
            
            tx3.sign(tenant_kp)
            result3 = rpc.send_transaction(tx3)
            print(f"Sublease result: {result3}")
            
            if result3.status.value == "SUCCESS":
                print("SUCCESS: Sublease created!")
                
                print("\n" + "="*50)
                print("LEASE TREE STRUCTURE")
                print("="*50)
                print("ID 1: Master Lease (Landlord -> Master Tenant)")
                print("|-- ID 2: Sublease (Master Tenant -> Subtenant)")
                print(f"    Subtenant: {subtenant_kp.public_key}")
                
                print("\nSummary:")
                print("- Created master lease (ID: 1)")
                print("- Accepted master lease")
                print("- Created sublease (ID: 2)")
                print("- Demonstrated lease graph functionality")
                
            else:
                print(f"FAILED: Sublease creation failed: {result3}")
        else:
            print(f"FAILED: Lease acceptance failed: {result2}")
    else:
        print(f"FAILED: Master lease creation failed: {result1}")
    
    print(f"\nContract ID: {contract_id}")
    print("View on Stellar Expert:")
    print(f"   https://stellar.expert/explorer/testnet/contract/{contract_id}")

if __name__ == "__main__":
    main()
