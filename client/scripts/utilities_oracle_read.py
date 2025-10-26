#!/usr/bin/env python3
"""
Utilities Oracle Read Script

This script allows reading utility readings from the utilities oracle contract.
It queries the get_reading function and displays the results in JSON format.

Usage:
    python utilities_oracle_read.py NYC123A OCT2025

Example:
    python utilities_oracle_read.py NYC123A OCT2025
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

load_dotenv()

def read_utility_reading(unit: str, period: str):
    """
    Read utility reading from the oracle contract
    
    Args:
        unit: Unit identifier (e.g., "NYC123A")
        period: Period identifier (e.g., "OCT2025")
        
    Returns:
        dict: Reading data with kwh, gas, water values
    """
    # Load configuration
    contract_id = os.environ.get("UTILITIES_ORACLE_ID", "CDDO7X23GQ7J3KXACSIFRIY6T7MESM5EACTX7ZAHRRQZZIW2LYUPIX77")
    rpc_url = os.environ["SOROBAN_RPC"]
    network_passphrase = os.environ["NETWORK_PASSPHRASE"]
    
    # Load a dummy account for simulation
    admin_secret = os.environ["ARBITRATOR_SECRET"]
    admin = Keypair.from_secret(admin_secret)
    
    # Initialize RPC client
    rpc = SorobanServer(rpc_url)
    
    # Load account
    account = rpc.load_account(admin.public_key)
    
    try:
        # Query the contract
        result = rpc.simulate_transaction(
            TransactionBuilder(account, network_passphrase=network_passphrase, base_fee=100)
            .append_invoke_contract_function_op(
                contract_id=contract_id,
                function_name="get_reading",
                parameters=[
                    scval.to_symbol(unit),
                    scval.to_symbol(period)
                ]
            ).build()
        )
        
        # Parse the result
        reading_data = result.results[0].xdr.scval.obj.vec.scvec
        
        reading = {
            "unit": unit,
            "period": period,
            "kwh": int(reading_data[0].obj.i64),
            "gas": int(reading_data[1].obj.i64),
            "water": int(reading_data[2].obj.i64)
        }
        
        return reading
        
    except Exception as e:
        print(f"ERROR: Error reading utility reading: {e}")
        return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Read utility reading from oracle contract")
    parser.add_argument("unit", help="Unit identifier (e.g., NYC123A)")
    parser.add_argument("period", help="Period identifier (e.g., OCT2025)")
    parser.add_argument("--format", choices=["json", "pretty"], default="pretty", 
                      help="Output format (default: pretty)")
    
    args = parser.parse_args()
    
    # Read the data
    reading = read_utility_reading(args.unit, args.period)
    
    if reading is None:
        sys.exit(1)
    
    # Display results
    if args.format == "json":
        print(json.dumps(reading, indent=2))
    else:
        print(f"Utility Reading for {reading['unit']} - {reading['period']}")
        print("=" * 50)
        print(f"Electricity: {reading['kwh']} kWh")
        print(f"Gas: {reading['gas']} units")
        print(f"Water: {reading['water']} units")
        print("=" * 50)

if __name__ == "__main__":
    main()
