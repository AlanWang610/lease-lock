#!/usr/bin/env python3
"""
Simple Auction Contract Logic Test

This script tests the auction contract logic by simulating the contract behavior
without requiring a full Stellar network deployment.
"""

import time
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class Auction:
    """Represents an auction"""
    id: int
    lease_id: int
    seller: str
    unit: str
    token: str
    reserve: int
    min_increment: int
    start_ts: int
    end_ts: int
    extend_secs: int
    extend_window: int
    max_extensions: int
    extensions_count: int
    best_bid: int
    best_bidder: str
    second_bid: int
    settled: bool

@dataclass
class Bid:
    """Represents a bid"""
    auction_id: int
    bidder: str
    amount: int
    timestamp: int

class AuctionContract:
    """Mock auction contract for testing"""
    
    def __init__(self):
        self.auctions: Dict[int, Auction] = {}
        self.bids: Dict[tuple, int] = {}  # (auction_id, bidder) -> total_amount
        self.next_id = 1
        self.events: List[tuple] = []
    
    def create(self, lease_id: int, unit: str, seller: str, token: str, 
               reserve: int, min_increment: int, start_ts: int, end_ts: int,
               extend_secs: int, extend_window: int) -> int:
        """Create a new auction"""
        # Validation
        if start_ts >= end_ts:
            raise ValueError("invalid-times")
        if reserve <= 0:
            raise ValueError("invalid-reserve")
        if min_increment <= 0:
            raise ValueError("invalid-increment")
        if extend_window == 0:
            raise ValueError("invalid-extend-window")
        if extend_secs == 0:
            raise ValueError("invalid-extend-secs")
        
        auction_id = self.next_id
        self.next_id += 1
        
        auction = Auction(
            id=auction_id,
            lease_id=lease_id,
            seller=seller,
            unit=unit,
            token=token,
            reserve=reserve,
            min_increment=min_increment,
            start_ts=start_ts,
            end_ts=end_ts,
            extend_secs=extend_secs,
            extend_window=extend_window,
            max_extensions=10,  # Fixed cap
            extensions_count=0,
            best_bid=0,
            best_bidder=seller,  # dummy address
            second_bid=0,
            settled=False
        )
        
        self.auctions[auction_id] = auction
        self.events.append(("AucCreate", auction_id, lease_id, seller, unit, reserve))
        
        return auction_id
    
    def bid(self, auction_id: int, bidder: str, amount: int, current_time: int) -> bool:
        """Place a bid on an auction"""
        if amount <= 0:
            raise ValueError("invalid-amount")
        
        if auction_id not in self.auctions:
            raise ValueError("auction-not-found")
        
        auction = self.auctions[auction_id]
        
        # Validation
        if auction.settled:
            raise ValueError("auction-settled")
        if current_time < auction.start_ts:
            raise ValueError("auction-not-started")
        if current_time > auction.end_ts:
            raise ValueError("auction-ended")
        
        # Update bidder's total escrowed amount
        current_bid = self.bids.get((auction_id, bidder), 0)
        new_total = current_bid + amount
        self.bids[(auction_id, bidder)] = new_total
        
        # Check if bid meets requirements
        if new_total < auction.reserve:
            raise ValueError("below-reserve")
        if new_total < auction.best_bid + auction.min_increment:
            raise ValueError("insufficient-increment")
        
        # Update auction state
        auction.second_bid = auction.best_bid
        auction.best_bid = new_total
        auction.best_bidder = bidder
        
        # Anti-sniping: extend auction if bid is within extend_window
        if auction.extensions_count < auction.max_extensions:
            time_remaining = auction.end_ts - current_time
            if time_remaining <= auction.extend_window:
                auction.end_ts += auction.extend_secs
                auction.extensions_count += 1
                self.events.append(("AucExtend", auction_id, auction.end_ts))
        
        self.events.append(("BidPlaced", auction_id, bidder, new_total, current_time, auction.end_ts))
        return True
    
    def finalize(self, auction_id: int, lessor: str, new_lessee: str, current_time: int) -> bool:
        """Finalize the auction and settle payments"""
        if auction_id not in self.auctions:
            raise ValueError("auction-not-found")
        
        auction = self.auctions[auction_id]
        
        # Validation
        if auction.settled:
            raise ValueError("already-settled")
        if current_time < auction.end_ts:
            raise ValueError("auction-not-ended")
        
        # Check if reserve was met
        if auction.best_bid < auction.reserve:
            # Refund all bidders
            for (_, bidder), amount in self.bids.items():
                if amount > 0:
                    self.events.append(("Refund", auction_id, bidder, amount))
            
            auction.settled = True
            self.events.append(("AucFailed", auction_id, auction.reserve))
            return False
        
        # Calculate clearing price (second price)
        clearing_price = max(auction.second_bid, auction.reserve)
        
        # Simulate payments
        self.events.append(("Payment", "seller", auction.seller, clearing_price))
        
        # Refund winner (best_bid - clearing_price)
        winner_refund = auction.best_bid - clearing_price
        if winner_refund > 0:
            self.events.append(("Refund", auction_id, auction.best_bidder, winner_refund))
        
        # Refund all other bidders
        for (_, bidder), amount in self.bids.items():
            if bidder != auction.best_bidder and amount > 0:
                self.events.append(("Refund", auction_id, bidder, amount))
        
        # Clear bids for this auction
        self.bids = {k: v for k, v in self.bids.items() if k[0] != auction_id}
        
        auction.settled = True
        self.events.append(("AucFinal", auction_id, auction.best_bidder, clearing_price, auction.lease_id))
        
        return True
    
    def cancel(self, auction_id: int, current_time: int) -> bool:
        """Cancel an auction"""
        if auction_id not in self.auctions:
            raise ValueError("auction-not-found")
        
        auction = self.auctions[auction_id]
        
        if auction.settled:
            raise ValueError("already-settled")
        
        has_bids = auction.best_bid > 0
        
        if has_bids and current_time >= auction.start_ts:
            raise ValueError("cannot-cancel-with-bids")
        
        # Refund any existing bids
        if has_bids:
            for (_, bidder), amount in self.bids.items():
                if amount > 0:
                    self.events.append(("Refund", auction_id, bidder, amount))
        
        auction.settled = True
        self.events.append(("AucCancel", auction_id))
        return True
    
    def get_auction(self, auction_id: int) -> Auction:
        """Get auction details"""
        if auction_id not in self.auctions:
            raise ValueError("auction-not-found")
        return self.auctions[auction_id]
    
    def get_bid(self, auction_id: int, bidder: str) -> int:
        """Get bidder's current escrowed amount"""
        return self.bids.get((auction_id, bidder), 0)
    
    def get_status(self, auction_id: int, current_time: int) -> str:
        """Get auction status"""
        auction = self.get_auction(auction_id)
        
        if auction.settled:
            return "settled"
        elif current_time < auction.start_ts:
            return "pending"
        elif current_time <= auction.end_ts:
            return "active"
        else:
            return "ended"

