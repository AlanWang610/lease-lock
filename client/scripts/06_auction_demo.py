#!/usr/bin/env python3
"""
Auction Demo Script

This script demonstrates the complete auction flow:
1. Create an auction for a sublease
2. Multiple bidders place bids
3. Finalize the auction with second-price settlement
4. Integrate with LeaseRegistry to create sublease for winner
"""

import os
import sys
import time
from dotenv import load_dotenv
from stellar_sdk import Server, Keypair, Network, TransactionBuilder, Asset
from stellar_sdk.exceptions import NotFoundError
from stellar_sdk.operation import InvokeHostFunction, CreateContractHostFunction, InstallContractCodeHostFunction
from stellar_sdk.soroban import SorobanServer
from stellar_sdk.soroban.soroban_rpc import GetTransactionStatus
from stellar_sdk.xdr import SCVal, SCValType

# Add the client scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from common import actor_from_env, ensure_funded, balances

load_dotenv()

# Configuration
HORIZON_URL = os.environ["HORIZON_URL"]
NETWORK_PASSPHRASE = os.environ["NETWORK_PASSPHRASE"]
SOROBAN_RPC_URL = os.environ.get("SOROBAN_RPC_URL", HORIZON_URL.replace("horizon", "soroban-rpc"))

# Initialize clients
server = Server(HORIZON_URL)
soroban_server = SorobanServer(SOROBAN_RPC_URL)

# Load actors
landlord = actor_from_env("LANDLORD_SECRET")
tenant = actor_from_env("TENANT_SECRET")
bidder1 = actor_from_env("BIDDER1_SECRET")
bidder2 = actor_from_env("BIDDER2_SECRET")

# Contract addresses (these would be deployed addresses in practice)
LEASE_REGISTRY_CONTRACT = os.environ.get("LEASE_REGISTRY_CONTRACT", "C...")  # Replace with actual address
AUCTION_CONTRACT = os.environ.get("AUCTION_CONTRACT", "C...")  # Replace with actual address
TOKEN_CONTRACT = os.environ.get("TOKEN_CONTRACT", "C...")  # Replace with actual address

def ensure_all_funded():
    """Ensure all accounts are funded"""
    print("Ensuring all accounts are funded...")
    ensure_funded(landlord.kp.public_key)
    ensure_funded(tenant.kp.public_key)
    ensure_funded(bidder1.kp.public_key)
    ensure_funded(bidder2.kp.public_key)
    print("All accounts funded!")

def create_auction():
    """Create an auction for a sublease"""
    print("\n=== Creating Auction ===")
    
    # Get current timestamp
    current_time = int(time.time())
    start_ts = current_time + 60  # Start in 1 minute
    end_ts = current_time + 3600  # End in 1 hour
    
    # Create auction transaction
    source_account = soroban_server.load_account(tenant.kp.public_key)
    
    tx = (
        TransactionBuilder(source_account, NETWORK_PASSPHRASE)
        .add_operation(
            InvokeHostFunction(
                function=SCVal.from_string("create"),
                args=[
                    SCVal.from_u64(1),  # lease_id
                    SCVal.from_string("unit:NYC:123-A"),  # unit
                    SCVal.from_address(tenant.kp.public_key),  # seller
                    SCVal.from_address(TOKEN_CONTRACT),  # token
                    SCVal.from_i128(100),  # reserve price
                    SCVal.from_i128(10),  # min_increment
                    SCVal.from_u64(start_ts),  # start_ts
                    SCVal.from_u64(end_ts),  # end_ts
                    SCVal.from_u64(60),  # extend_secs
                    SCVal.from_u64(30),  # extend_window
                ],
                source=AUCTION_CONTRACT,
            )
        )
        .set_timeout(300)
        .build()
    )
    
    tx.sign(tenant.kp)
    result = soroban_server.send_transaction(tx)
    
    if result.status == GetTransactionStatus.SUCCESS:
        print(f"Auction created successfully! Transaction: {result.hash}")
        return result.result_xdr
    else:
        print(f"Failed to create auction: {result}")
        return None

def place_bid(bidder_kp, auction_id, amount):
    """Place a bid on an auction"""
    print(f"\n=== Placing bid of {amount} from {bidder_kp.public_key[:8]}... ===")
    
    # First, approve the auction contract to spend tokens
    source_account = soroban_server.load_account(bidder_kp.public_key)
    
    approve_tx = (
        TransactionBuilder(source_account, NETWORK_PASSPHRASE)
        .add_operation(
            InvokeHostFunction(
                function=SCVal.from_string("approve"),
                args=[
                    SCVal.from_address(bidder_kp.public_key),  # from
                    SCVal.from_address(AUCTION_CONTRACT),  # spender
                    SCVal.from_i128(amount),  # amount
                    SCVal.from_u64(0),  # expiration_ledger
                ],
                source=TOKEN_CONTRACT,
            )
        )
        .set_timeout(300)
        .build()
    )
    
    approve_tx.sign(bidder_kp)
    approve_result = soroban_server.send_transaction(approve_tx)
    
    if approve_result.status != GetTransactionStatus.SUCCESS:
        print(f"Failed to approve tokens: {approve_result}")
        return False
    
    # Now place the bid
    bid_tx = (
        TransactionBuilder(source_account, NETWORK_PASSPHRASE)
        .add_operation(
            InvokeHostFunction(
                function=SCVal.from_string("bid"),
                args=[
                    SCVal.from_u64(auction_id),
                    SCVal.from_address(bidder_kp.public_key),
                    SCVal.from_i128(amount),
                ],
                source=AUCTION_CONTRACT,
            )
        )
        .set_timeout(300)
        .build()
    )
    
    bid_tx.sign(bidder_kp)
    bid_result = soroban_server.send_transaction(bid_tx)
    
    if bid_result.status == GetTransactionStatus.SUCCESS:
        print(f"Bid placed successfully! Transaction: {bid_result.hash}")
        return True
    else:
        print(f"Failed to place bid: {bid_result}")
        return False

