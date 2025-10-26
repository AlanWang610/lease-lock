# Auction Recording on Stellar Network

## Current State

**The UI currently simulates auction bidding** for demo purposes, but the infrastructure is ready for real blockchain integration.

## How Auctions Would Be Recorded

When fully integrated, auctions would be recorded on the Stellar network in these ways:

### 1. **Soroban Smart Contract Storage**

The auction contract uses **instance storage** to store:

```rust
// Auction data stored on-chain
Map<u64, Auction> auctions {
    id -> {
        lease_id, seller, unit, token,
        reserve, best_bid, best_bidder,
        second_bid, start_ts, end_ts,
        settled, extensions_count
    }
}

// Bids escrowed in contract  
Map<(u64, Address), i128> bids {
    (auction_id, bidder_address) -> escrowed_amount
}
```

**Storage location**: On-chain in the Soroban contract's instance storage
**Persistent**: Yes, stored in the ledger permanently
**Queryable**: Yes, via contract query functions

### 2. **Event Emission** (Transaction History)

Every auction action emits events:

- `AuctionCreated` - When auction is created
- `BidPlaced` - When a bid is placed
- `AuctionExtended` - When auction auto-extends
- `AuctionFinalized` - When auction settles
- `RefundIssued` - When bidders get refunded

**Location**: Stellar ledger event stream
**Accessible**: Via Soroban RPC or Horizon API
**Queryable**: Yes, can filter by auction_id, bidder, etc.

### 3. **Token Escrow** (Viewable on stellar.expert)

When you place a bid:

1. **Approve**: Token contract approves auction contract to spend
2. **Transfer**: Tokens are transferred from your account to the auction contract
3. **Escrow**: Tokens held in contract until auction ends

**This transfer is visible on stellar.expert:**
- Account: Auction contract address
- Operation: Payment/transfer to escrow
- Amount: Your bid amount
- Asset: XLM (or other SAC token)
- Transaction hash: Linkable to the bid event

### 4. **What You See on stellar.expert**

When bidding, you can view:

**Account View:**
- Auction contract account shows escrowed balances
- See all bidders' escrowed amounts
- See contract's token holdings

**Transaction View:**
- Your transfer to the contract (escrow)
- Contract's internal bid processing
- Refund transactions (if any)

**Contract View:**
- Auction instance data (via query)
- All active auctions
- Historical auction data

## Current Implementation

The UI has:
- ✅ API endpoint: `/api/place-bid`
- ✅ Function stub: `execute_place_bid()`
- ✅ Ready to call the auction contract
- ⏳ Waiting for: Deployed auction contract address

**To make it fully real:**

1. **Deploy auction contract** to testnet/mainnet
2. **Add `AUCTION_CONTRACT_ID`** to config.env
3. **Implement token approval** (for SAC tokens)
4. **Call contract.bid()** with real parameters
5. **Return transaction hash** for stellar.expert link

## Escrow Visibility

Once fully integrated, escrowed tokens would be visible:

### On stellar.expert:

**Search for:**
- Contract address (the auction contract)
- Your account (to see transfers)
- Transaction hash (from the bid response)

**What you'd see:**
1. Transaction: "Transfer to contract"
2. Amount: Your bid in XLM
3. From: Your account
4. To: Auction contract
5. Memo/Tags: Auction ID, bidder

### In the Contract Storage:

- **Query auction**: `GET /contracts/{auction_id}`
- **See escrowed bids**: All bidders' amounts
- **View auction state**: Best bid, second bid, time left
- **Check if settled**: Settlement status

## Integration Path

To connect real auctions:

1. **Backend** (`demo_runner.py`):
   ```python
   # Need to implement:
   - Token approval transaction
   - Auction bid transaction  
   - Return real tx hash
   ```

2. **Frontend** (`script.js`):
   ```javascript
   // Already implemented!
   - Calls /api/place-bid
   - Shows transaction hash
   - Links to stellar.expert
   - Explains escrow system
   ```

3. **Config** (`config.env`):
   ```env
   AUCTION_CONTRACT_ID=CD...
   TOKEN_CONTRACT_ID=...
   ```

## Example: What Transaction Would Look Like

```
Transaction Hash: abc123...
From: GYOURACCOUNT
To: CAUCTIONCONTRACT
Amount: 5.0 XLM
Type: Payment
Memo: Auction 1, Bidder: GYOURACCOUNT
Status: Confirmed

Contract Storage:
- Auction 1: best_bid = 5.0 XLM
- Bids: (auction_id=1, bidder=GYOURACCOUNT) = 5.0 XLM
```

## Summary

- **Current**: Simulated bids (for demo)
- **Ready for**: Real blockchain integration
- **When real**: Bids escrowed on-chain, viewable on stellar.expert
- **Infrastructure**: Contract storage + events + token escrow
- **Visibility**: All transactions public and queryable

The UI is ready for real auctions once the contract is deployed!

