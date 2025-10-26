# Auction Contract

A Soroban smart contract implementing second-price auctions for sublease transfers. This contract enables competitive bidding on subleases with escrowed payments and automatic settlement at the second-highest price.

## Features

- **Second-Price Auction**: Winner pays the second-highest bid price, encouraging truthful bidding
- **Escrowed Bids**: All bid amounts are held in the contract until settlement
- **Anti-Sniping**: Auction extends automatically if bids arrive near the end
- **Capped Extensions**: Maximum number of extensions prevents indefinite auctions
- **LeaseRegistry Integration**: Emits events for client-driven sublease creation
- **SAC Token Support**: Compatible with Stellar Asset Contracts

## Auction Mechanics

### Second-Price Auction
The winner pays `max(second_highest_bid, reserve_price)` instead of their actual bid. This encourages bidders to bid their true valuation without fear of overpaying.

### Anti-Sniping Protection
If a bid is placed within the `extend_window` seconds of the auction end, the auction extends by `extend_secs` seconds. This prevents last-second sniping but is capped at `max_extensions` (default: 10) to prevent indefinite auctions.

### Escrow System
- All bids are immediately transferred to the contract
- Losers receive full refunds
- Winner receives refund of `(their_bid - clearing_price)`
- Seller receives the clearing price

## Contract API

### `create(lease_id, unit, seller, token, reserve, min_increment, start_ts, end_ts, extend_secs, extend_window) -> u64`

Creates a new auction for a sublease.

**Parameters:**
- `lease_id`: ID of the lease being auctioned
- `unit`: Unit identifier (e.g., "unit:NYC:123-A")
- `seller`: Address of the current lessee selling the sublease
- `token`: Address of the token contract for bids
- `reserve`: Minimum acceptable bid amount
- `min_increment`: Minimum increase required for new bids
- `start_ts`: Unix timestamp when auction starts
- `end_ts`: Unix timestamp when auction ends
- `extend_secs`: Seconds to extend auction on anti-sniping
- `extend_window`: Seconds before end when extension triggers

**Returns:** Auction ID

**Events:** `AucCreate(auction_id, lease_id, seller, unit, reserve)`

### `bid(auction_id, bidder, amount)`

Places a bid on an auction. Bids are cumulative - multiple calls add to the bidder's total.

**Parameters:**
- `auction_id`: ID of the auction
- `bidder`: Address of the bidder (must match transaction signer)
- `amount`: Additional amount to add to bidder's total

**Requirements:**
- Auction must be active (between start_ts and end_ts)
- New total must be >= reserve price
- New total must be >= (current_best_bid + min_increment)
- Bidder must have approved contract to spend tokens

**Events:** 
- `BidPlaced(auction_id, bidder, total_amount, timestamp, end_ts)`
- `AucExtend(auction_id, new_end_ts)` (if extension triggered)

### `finalize(auction_id, lessor, new_lessee)`

Settles the auction and distributes payments.

**Parameters:**
- `auction_id`: ID of the auction
- `lessor`: Address of the lessor (for LeaseRegistry integration)
- `new_lessee`: Address of the new lessee (typically the winner)

**Requirements:**
- Auction must be ended (current time >= end_ts)
- Only seller can call finalize
- Auction must not already be settled

**Settlement Logic:**
1. If best_bid < reserve: refund all bidders, emit `AucFailed`
2. Calculate clearing_price = max(second_bid, reserve)
3. Transfer clearing_price to seller
4. Refund winner: (best_bid - clearing_price)
5. Refund all losers: their full bid amounts
6. Emit `AucFinal(auction_id, winner, clearing_price, lease_id)`

### `cancel(auction_id)`

Cancels an auction before it starts or if no valid bids exist.

**Requirements:**
- Only seller can cancel
- Cannot cancel if auction has started and has valid bids

**Events:** `AucCancel(auction_id)`

### Query Functions

#### `get_auction(auction_id) -> Auction`
Returns the complete auction struct.

#### `get_bid(auction_id, bidder) -> i128`
Returns the total amount escrowed by a specific bidder.

#### `get_status(auction_id) -> Symbol`
Returns auction status: "pending", "active", "ended", or "settled".

## Integration with LeaseRegistry

The auction contract uses a **client-driven integration** pattern:

1. **Auction Creation**: Seller creates auction for existing lease
2. **Bidding**: Multiple bidders place competitive bids
3. **Finalization**: Auction settles with second-price payment
4. **Sublease Creation**: Client listens for `AucFinal` event and calls LeaseRegistry:
   - `create_sublease(parent_id, winner, terms, limit, expiry)`
   - Winner calls `accept()`
   - Lessor calls `set_active()`

## Usage Example

```python
# Create auction
auction_id = auction_client.create(
    lease_id=1,
    unit="unit:NYC:123-A",
    seller=tenant_address,
    token=token_address,
    reserve=100,
    min_increment=10,
    start_ts=current_time + 60,
    end_ts=current_time + 3600,
    extend_secs=60,
    extend_window=30
)

# Place bids
token_client.approve(bidder, auction_contract, 200)
auction_client.bid(auction_id, bidder1, 150)
auction_client.bid(auction_id, bidder2, 200)

# Finalize auction
auction_client.finalize(auction_id, landlord, winner)

# Create sublease for winner (client-driven)
lease_client.create_sublease(parent_id, winner, terms, limit, expiry)
winner_client.accept(sublease_id)
landlord_client.set_active(sublease_id)
```

## Security Considerations

- **Reentrancy**: No external calls before state updates
- **Integer Safety**: Uses `i128` for amounts with overflow checks
- **Authorization**: All functions require proper authentication
- **Escrow Safety**: All funds held in contract until settlement
- **Extension Limits**: Capped extensions prevent indefinite auctions

## Events

All events use short symbols (≤9 characters) for Soroban compatibility:

- `AucCreate`: Auction created
- `BidPlaced`: Bid placed
- `AucExtend`: Auction extended
- `AucFinal`: Auction finalized
- `AucFailed`: Auction failed (reserve not met)
- `Refund`: Refund issued
- `AucCancel`: Auction canceled

## Testing

The contract includes comprehensive unit tests covering:

- Happy path: create → bid → finalize with second-price settlement
- Reserve not met: all refunds
- Anti-sniping extension (capped)
- Tie handling (first to amount wins)
- Cancellation scenarios

Run tests with:
```bash
cd leaselock
cargo test -p auction
```

## Building

Build the contract to WASM:
```bash
cd leaselock
cargo build --release --target wasm32-unknown-unknown -p auction
```

The compiled contract will be available at:
`target/wasm32-unknown-unknown/release/auction.wasm`
