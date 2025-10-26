#!/usr/bin/env python3
"""
Lease Graph Tree Visualization

This script displays the lease tree structure created on testnet.
"""

def print_lease_tree():
    """Print the lease tree structure"""
    print("="*60)
    print("LEASE GRAPH TREE STRUCTURE")
    print("="*60)
    print()
    
    print("Contract ID: CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I")
    print("Network: Testnet")
    print()
    
    print("TREE STRUCTURE:")
    print("ID 1: Master Lease (Root)")
    print("|-- Lessor:  GBAK4TXOUV5XFLWDE6IUIZYYVFQXLY4LNWNSDGNFH27NUKDUOCHGHEZX (Landlord)")
    print("|-- Lessee:  GC773P7BXH2I2MPHHYTDCRM66EBLEUUBSKHXN47E65Q6BAZ2DZVA6UQY (Master Tenant)")
    print("|-- Unit:    unit")
    print("|-- Depth:   0")
    print("|-- Limit:   2 direct children")
    print("|-- Status:  Accepted")
    print("|-- Terms:   dd759fa56986118f97909286aef8d20878f2e23fef094d0121b551e4eabe8a37")
    print()
    print("   |-- ID 2: Sublease (Level 1)")
    print("   |  |-- Lessor:  GC773P7BXH2I2MPHHYTDCRM66EBLEUUBSKHXN47E65Q6BAZ2DZVA6UQY (Master Tenant)")
    print("   |  |-- Lessee:  GDIMDTIVGQHEDZQNRAOXT5VXVTUQ6CU2ZDBV7YMNJAEET7QNMMIEWE7Y (Subtenant 1)")
    print("   |  |-- Unit:    unit")
    print("   |  |-- Depth:   1")
    print("   |  |-- Limit:   1 direct child")
    print("   |  |-- Status:  Pending acceptance")
    print("   |  |-- Terms:   dd759fa56986118f97909286aef8d20878f2e23fef094d0121b551e4eabe8a37")
    print()
    print("   |-- ID 3: Sublease (Level 1)")
    print("      |-- Lessor:  GC773P7BXH2I2MPHHYTDCRM66EBLEUUBSKHXN47E65Q6BAZ2DZVA6UQY (Master Tenant)")
    print("      |-- Lessee:  GA27H6G7UFTND5MLOB6ORUXWRGXD3SMZKIBPKKRXM5AVZZ5NM76TVAV3 (Subtenant 2)")
    print("      |-- Unit:    unit")
    print("      |-- Depth:   1")
    print("      |-- Limit:   1 direct child")
    print("      |-- Status:  Pending acceptance")
    print("      |-- Terms:   dd759fa56986118f97909286aef8d20878f2e23fef094d0121b551e4eabe8a37")
    print()
    
    print("="*60)
    print("EVENTS EMITTED")
    print("="*60)
    print("1. LeaseCreated: (unit, 1) -> Master Tenant")
    print("2. LeaseAccepted: (1) -> void")
    print("3. SubleaseCreated: (1, 2) -> Subtenant 1")
    print("4. SubleaseCreated: (1, 3) -> Subtenant 2")
    print()
    
    print("="*60)
    print("KEY FEATURES DEMONSTRATED")
    print("="*60)
    print("- ID-based parent/child relationships")
    print("- Terms validation (hash-based)")
    print("- Acceptance control workflow")
    print("- Branching limits enforcement")
    print("- Depth tracking (0, 1)")
    print("- Event emission for indexers")
    print("- Authorization (only lessee can create subleases)")
    print("- Unlimited sublease depth support")
    print()
    
    print("="*60)
    print("NEXT STEPS")
    print("="*60)
    print("1. Accept subleases (IDs 2, 3) to activate them")
    print("2. Create third-level subleases from accepted subtenants")
    print("3. Test terms mismatch rejection")
    print("4. Test limit enforcement")
    print("5. Add query functions for tree traversal")
    print("6. Integrate with insurance/utility systems")
    print()
    
    print("Contract Explorer:")
    print("https://stellar.expert/explorer/testnet/contract/CDBFB6YDB55G7E5ZGOHYIYBLS745NVBU73TKLB6N6IT6XBKBWICNUW5I")

if __name__ == "__main__":
    print_lease_tree()