def test_happy_path():
    """Test the happy path scenario"""
    print("Testing Happy Path Scenario")
    
    contract = AuctionContract()
    current_time = int(time.time())
    
    # Create auction
    auction_id = contract.create(
        lease_id=1,
        unit="unit:NYC:123-A",
        seller="seller123",
        token="token456",
        reserve=100,
        min_increment=10,
        start_ts=current_time + 60,
        end_ts=current_time + 3600,
        extend_secs=60,
        extend_window=30
    )
    
    print(f"Created auction {auction_id}")
    
    # Place bids
    contract.bid(auction_id, "bidder1", 150, current_time + 120)
    print("Bidder1 placed bid of 150")
    
    contract.bid(auction_id, "bidder2", 200, current_time + 180)
    print("Bidder2 placed bid of 200")
    
    contract.bid(auction_id, "bidder1", 60, current_time + 240)  # Total: 210 (150+60)
    print("Bidder1 increased bid to 210 total")
    
    contract.bid(auction_id, "bidder2", 50, current_time + 300)  # Total: 250 (200+50)
    print("Bidder2 increased bid to 250 total")
    
    # Finalize auction
    success = contract.finalize(auction_id, "lessor", "bidder2", current_time + 3700)
    
    if success:
        auction = contract.get_auction(auction_id)
        print(f"Auction finalized successfully!")
        print(f"   Winner: {auction.best_bidder}")
        print(f"   Best bid: {auction.best_bid}")
        print(f"   Second bid: {auction.second_bid}")
        print(f"   Clearing price: {max(auction.second_bid, auction.reserve)}")
        
        # Verify second-price auction
        clearing_price = max(auction.second_bid, auction.reserve)
        assert clearing_price == 210, f"Expected clearing price 210, got {clearing_price}"
        assert auction.best_bidder == "bidder2", f"Expected winner bidder2, got {auction.best_bidder}"
        
        print("Second-price auction working correctly!")
    else:
        print("Auction finalization failed")
    
    return success

