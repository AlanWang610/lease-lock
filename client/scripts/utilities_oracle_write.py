#!/usr/bin/env python3
"""
Utilities Oracle Write Script

This script allows writing utility readings to the utilities oracle contract.
It loads the admin keypair from environment variables and invokes the set_reading function.

Usage:
    python utilities_oracle_write.py NYC123A OCT2025 320 14 6800

Example:
    python utilities_oracle_write.py NYC123A OCT2025 320 14 6800
"""

import os
import sys
import argparse
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

# Add the scripts directory to the path to import common
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import ensure_funded

load_dotenv()

def write_utility_reading(unit: str, period: str, kwh: int, gas: int, water: int):
    """
    Write utility reading to the oracle contract
    
    Args:
        unit: Unit identifier (e.g., "NYC123A")
        period: Period identifier (e.g., "OCT2025")
        kwh: Electricity usage in kWh
        gas: Gas usage in units
        water: Water usage in units
    """
    # Load configuration
    contract_id = os.environ.get("UTILITIES_ORACLE_ID", "CDDO7X23GQ7J3KXACSIFRIY6T7MESM5EACTX7ZAHRRQZZIW2LYUPIX77")
    rpc_url = os.environ["SOROBAN_RPC"]
    network_passphrase = os.environ["NETWORK_PASSPHRASE"]
    
    # Load admin keypair
    admin_secret = os.environ["ARBITRATOR_SECRET"]
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
    
    try:
        result = rpc.send_transaction(tx)
        print(f"SUCCESS: Successfully wrote utility reading:")
        print(f"   Unit: {unit}")
        print(f"   Period: {period}")
        print(f"   Electricity: {kwh} kWh")
        print(f"   Gas: {gas} units")
        print(f"   Water: {water} units")
        print(f"   Transaction Hash: {result.hash}")
        return result
    except Exception as e:
        print(f"ERROR: Error writing utility reading: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Write utility reading to oracle contract")
    parser.add_argument("unit", help="Unit identifier (e.g., NYC123A)")
    parser.add_argument("period", help="Period identifier (e.g., OCT2025)")
    parser.add_argument("kwh", type=int, help="Electricity usage in kWh")
    parser.add_argument("gas", type=int, help="Gas usage in units")
    parser.add_argument("water", type=int, help="Water usage in units")
    
    args = parser.parse_args()
    
    # Validate inputs
    if args.kwh < 0 or args.gas < 0 or args.water < 0:
        print("ERROR: Utility values cannot be negative")
        sys.exit(1)
    
    # Write the reading
    result = write_utility_reading(args.unit, args.period, args.kwh, args.gas, args.water)
    
    if result is None:
        sys.exit(1)

if __name__ == "__main__":
    main()
