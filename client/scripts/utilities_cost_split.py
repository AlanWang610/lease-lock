#!/usr/bin/env python3
"""
Utilities Cost Split Script

This script integrates with the lease registry to find all active leaf leases for a unit
and splits utility costs equally among them. It demonstrates the off-chain cost splitting
logic that would be used for billing.

Usage:
    python utilities_cost_split.py NYC123A OCT2025

Example:
    python utilities_cost_split.py NYC123A OCT2025
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any
from dotenv import load_dotenv
from stellar_sdk import SorobanServer
from stellar_sdk import scval

# Add the scripts directory to the path to import common and lease_api
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import ensure_funded
from lease_api import LeaseAPI

load_dotenv()

def get_active_leaf_leases(lease_api: LeaseAPI, root_id: int) -> List[Dict[str, Any]]:
    """
    Get all active leaf leases (leases with no children) from a lease tree
    
    Args:
        lease_api: LeaseAPI instance
        root_id: Root lease ID
        
    Returns:
        List of active leaf lease dictionaries
    """
    def find_leaves(node_id: int) -> List[Dict[str, Any]]:
        lease = lease_api.get_lease(node_id)
        children = lease_api.children_of(node_id)
        
        # If no children, this is a leaf
        if not children:
            return [lease] if lease['active'] else []
        
        # Recursively find leaves from children
        leaves = []
        for child_id in children:
            leaves.extend(find_leaves(child_id))
        
        return leaves
    
    return find_leaves(root_id)

def calculate_cost_split(reading: Dict[str, Any], active_leases: List[Dict[str, Any]], 
                        rates: Dict[str, float] = None) -> List[Dict[str, Any]]:
    """
    Calculate cost split among active leases
    
    Args:
        reading: Utility reading data
        active_leases: List of active leaf leases
        rates: Optional utility rates (default: demo rates)
        
    Returns:
        List of cost breakdowns per lease
    """
    if not active_leases:
        return []
    
    # Default demo rates (in USD per unit)
    if rates is None:
        rates = {
            "electricity": 0.12,  # $0.12 per kWh
            "gas": 1.50,          # $1.50 per unit
            "water": 0.008        # $0.008 per unit
        }
    
    # Calculate total costs
    total_electricity_cost = reading['kwh'] * rates['electricity']
    total_gas_cost = reading['gas'] * rates['gas']
    total_water_cost = reading['water'] * rates['water']
    total_cost = total_electricity_cost + total_gas_cost + total_water_cost
    
    # Split equally among active leases
    num_leases = len(active_leases)
    cost_per_lease = total_cost / num_leases
    
    # Generate invoices
    invoices = []
    for i, lease in enumerate(active_leases):
        invoice = {
            "lease_id": lease['id'],
            "lessee": lease['lessee'],
            "unit": lease['unit'],
            "period": reading['period'],
            "cost_breakdown": {
                "electricity": {
                    "usage": reading['kwh'] / num_leases,
                    "rate": rates['electricity'],
                    "cost": total_electricity_cost / num_leases
                },
                "gas": {
                    "usage": reading['gas'] / num_leases,
                    "rate": rates['gas'],
                    "cost": total_gas_cost / num_leases
                },
                "water": {
                    "usage": reading['water'] / num_leases,
                    "rate": rates['water'],
                    "cost": total_water_cost / num_leases
                }
            },
            "total_cost": cost_per_lease
        }
        invoices.append(invoice)
    
    return invoices

def split_utility_costs(unit: str, period: str, root_lease_id: int = None):
    """
    Main function to split utility costs for a unit and period
    
    Args:
        unit: Unit identifier
        period: Period identifier
        root_lease_id: Optional root lease ID (if not provided, will search)
    """
    # Load configuration
    utilities_contract_id = os.environ.get("UTILITIES_ORACLE_ID", "CDDO7X23GQ7J3KXACSIFRIY6T7MESM5EACTX7ZAHRRQZZIW2LYUPIX77")
    lease_contract_id = os.environ.get("LEASE_CONTRACT_ID", "CBRYYKZFYRQFAX2M54QOKFXP4M7AB4C7N3OPQ23OV5TTVTCQ")
    rpc_url = os.environ["SOROBAN_RPC"]
    
    # Initialize clients
    rpc = SorobanServer(rpc_url)
    lease_api = LeaseAPI(lease_contract_id, rpc_url)
    
    print(f"Analyzing utility costs for {unit} - {period}")
    print("=" * 60)
    
    # Read utility data
    try:
        result = rpc.invoke_contract_function(
            contract_id=utilities_contract_id,
            function_name="get_reading",
            parameters=[
                scval.to_symbol(unit),
                scval.to_symbol(period)
            ]
        )
        
        reading_data = result.result.scval.obj.vec.scvec
        reading = {
            "unit": unit,
            "period": period,
            "kwh": int(reading_data[0].obj.i64),
            "gas": int(reading_data[1].obj.i64),
            "water": int(reading_data[2].obj.i64)
        }
        
        print(f"Utility Reading:")
        print(f"   Electricity: {reading['kwh']} kWh")
        print(f"   Gas: {reading['gas']} units")
        print(f"   Water: {reading['water']} units")
        print()
        
    except Exception as e:
        print(f"ERROR: Error reading utility data: {e}")
        return
    
    # Find active leaf leases
    if root_lease_id is None:
        # For demo purposes, we'll assume we know the root lease ID
        # In a real implementation, you'd search for leases by unit
        print("NOTE: Root lease ID not provided. Using demo data.")
        active_leases = [
            {
                "id": 1,
                "lessee": "GDEMO123...",
                "unit": unit,
                "active": True
            },
            {
                "id": 2,
                "lessee": "GDEMO456...",
                "unit": unit,
                "active": True
            }
        ]
    else:
        try:
            active_leases = get_active_leaf_leases(lease_api, root_lease_id)
        except Exception as e:
            print(f"ERROR: Error finding active leases: {e}")
            return
    
    if not active_leases:
        print("ERROR: No active leases found for this unit")
        return
    
    print(f"Found {len(active_leases)} active lease(s):")
    for lease in active_leases:
        print(f"   - Lease ID {lease['id']}: {lease['lessee'][:8]}...")
    print()
    
    # Calculate cost split
    invoices = calculate_cost_split(reading, active_leases)
    
    print("Cost Split Results:")
    print("=" * 60)
    
    total_cost = 0
    for invoice in invoices:
        print(f"Invoice for Lease ID {invoice['lease_id']}")
        print(f"   Lessee: {invoice['lessee'][:8]}...")
        print(f"   Period: {invoice['period']}")
        print(f"   Cost Breakdown:")
        
        breakdown = invoice['cost_breakdown']
        print(f"     Electricity: {breakdown['electricity']['usage']:.2f} kWh x ${breakdown['electricity']['rate']:.3f} = ${breakdown['electricity']['cost']:.2f}")
        print(f"     Gas: {breakdown['gas']['usage']:.2f} units x ${breakdown['gas']['rate']:.2f} = ${breakdown['gas']['cost']:.2f}")
        print(f"     Water: {breakdown['water']['usage']:.2f} units x ${breakdown['water']['rate']:.3f} = ${breakdown['water']['cost']:.2f}")
        print(f"   Total: ${invoice['total_cost']:.2f}")
        print()
        
        total_cost += invoice['total_cost']
    
    print(f"Summary:")
    print(f"   Total Utility Cost: ${total_cost:.2f}")
    print(f"   Split Among: {len(invoices)} lease(s)")
    print(f"   Cost Per Lease: ${total_cost/len(invoices):.2f}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Split utility costs among active leases")
    parser.add_argument("unit", help="Unit identifier (e.g., NYC123A)")
    parser.add_argument("period", help="Period identifier (e.g., OCT2025)")
    parser.add_argument("--root-lease-id", type=int, help="Root lease ID (optional)")
    parser.add_argument("--output", choices=["console", "json"], default="console",
                      help="Output format (default: console)")
    
    args = parser.parse_args()
    
    # Split the costs
    split_utility_costs(args.unit, args.period, args.root_lease_id)

if __name__ == "__main__":
    main()