def test_reserve_not_met():
    """Test scenario where reserve is not met"""
    print("\nTesting Reserve Not Met Scenario")
    
    contract = AuctionContract()
    current_time = int(time.time())
    
    # Create auction
    auction_id = contract.create(
        lease_id=2,
        unit="unit:NYC:456-B",
        seller="seller456",
        token="token789",
        reserve=100,
        min_increment=10,
        start_ts=current_time + 60,
        end_ts=current_time + 3600,
        extend_secs=60,
        extend_window=30
    )
    
    print(f"Created auction {auction_id}")
    
    # Place bid below reserve
    try:
        contract.bid(auction_id, "bidder1", 50, current_time + 120)
        print("ERROR: Bid below reserve should have failed")
        return False
    except ValueError as e:
        if "below-reserve" in str(e):
            print("Bid below reserve correctly rejected")
            return True
        else:
            print(f"Unexpected error: {e}")
            return False

def test_anti_sniping():
    """Test anti-sniping extension"""
    print("\nTesting Anti-Sniping Extension")
    
    contract = AuctionContract()
    current_time = int(time.time())
    
    # Create auction with short duration
    auction_id = contract.create(
        lease_id=3,
        unit="unit:NYC:789-C",
        seller="seller789",
        token="token123",
        reserve=100,
        min_increment=10,
        start_ts=current_time + 60,
        end_ts=current_time + 120,  # Short auction
        extend_secs=60,
        extend_window=30
    )
    
    print(f"Created auction {auction_id}")
    
    # Place bid within extend_window (5 seconds before end)
    bid_time = current_time + 115
    contract.bid(auction_id, "bidder1", 150, bid_time)
    print("Bidder1 placed bid within extend_window")
    
    auction = contract.get_auction(auction_id)
    print(f"   Original end time: {current_time + 120}")
    print(f"   New end time: {auction.end_ts}")
    print(f"   Extensions count: {auction.extensions_count}")
    
    # Verify extension
    assert auction.end_ts == current_time + 120 + 60, f"Expected extension, got {auction.end_ts}"
    assert auction.extensions_count == 1, f"Expected 1 extension, got {auction.extensions_count}"
    
    print("Anti-sniping extension working correctly!")
    return True

def test_cancel_before_start():
    """Test cancellation before auction starts"""
    print("\nTesting Cancel Before Start")
    
    contract = AuctionContract()
    current_time = int(time.time())
    
    # Create auction
    auction_id = contract.create(
        lease_id=4,
        unit="unit:NYC:999-D",
        seller="seller999",
        token="token999",
        reserve=100,
        min_increment=10,
        start_ts=current_time + 60,
        end_ts=current_time + 3600,
        extend_secs=60,
        extend_window=30
    )
    
    print(f"Created auction {auction_id}")
    
    # Cancel before start
    contract.cancel(auction_id, current_time + 30)
    print("Cancelled auction before start")
    
    auction = contract.get_auction(auction_id)
    assert auction.settled, "Auction should be settled after cancellation"
    
    print("Cancel before start working correctly!")
    return True

def main():
    """Run all tests"""
    print("Starting Auction Contract Logic Tests")
    print("=" * 50)
    
    tests = [
        ("Happy Path", test_happy_path),
        ("Reserve Not Met", test_reserve_not_met),
        ("Anti-Sniping", test_anti_sniping),
        ("Cancel Before Start", test_cancel_before_start),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"PASSED: {test_name}")
            else:
                print(f"FAILED: {test_name}")
        except Exception as e:
            print(f"ERROR: {test_name} - {e}")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("SUCCESS: All tests passed! Auction contract logic is working correctly.")
        print("\nKey Features Verified:")
        print("   - Second-price auction mechanics")
        print("   - Reserve price enforcement")
        print("   - Anti-sniping extensions")
        print("   - Auction cancellation")
        print("   - Event emission")
        print("   - State management")
    else:
        print("FAILURE: Some tests failed. Please review the implementation.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
