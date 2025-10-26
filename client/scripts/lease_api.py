#!/usr/bin/env python3
"""
Lease API Python Wrapper

This module provides Python wrappers for the lease registry contract functions,
including helper functions for creating lease chains and visualizing tree structures.
"""

import os
import json
import sys
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from stellar_sdk import Keypair, Network, Address, TransactionBuilder
from stellar_sdk import SorobanServer
from stellar_sdk import scval

# Add the scripts directory to the path to import common
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import generate_terms_hash, hex_to_bytes

load_dotenv()

class LeaseAPI:
    """Python wrapper for the lease registry contract"""
    
    def __init__(self, contract_id: str, rpc_url: str = None, network_passphrase: str = None):
        """
        Initialize the Lease API client
        
        Args:
            contract_id: The deployed contract ID
            rpc_url: Soroban RPC URL (defaults to environment variable)
            network_passphrase: Network passphrase (defaults to testnet)
        """
        self.contract_id = contract_id
        self.rpc = SorobanServer(rpc_url or os.environ["SOROBAN_RPC"])
        self.network_passphrase = network_passphrase or Network.TESTNET_NETWORK_PASSPHRASE
        
        # Cache for terms hash to avoid regenerating
        self._terms_cache: Dict[str, bytes] = {}
    
    def _get_terms_bytes(self, terms_dict: Dict[str, Any]) -> bytes:
        """Get terms bytes from dict, using cache if available"""
        terms_json = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True)
        if terms_json not in self._terms_cache:
            terms_hash_hex = generate_terms_hash(terms_dict)
            self._terms_cache[terms_json] = hex_to_bytes(terms_hash_hex)
        return self._terms_cache[terms_json]
    
    def _load_account(self, keypair: Keypair):
        """Load account for transaction building"""
        return self.rpc.load_account(keypair.public_key)
    
    def _build_and_send_tx(self, keypair: Keypair, function_name: str, parameters: List):
        """Build and send a transaction"""
        account = self._load_account(keypair)
        tx = TransactionBuilder(account, network_passphrase=self.network_passphrase, base_fee=100) \
            .append_invoke_contract_function_op(
                contract_id=self.contract_id,
                function_name=function_name,
                parameters=parameters
            ).build()
        tx.sign(keypair)
        return self.rpc.send_transaction(tx)
    
    def create_master(
        self, 
        keypair: Keypair, 
        unit: str, 
        landlord: Keypair, 
        master: Keypair, 
        terms_dict: Dict[str, Any], 
        limit: int, 
        expiry_ts: int
    ) -> int:
        """
        Create a master lease
        
        Args:
            keypair: Keypair to sign the transaction (should be landlord)
            unit: Unit identifier (e.g., "unit:NYC:123-A")
            landlord: Landlord keypair
            master: Master tenant keypair
            terms_dict: Terms dictionary
            limit: Maximum number of direct subleases
            expiry_ts: Expiry timestamp
            
        Returns:
            Lease ID
        """
        terms_bytes = self._get_terms_bytes(terms_dict)
        
        result = self._build_and_send_tx(keypair, "create_master", [
            scval.to_symbol(unit),
            scval.to_address(Address(landlord.public_key)),
            scval.to_address(Address(master.public_key)),
            scval.to_bytes(terms_bytes),
            scval.to_uint32(limit),
            scval.to_uint64(expiry_ts)
        ])
        
        # Extract lease ID from result
        return int(result.result.scval.obj.vec.scvec[0].obj.u64)
    
    def accept(self, keypair: Keypair, lease_id: int) -> Dict:
        """Accept a lease"""
        return self._build_and_send_tx(keypair, "accept", [
            scval.to_uint64(lease_id)
        ])
    
    def create_sublease(
        self, 
        keypair: Keypair, 
        parent_id: int, 
        sublessee: Keypair, 
        terms_dict: Dict[str, Any], 
        limit: int, 
        expiry_ts: int
    ) -> int:
        """
        Create a sublease
        
        Args:
            keypair: Keypair to sign the transaction (should be parent lessee)
            parent_id: Parent lease ID
            sublessee: Sublessee keypair
            terms_dict: Terms dictionary (must match parent)
            limit: Maximum number of direct subleases (must be <= parent limit)
            expiry_ts: Expiry timestamp (must be <= parent expiry)
            
        Returns:
            New lease ID
        """
        terms_bytes = self._get_terms_bytes(terms_dict)
        
        result = self._build_and_send_tx(keypair, "create_sublease", [
            scval.to_uint64(parent_id),
            scval.to_address(Address(sublessee.public_key)),
            scval.to_bytes(terms_bytes),
            scval.to_uint32(limit),
            scval.to_uint64(expiry_ts)
        ])
        
        # Extract lease ID from result
        return int(result.result.scval.obj.u64)
    
    def get_lease(self, lease_id: int) -> Dict[str, Any]:
        """Get lease details"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="get_lease",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        # Parse the result into a dictionary
        lease_data = result.result.scval.obj.vec.scvec
        return {
            "id": int(lease_data[0].obj.u64),
            "parent": int(lease_data[1].obj.u64) if lease_data[1].obj.u64 else None,
            "unit": str(lease_data[2].obj.sym),
            "lessor": str(lease_data[3].obj.address),
            "lessee": str(lease_data[4].obj.address),
            "depth": int(lease_data[5].obj.u32),
            "terms": lease_data[6].obj.bytes.hex(),
            "limit": int(lease_data[7].obj.u32),
            "expiry_ts": int(lease_data[8].obj.u64),
            "accepted": bool(lease_data[9].obj.b),
            "active": bool(lease_data[10].obj.b)
        }
    
    def children_of(self, lease_id: int) -> List[int]:
        """Get children of a lease"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="children_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        children = []
        if result.result.scval.obj.vec:
            for child in result.result.scval.obj.vec.scvec:
                children.append(int(child.obj.u64))
        return children
    
    def parent_of(self, lease_id: int) -> Optional[int]:
        """Get parent of a lease"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="parent_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        parent_val = result.result.scval.obj.u64
        return int(parent_val) if parent_val else None
    
    def root_of(self, lease_id: int) -> int:
        """Get root lease ID"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="root_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        return int(result.result.scval.obj.u64)
    
    def set_active(self, keypair: Keypair, lease_id: int) -> Dict:
        """Activate a lease"""
        return self._build_and_send_tx(keypair, "set_active", [
            scval.to_uint64(lease_id)
        ])
    
    def set_delinquent(self, keypair: Keypair, lease_id: int) -> Dict:
        """Mark lease as delinquent"""
        return self._build_and_send_tx(keypair, "set_delinquent", [
            scval.to_uint64(lease_id)
        ])
    
    def cancel_unaccepted(self, keypair: Keypair, lease_id: int) -> Dict:
        """Cancel an unaccepted sublease"""
        return self._build_and_send_tx(keypair, "cancel_unaccepted", [
            scval.to_uint64(lease_id)
        ])
    
    def replace_sublessee(self, keypair: Keypair, lease_id: int, new_lessee: Keypair) -> Dict:
        """Replace sublessee of an unaccepted lease"""
        return self._build_and_send_tx(keypair, "replace_sublessee", [
            scval.to_uint64(lease_id),
            scval.to_address(Address(new_lessee.public_key))
        ])
    
    def terms_of(self, lease_id: int) -> str:
        """Get terms hash for a lease"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="terms_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        return result.result.scval.obj.bytes.hex()
    
    def create_chain(
        self, 
        parent_keypair: Keypair, 
        parent_id: int, 
        sublessees: List[Keypair], 
        terms_dict: Dict[str, Any], 
        limit: int, 
        expiry_ts: int
    ) -> List[int]:
        """
        Create a chain of subleases
        
        Args:
            parent_keypair: Keypair of the parent lessee
            parent_id: Parent lease ID
            sublessees: List of sublessee keypairs
            terms_dict: Terms dictionary
            limit: Limit for each sublease
            expiry_ts: Expiry timestamp
            
        Returns:
            List of created lease IDs
        """
        lease_ids = []
        current_parent_id = parent_id
        current_keypair = parent_keypair
        
        for sublessee in sublessees:
            # Create sublease
            child_id = self.create_sublease(
                current_keypair, 
                current_parent_id, 
                sublessee, 
                terms_dict, 
                limit, 
                expiry_ts
            )
            lease_ids.append(child_id)
            
            # Accept the sublease
            self.accept(sublessee, child_id)
            
            # Move to next level
            current_parent_id = child_id
            current_keypair = sublessee
        
        return lease_ids
    
    def get_lease_tree(self, root_id: int) -> Dict[str, Any]:
        """
        Get the entire lease tree structure
        
        Args:
            root_id: Root lease ID
            
        Returns:
            Dictionary containing tree structure
        """
        def build_tree(node_id: int) -> Dict[str, Any]:
            lease = self.get_lease(node_id)
            children = self.children_of(node_id)
            
            tree_node = {
                "lease": lease,
                "children": []
            }
            
            for child_id in children:
                tree_node["children"].append(build_tree(child_id))
            
            return tree_node
        
        return build_tree(root_id)
    
    def print_tree(self, root_id: int, indent: int = 0) -> None:
        """
        Print a visual representation of the lease tree
        
        Args:
            root_id: Root lease ID
            indent: Indentation level for printing
        """
        def print_node(node_id: int, depth: int):
            lease = self.get_lease(node_id)
            prefix = "  " * depth
            
            # Format addresses for display
            lessor_short = lease['lessor'][:8] + "..." if len(lease['lessor']) > 8 else lease['lessor']
            lessee_short = lease['lessee'][:8] + "..." if len(lease['lessee']) > 8 else lease['lessee']
            
            status = "✓" if lease['accepted'] else "○"
            active = "🟢" if lease['active'] else "⚪"
            
            print(f"{prefix}├─ ID:{node_id} {status}{active} {lease['unit']}")
            print(f"{prefix}   Lessor: {lessor_short}")
            print(f"{prefix}   Lessee: {lessee_short}")
            print(f"{prefix}   Depth: {lease['depth']}, Limit: {lease['limit']}")
            print(f"{prefix}   Terms: {lease['terms'][:16]}...")
            
            # Print children
            children = self.children_of(node_id)
            for child_id in children:
                print_node(child_id, depth + 1)
        
        print(f"\nLease Tree (Root: {root_id})")
        print("=" * 50)
        print_node(root_id, 0)
        print("\nLegend:")
        print("✓ = Accepted lease")
        print("○ = Pending acceptance")
        print("🟢 = Active lease")
        print("⚪ = Inactive lease")


def main():
    """Example usage of the LeaseAPI"""
    # Example configuration
    contract_id = os.environ.get("LEASE_REGISTRY_ID", "CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I")
    
    # Create API client
    api = LeaseAPI(contract_id)
    
    # Generate test keypairs
    landlord = Keypair.from_secret(os.environ["LANDLORD_SECRET"])
    master = Keypair.from_secret(os.environ["TENANT_SECRET"])
    sub1 = Keypair.random()
    sub2 = Keypair.random()
    
    # Define terms
    terms_dict = {
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
    
    print("Creating master lease...")
    root_id = api.create_master(
        landlord, "unit:NYC:123-A", landlord, master, 
        terms_dict, 2, 2_000_000_000
    )
    print(f"Master lease created with ID: {root_id}")
    
    print("Accepting master lease...")
    api.accept(master, root_id)
    
    print("Creating sublease chain...")
    sublease_ids = api.create_chain(
        master, root_id, [sub1, sub2], 
        terms_dict, 1, 2_000_000_000
    )
    print(f"Created subleases: {sublease_ids}")
    
    print("Activating leases...")
    api.set_active(landlord, root_id)
    api.set_active(master, sublease_ids[0])
    api.set_active(sub1, sublease_ids[1])
    
    print("Printing lease tree...")
    api.print_tree(root_id)
    
    print("Querying lease details...")
    lease_details = api.get_lease(root_id)
    print(f"Root lease details: {json.dumps(lease_details, indent=2)}")


if __name__ == "__main__":
    main()
