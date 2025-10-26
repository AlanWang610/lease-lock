#!/usr/bin/env python3
"""
Demo: Post Utility Reading

This script demonstrates posting a utility reading to the oracle contract.

Usage:
    python client/scripts/demo_post_reading.py
"""

import os
import sys
from dotenv import load_dotenv
from stellar_sdk import Keypair, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

# Add the scripts directory to the path to import common
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import ensure_funded

load_dotenv(override=True)


def post_reading(unit, period, kwh, gas, water):
    """
    Post utility reading to the oracle contract
    """
    contract_id = os.getenv("UTILITIES_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    network_passphrase = os.getenv("NETWORK_PASSPHRASE")
    
    # Use arbitrator as the oracle admin
    admin_secret = os.getenv("ARBITRATOR_SECRET")
    admin = Keypair.from_secret(admin_secret)
    
    # Ensure admin account is funded
    ensure_funded(admin.public_key)
    
    # Initialize RPC client
    rpc = SorobanServer(rpc_url)
    
    # Load account
    account = rpc.load_account(admin.public_key)
    
    # Build transaction
    tx = TransactionBuilder(account, network_passphrase=network_passphrase, base_fee=100) \
        .append_invoke_contract_function_op(
            contract_id=contract_id,
            function_name="set_reading",
            parameters=[
                scval.to_symbol(unit),
                scval.to_symbol(period),
                scval.to_int64(kwh),
                scval.to_int64(gas),
                scval.to_int64(water)
            ]
        ).build()
    
    # Sign and submit transaction
    tx.sign(admin)
    result = rpc.send_transaction(tx)
    
    print(f"✓ Utility reading posted:")
    print(f"   Unit: {unit}")
    print(f"   Period: {period}")
    print(f"   Electricity: {kwh} kWh")
    print(f"   Gas: {gas} units")
    print(f"   Water: {water} units")
    print(f"   Transaction: {result}")
    
    return result


def main():
    print("=" * 60)
    print("DEMO: Post Utility Reading")
    print("=" * 60)
    
    # Get parameters from environment
    unit = os.getenv("UNIT", "unit:NYC:123-A")
    period = os.getenv("PERIOD", "2025-10")
    
    # Post a sample reading
    post_reading(unit, period, 320, 14, 6800)
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

