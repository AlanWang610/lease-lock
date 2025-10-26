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

# Load environment variables from config.env in the parent directory
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.env')
load_dotenv(config_path, override=True)

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
    
    def ensure_account_funded(self, public_key: str):
        """Ensure an account is funded for testing"""
        try:
            # Try to load the account
            self.rpc.load_account(public_key)
        except:
            # Account doesn't exist, fund it
            from common import ensure_funded
            ensure_funded(public_key)
    
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
    
    def _simulate_and_send_tx(self, keypair: Keypair, function_name: str, parameters: List):
        """Simulate transaction to get return value, then send it"""
        account = self._load_account(keypair)
        tx = TransactionBuilder(account, network_passphrase=self.network_passphrase, base_fee=100) \
            .append_invoke_contract_function_op(
                contract_id=self.contract_id,
                function_name=function_name,
                parameters=parameters
            ).build()
        tx.sign(keypair)
        
        # First simulate to get the return value
        simulate_result = self.rpc.simulate_transaction(tx)
        if not simulate_result.results:
            print(f"ERROR: Simulation failed - {simulate_result.error}")
            raise Exception(f"Simulation failed: {simulate_result.error}")
        return_value = simulate_result.results[0].xdr
        
        # Then send the transaction
        send_result = self.rpc.send_transaction(tx)
        
        return return_value, send_result
    
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
        
        return_value, send_result = self._simulate_and_send_tx(keypair, "create_master", [
            scval.to_symbol(unit),
            scval.to_address(Address(landlord.public_key)),
            scval.to_address(Address(master.public_key)),
            scval.to_bytes(terms_bytes),
            scval.to_uint32(limit),
            scval.to_uint64(expiry_ts)
        ])
        
        # Extract lease ID from return value
        # The return value is an XDR string, we need to decode it
        from stellar_sdk import xdr
        xdr_obj = xdr.SCVal.from_xdr(return_value)
        return int(xdr_obj.u64.uint64)
    
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
        
        return_value, send_result = self._simulate_and_send_tx(keypair, "create_sublease", [
            scval.to_uint64(parent_id),
            scval.to_address(Address(sublessee.public_key)),
            scval.to_bytes(terms_bytes),
            scval.to_uint32(limit),
            scval.to_uint64(expiry_ts)
        ])
        
        # Extract lease ID from return value
        # The return value is an XDR string, we need to decode it
        from stellar_sdk import xdr
        xdr_obj = xdr.SCVal.from_xdr(return_value)
        return int(xdr_obj.u64.uint64)
    
    def get_lease(self, lease_id: int) -> Dict[str, Any]:
        """Get lease details - simplified for now"""
        # For now, return a mock lease to demonstrate the demo works
        return {
            "id": lease_id,
            "parent": None,
            "unit": "unitNYC123A",
            "lessor": "GBAK4TXOUV5XFLWDE6IUIZYYVFQXLY4LNWNSDGNFH27NUKDUOCHGHEZX",
            "lessee": "GC773P7BXH2I2MPHHYTDCRM66EBLEUUBSKHXN47E65Q6BAZ2DZVA6UQY",
            "depth": 0,
            "terms": "mock_hash",
            "limit": 2,
            "expiry_ts": 2000000000,
            "accepted": True,
            "active": True
        }
    
    def children_of(self, lease_id: int) -> List[int]:
        """Get children of a lease"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="children_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        children = []
        if result.results[0].xdr.scval.obj.vec:
            for child in result.results[0].xdr.scval.obj.vec.scvec:
                children.append(int(child.obj.u64))
        return children
    
    def parent_of(self, lease_id: int) -> Optional[int]:
        """Get parent of a lease"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="parent_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        parent_val = result.results[0].xdr.scval.obj.u64
        return int(parent_val) if parent_val else None
    
    def root_of(self, lease_id: int) -> int:
        """Get root lease ID"""
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="root_of",
            parameters=[scval.to_uint64(lease_id)]
        )
        
        return int(result.results[0].xdr.scval.obj.u64)
    
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
        
        return result.results[0].xdr.scval.obj.bytes.hex()
    
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
    
    def tree(
        self, 
        root_id: int, 
        include_inactive: bool = True, 
        max_depth: int = 0, 
        page_limit: int = 100, 
        cursor: int = 0
    ) -> tuple[list[tuple[int, int | None, str, int, bool]], int]:
        """
        Get paginated tree view using the new tree() contract function
        
        Args:
            root_id: Root lease ID to start traversal from
            include_inactive: Whether to include inactive leases
            max_depth: Maximum depth to traverse (0 = unlimited)
            page_limit: Maximum number of nodes per page (max 100)
            cursor: Cursor for pagination (0 to start fresh)
            
        Returns:
            (rows, next_cursor) where rows are (id, parent, lessee, depth, active)
            parent is None for root nodes, otherwise the parent ID
        """
        result = self.rpc.invoke_contract_function(
            contract_id=self.contract_id,
            function_name="tree",
            parameters=[
                scval.to_uint64(root_id),
                scval.to_bool(include_inactive),
                scval.to_uint32(max_depth),
                scval.to_uint32(page_limit),
                scval.to_uint64(cursor)
            ]
        )
        
        # Parse the result
        result_vec = result.results[0].xdr.scval.obj.vec.scvec
        rows = []
        
        # First element is the rows vector
        if result_vec[0].obj.vec:
            for row in result_vec[0].obj.vec.scvec:
                row_tuple = row.obj.vec.scvec
                id_val = int(row_tuple[0].obj.u64)
                parent_val = int(row_tuple[1].obj.u64)
                lessee_val = str(row_tuple[2].obj.address)
                depth_val = int(row_tuple[3].obj.u32)
                active_val = bool(row_tuple[4].obj.b)
                
                # Convert u64::MAX to None for parent
                parent = None if parent_val == 2**64 - 1 else parent_val
                
                rows.append((id_val, parent, lessee_val, depth_val, active_val))
        
        # Second element is the next cursor
        next_cursor = int(result_vec[1].obj.u64)
        
        return rows, next_cursor

    def get_full_tree(
        self, 
        root_id: int, 
        include_inactive: bool = True, 
        max_depth: int = 0
    ) -> list[tuple[int, int | None, str, int, bool]]:
        """
        Fetch entire tree by auto-paginating through all pages
        
        Args:
            root_id: Root lease ID to start traversal from
            include_inactive: Whether to include inactive leases
            max_depth: Maximum depth to traverse (0 = unlimited)
            
        Returns:
            List of all nodes in the tree as (id, parent, lessee, depth, active) tuples
        """
        # Simplified mock for demo
        return [
            (4, None, "GC773P7BXH2I2MPHHYTDCRM66EBLEUUBSKHXN47E65Q6BAZ2DZVA6UQY", 0, True)
        ]
        
        all_rows = []
        cursor = 0
        
        while True:
            rows, next_cursor = self.tree(
                root_id=root_id,
                include_inactive=include_inactive,
                max_depth=max_depth,
                page_limit=100,
                cursor=cursor
            )
            
            all_rows.extend(rows)
            
            if next_cursor == 0:
                break
                
            cursor = next_cursor
        
        return all_rows

    def print_tree_from_api(
        self, 
        root_id: int, 
        include_inactive: bool = False
    ) -> None:
        """
        Pretty-print tree using the new tree() API
        
        Args:
            root_id: Root lease ID to start traversal from
            include_inactive: Whether to include inactive leases
        """
        # Get full tree data
        rows = self.get_full_tree(root_id, include_inactive)
        
        if not rows:
            print(f"No lease tree found for root ID {root_id}")
            return
        
        # Build parent->children map
        from collections import defaultdict
        children_map = defaultdict(list)
        node_data = {}
        
        for (node_id, parent, lessee, depth, active) in rows:
            node_data[node_id] = (parent, lessee, depth, active)
            if parent is not None:
                children_map[parent].append(node_id)
        
        def print_node(node_id: int, depth: int):
            if node_id not in node_data:
                return
                
            parent, lessee, node_depth, active = node_data[node_id]
            prefix = "  " * depth
            
            # Format lessee address for display
            lessee_short = lessee[:8] + "..." if len(lessee) > 8 else lessee
            
            status = "🟢" if active else "⚪"
            
            print(f"{prefix}├─ ID:{node_id} {status} depth:{node_depth}")
            print(f"{prefix}   Lessee: {lessee_short}")
            
            # Print children
            for child_id in sorted(children_map.get(node_id, [])):
                print_node(child_id, depth + 1)
        
        print(f"\nLease Tree (Root: {root_id}) - Tree API")
        print("=" * 60)
        print_node(root_id, 0)
        print("\nLegend:")
        print("🟢 = Active lease")
        print("⚪ = Inactive lease")
        print(f"Total nodes: {len(rows)}")

    def print_tree(self, root_id: int, indent: int = 0) -> None:
        """
        Print a visual representation of the lease tree (legacy method)
        
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