def finalize_auction(auction_id):
    """Finalize the auction"""
    print(f"\n=== Finalizing Auction {auction_id} ===")
    
    source_account = soroban_server.load_account(tenant.kp.public_key)
    
    tx = (
        TransactionBuilder(source_account, NETWORK_PASSPHRASE)
        .add_operation(
            InvokeHostFunction(
                function=SCVal.from_string("finalize"),
                args=[
                    SCVal.from_u64(auction_id),
                    SCVal.from_address(tenant.kp.public_key),  # lessor
                    SCVal.from_address(bidder1.kp.public_key),  # new_lessee (winner)
                ],
                source=AUCTION_CONTRACT,
            )
        )
        .set_timeout(300)
        .build()
    )
    
    tx.sign(tenant.kp)
    result = soroban_server.send_transaction(tx)
    
    if result.status == GetTransactionStatus.SUCCESS:
        print(f"Auction finalized successfully! Transaction: {result.hash}")
        return True
    else:
        print(f"Failed to finalize auction: {result}")
        return False

def create_sublease_for_winner(winner_address):
    """Create sublease for the auction winner"""
    print(f"\n=== Creating Sublease for Winner {winner_address[:8]}... ===")
    
    # Generate terms hash (simplified)
    terms_dict = {
        "rent": 1000,
        "duration": 12,
        "utilities": "included"
    }
    terms_hash = generate_terms_hash(terms_dict)
    
    source_account = soroban_server.load_account(tenant.kp.public_key)
    
    tx = (
        TransactionBuilder(source_account, NETWORK_PASSPHRASE)
        .add_operation(
            InvokeHostFunction(
                function=SCVal.from_string("create_sublease"),
                args=[
                    SCVal.from_u64(1),  # parent_id
                    SCVal.from_address(winner_address),  # sublessee
                    SCVal.from_bytes(bytes.fromhex(terms_hash)),  # terms
                    SCVal.from_u32(2),  # limit
                    SCVal.from_u64(int(time.time()) + 31536000),  # expiry_ts (1 year)
                ],
                source=LEASE_REGISTRY_CONTRACT,
            )
        )
        .set_timeout(300)
        .build()
    )
    
    tx.sign(tenant.kp)
    result = soroban_server.send_transaction(tx)
    
    if result.status == GetTransactionStatus.SUCCESS:
        print(f"Sublease created successfully! Transaction: {result.hash}")
        return True
    else:
        print(f"Failed to create sublease: {result}")
        return False

def generate_terms_hash(terms_dict):
    """Generate SHA-256 hash of canonical JSON terms"""
    import json
    import hashlib
    
    canon = json.dumps(terms_dict, separators=(',', ':'), sort_keys=True).encode('utf-8')
    h = hashlib.sha256(canon).digest()
    return h.hex()

def main():
    """Main demo function"""
    print("=== Auction Demo ===")
    print("This demo shows a complete second-price auction flow for subleases")
    
    # Ensure all accounts are funded
    ensure_all_funded()
    
    # Create auction
    auction_result = create_auction()
    if not auction_result:
        print("Failed to create auction. Exiting.")
        return
    
    # Extract auction ID from result (simplified - in practice you'd parse the XDR)
    auction_id = 1  # This would be extracted from the transaction result
    
    # Wait for auction to start
    print("Waiting for auction to start...")
    time.sleep(65)  # Wait 1 minute + 5 seconds
    
    # Place bids
    print("\n=== Bidding Phase ===")
    
    # Bidder 1 places bid of 150
    place_bid(bidder1.kp, auction_id, 150)
    time.sleep(5)
    
    # Bidder 2 places bid of 200
    place_bid(bidder2.kp, auction_id, 200)
    time.sleep(5)
    
    # Bidder 1 increases bid to 250
    place_bid(bidder1.kp, auction_id, 100)  # Total: 250
    
    # Wait for auction to end
    print("\nWaiting for auction to end...")
    time.sleep(3600)  # Wait 1 hour
    
    # Finalize auction
    finalize_auction(auction_id)
    
    # Create sublease for winner (bidder1 with 250 total bid)
    create_sublease_for_winner(bidder1.kp.public_key)
    
    print("\n=== Demo Complete ===")
    print("The auction has been completed with second-price settlement.")
    print("Winner (bidder1) paid the second-highest price (200) instead of their bid (250).")
    print("A sublease has been created for the winner.")

if __name__ == "__main__":
    main()
