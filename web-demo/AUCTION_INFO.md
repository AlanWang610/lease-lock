# Second-Price Auction Information

## What is a Second-Price Auction?

A second-price auction (also known as a Vickrey auction) is a bidding mechanism where:

1. **Highest bidder wins** the item
2. **Winner pays the second-highest bid**, not their own bid
3. This encourages **honest bidding** - you can bid what the item is truly worth to you

## How It Works

### Example Scenario

Imagine an auction for a unit with these bids:
- Bidder A: 5.0 XLM
- Bidder B: 7.5 XLM (highest)
- Bidder C: 4.0 XLM
- Bidder D: 3.5 XLM

**Result**: 
- Winner: Bidder B
- Payment: 5.0 XLM (second-highest bid from Bidder A)
- Refund: 2.5 XLM (difference between Bidder B's bid of 7.5 and payment of 5.0)

### Why This Is Better

**Traditional Auction Problems:**
- Bidders may underbid to avoid overpaying
- Creates uncertainty about true value
- Winner's curse - winner overpays

**Second-Price Auction Benefits:**
- ✅ Encourages honest valuations
- ✅ Reduces winner's curse
- ✅ Creates efficient price discovery
- ✅ Winner gets a refund if they overbid

## Your Bidding Strategy

1. **Bid honestly** - What is this unit worth to you?
2. **Don't worry about overbidding** - You only pay the second-highest price
3. **If you win**, you get back any excess payment above the second-highest bid
4. **If you lose**, you pay nothing (in a second-price auction, losers don't pay)

## Real Auction Features

The lease-lock auction system includes:

- **Escrowed bids**: All bids are held in the contract until settlement
- **Automatic settlement**: Winner's price and refunds are processed automatically
- **Anti-sniping protection**: Auction extends if bids come in near the end
- **Lease integration**: Winner automatically gets a sublease created

## Code References

### Working Demo Scripts

1. **`client/scripts/06_auction_demo.py`**
   - Complete auction flow demonstration
   - Creates auction, places bids, finalizes
   - Shows second-price settlement

2. **`client/scripts/test_auction.py`**
   - Unit tests for auction contract
   - Tests bidding, finalization, second-price logic

3. **`client/scripts/test_auction_logic.py`**
   - Logic tests for auction mechanics
   - Validates second-price calculation

### Contract Implementation

Located in `leaselock/contracts/auction/src/lib.rs`:
- `create()` - Create auction with reserve price
- `bid()` - Place a bid (escrowed)
- `finalize()` - Settle auction with second-price
- `query()` - Get auction details

### Auction Contract Features

```rust
// Calculate clearing price (second price)
let clearing_price = if auction.second_bid > auction.reserve {
    auction.second_bid
} else {
    auction.reserve
};

// Pay seller the clearing price
token_client.transfer(&contract_addr, &auction.seller, &clearing_price);

// Refund winner (best_bid - clearing_price)
let winner_refund = auction.best_bid - clearing_price;
if winner_refund > 0 {
    token_client.transfer(&contract_addr, &auction.best_bidder, &winner_refund);
}
```

## Web Demo Integration

The web demo currently simulates the auction:

1. **Input**: User enters bid amount
2. **Processing**: Bid is validated (minimum 3.5 XLM)
3. **Feedback**: Shows second-price explanation
4. **Future**: Will integrate with real auction contract

### Future Enhancement

To make the auction use real blockchain transactions:

1. Connect to deployed auction contract
2. Call `bid()` function with user's bid
3. Escrow XLM in the contract
4. When auction ends, call `finalize()`
5. Automatic settlement with refund processing

## Resources

- [Vickrey Auction Wikipedia](https://en.wikipedia.org/wiki/Vickrey_auction)
- [Second-Price Auction Explained](https://www.investopedia.com/terms/v/vickrey-auction.asp)
- [Auction Contract README](leaselock/contracts/auction/README.md)

