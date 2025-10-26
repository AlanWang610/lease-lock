#!/usr/bin/env python3
"""
Demo: Split Utilities Among Active Leases

This script demonstrates:
1. Reading utility totals from oracle
2. Finding all active leaf leases in the tree
3. Splitting costs equally among active leaves
4. Displaying per-lease allocation

Usage:
    python client/scripts/demo_split_utilities.py
"""

import os
import sys
from dotenv import load_dotenv
from stellar_sdk import SorobanServer, Keypair, TransactionBuilder
from stellar_sdk import scval

# Add the scripts directory to the path to import lease_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from lease_api import LeaseAPI

# Load environment variables from config.env in the parent directory
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.env')
load_dotenv(config_path, override=True)


def get_utility_reading(unit, period):
    """
    Read utility totals from oracle
    """
    contract_id = os.getenv("UTILITIES_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    network_passphrase = os.getenv("NETWORK_PASSPHRASE")
    
    rpc = SorobanServer(rpc_url)
    
    # Load a dummy account for simulation
    admin_secret = os.getenv("ARBITRATOR_SECRET")
    admin = Keypair.from_secret(admin_secret)
    
    # Load account
    account = rpc.load_account(admin.public_key)
    
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
    
    # Check if we have results
    if not result.results or not result.results[0].xdr:
        raise Exception("No utility data found for this unit/period")
    
    # Parse the result using XDR decoding
    from stellar_sdk import xdr
    xdr_obj = xdr.SCVal.from_xdr(result.results[0].xdr)
    
    # The result should be a vec
    if not xdr_obj.vec or not xdr_obj.vec.scvec:
        raise Exception("Invalid result format from utilities oracle")
    
    reading_data = xdr_obj.vec.scvec
    
    reading = {
        "unit": unit,
        "period": period,
        "kwh": int(reading_data[0].i64) if reading_data[0].i64 else 0,
        "gas": int(reading_data[1].i64) if reading_data[1].i64 else 0,
        "water": int(reading_data[2].i64) if reading_data[2].i64 else 0
    }
    
    return reading


def find_active_leaf_leases(tree_rows):
    """
    Find all active leaf leases (active=True and no children)
    
    Args:
        tree_rows: List of (id, parent, lessee, depth, active) tuples
        
    Returns:
        List of active leaf lease tuples
    """
    # Build a map of node_id -> has_children
    all_ids = set(id_val for (id_val, _, _, _, _) in tree_rows)
    parent_ids = set(parent for (_, parent, _, _, _) in tree_rows if parent is not None)
    
    # Active leaves: active=True AND not a parent of any node
    active_leaves = []
    for (node_id, parent, lessee, depth, active) in tree_rows:
        if active and node_id not in parent_ids:
            active_leaves.append((node_id, parent, lessee, depth, active))
    
    return active_leaves


def split_utilities(unit, period, root_id):
    """
    Main function to split utility costs
    """
    registry_id = os.getenv("REGISTRY_ID")
    rpc_url = os.getenv("SOROBAN_RPC")
    
    # Initialize API
    api = LeaseAPI(registry_id, rpc_url)
    
    print(f"\nReading utility data for {unit} - {period}...")
    
    # Read utility totals
    try:
        reading = get_utility_reading(unit, period)
        kwh = reading['kwh']
        gas = reading['gas']
        water = reading['water']
        
        print(f"[OK] Utility totals:")
        print(f"   Electricity: {kwh} kWh")
        print(f"   Gas: {gas} units")
        print(f"   Water: {water} units")
        
    except Exception as e:
        print(f"[SKIP] Error reading utility data: {e}")
        print("[INFO] Using mock data for demonstration...")
        # Use mock data for demo purposes
        kwh = 1500
        gas = 120
        water = 4000
        print(f"[OK] Using mock utility totals:")
        print(f"   Electricity: {kwh} kWh")
        print(f"   Gas: {gas} units")
        print(f"   Water: {water} units")
    
    # Get full lease tree
    print(f"\nGetting lease tree from root {root_id}...")
    try:
        tree_rows = api.get_full_tree(root_id, include_inactive=False)
        print(f"[OK] Found {len(tree_rows)} total active nodes")
        
    except Exception as e:
        print(f"[ERROR] Error getting lease tree: {e}")
        return
    
    # Find active leaf leases
    active_leaves = find_active_leaf_leases(tree_rows)
    
    if not active_leaves:
        print("\n[ERROR] No active leaf leases found!")
        return
    
    n = len(active_leaves)
    print(f"\n[OK] Found {n} active leaf lease(s)")
    
    # Calculate equal split
    share_kwh = kwh // n
    share_gas = gas // n
    share_water = water // n
    
    # Display results
    print("\n" + "=" * 70)
    print(f"Utility Cost Split Results")
    print("=" * 70)
    print(f"Period: {period}")
    print(f"Unit: {unit}")
    print(f"Total usage: {kwh} kWh, {gas} gas, {water} water")
    print(f"Split among {n} active leaf lease(s)")
    print("=" * 70)
    
    for idx, (lease_id, parent, lessee, depth, active) in enumerate(active_leaves, 1):
        print(f"\nLease {idx}:")
        print(f"  ID: {lease_id}")
        print(f"  Lessee: {lessee}")
        print(f"  Depth: {depth}")
        print(f"  Share:")
        print(f"    - Electricity: {share_kwh} kWh")
        print(f"    - Gas: {share_gas} units")
        print(f"    - Water: {share_water} units")
    
    # Calculate per-unit costs (using demo rates)
    rates = {
        "electricity": 0.12,  # $0.12 per kWh
        "gas": 1.50,           # $1.50 per unit
        "water": 0.008         # $0.008 per gallon
    }
    
    total_electricity_cost = kwh * rates['electricity']
    total_gas_cost = gas * rates['gas']
    total_water_cost = water * rates['water']
    total_cost = total_electricity_cost + total_gas_cost + total_water_cost
    cost_per_lease = total_cost / n
    
    print("\n" + "=" * 70)
    print("Cost Summary (using demo rates):")
    print("=" * 70)
    print(f"  Electricity: {kwh} kWh × ${rates['electricity']:.3f} = ${total_electricity_cost:.2f}")
    print(f"  Gas: {gas} units × ${rates['gas']:.2f} = ${total_gas_cost:.2f}")
    print(f"  Water: {water} units × ${rates['water']:.3f} = ${total_water_cost:.2f}")
    print(f"  Total: ${total_cost:.2f}")
    print(f"  Per Lease ({n} active): ${cost_per_lease:.2f}")
    print("=" * 70)


def main():
    print("=" * 60)
    print("DEMO: Split Utilities")
    print("=" * 60)
    
    # Get parameters from environment
    unit = os.getenv("UNIT", "unit:NYC:123-A")
    period = os.getenv("PERIOD", "2025-10")
    root_id = int(os.getenv("ROOT_ID", "1"))
    
    split_utilities(unit, period, root_id)
    
    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()

