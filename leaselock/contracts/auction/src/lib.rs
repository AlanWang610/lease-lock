#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, Address, Env, Symbol, Map, 
    symbol_short
};
use soroban_sdk::token;

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Auction {
    pub id: u64,
    pub lease_id: u64,
    pub seller: Address,
    pub unit: Symbol,
    pub token: Address,
    pub reserve: i128,
    pub min_increment: i128,
    pub start_ts: u64,
    pub end_ts: u64,
    pub extend_secs: u64,
    pub extend_window: u64,
    pub max_extensions: u32,
    pub extensions_count: u32,
    pub best_bid: i128,
    pub best_bidder: Address,
    pub second_bid: i128,
    pub settled: bool,
}

fn sym(s: &str) -> Symbol { 
    match s {
        "auctions" => symbol_short!("auctions"),
        "bids" => symbol_short!("bids"),
        "next_id" => symbol_short!("next_id"),
        "AuctionCreated" => symbol_short!("AucCreate"),
        "BidPlaced" => symbol_short!("BidPlaced"),
        "AuctionExtended" => symbol_short!("AucExtend"),
        "AuctionFinalized" => symbol_short!("AucFinal"),
        "AuctionFailed" => symbol_short!("AucFailed"),
        "RefundIssued" => symbol_short!("Refund"),
        "AuctionCanceled" => symbol_short!("AucCancel"),
        "settled" => symbol_short!("settled"),
        "pending" => symbol_short!("pending"),
        "active" => symbol_short!("active"),
        "ended" => symbol_short!("ended"),
        _ => symbol_short!("unknown"),
    }
}

#[contract]
pub struct AuctionContract;

#[contractimpl]
impl AuctionContract {
    // Storage keys
    fn k_auctions() -> Symbol { sym("auctions") }
    fn k_bids() -> Symbol { sym("bids") }
    fn k_next_id() -> Symbol { sym("next_id") }

    /// Create a new auction for a sublease
    pub fn create(
        e: Env,
        lease_id: u64,
        unit: Symbol,
        seller: Address,
        token: Address,
        reserve: i128,
        min_increment: i128,
        start_ts: u64,
        end_ts: u64,
        extend_secs: u64,
        extend_window: u64,
    ) -> u64 {
        seller.require_auth();
        
        // Validation
        if start_ts >= end_ts { panic!("invalid-times"); }
        if reserve <= 0 { panic!("invalid-reserve"); }
        if min_increment <= 0 { panic!("invalid-increment"); }
        if extend_window == 0 { panic!("invalid-extend-window"); }
        if extend_secs == 0 { panic!("invalid-extend-secs"); }
        let max_extensions = 10u32; // Fixed cap

        let id = Self::next_id(&e);
        let auction = Auction {
            id,
            lease_id,
            seller: seller.clone(),
            unit: unit.clone(),
            token: token.clone(),
            reserve,
            min_increment,
            start_ts,
            end_ts,
            extend_secs,
            extend_window,
            max_extensions,
            extensions_count: 0,
            best_bid: 0,
            best_bidder: seller.clone(), // dummy address, will be updated on first bid
            second_bid: 0,
            settled: false,
        };

        let mut auctions = Self::get_auctions(&e);
        auctions.set(id, auction);
        Self::put_auctions(&e, &auctions);

        e.events().publish((sym("AuctionCreated"), id), (lease_id, seller, unit, reserve));
        id
    }

    /// Place a bid on an auction
    pub fn bid(e: Env, auction_id: u64, bidder: Address, amount: i128) {
        bidder.require_auth();
        
        if amount <= 0 { panic!("invalid-amount"); }

        let mut auctions = Self::get_auctions(&e);
        let mut auction = auctions.get(auction_id).expect("auction-not-found");
        
        // Validation
        if auction.settled { panic!("auction-settled"); }
        let now = e.ledger().timestamp();
        if now < auction.start_ts { panic!("auction-not-started"); }
        if now > auction.end_ts { panic!("auction-ended"); }

        // Transfer tokens from bidder to contract
        let token_client = token::Client::new(&e, &auction.token);
        let contract_addr = e.current_contract_address();
        token_client.transfer_from(&bidder, &bidder, &contract_addr, &amount);

        // Update bidder's total escrowed amount
        let mut bids = Self::get_bids(&e);
        let current_bid = bids.get((auction_id, bidder.clone())).unwrap_or(0);
        let new_total = current_bid + amount;
        bids.set((auction_id, bidder.clone()), new_total);
        Self::put_bids(&e, &bids);

        // Check if bid meets requirements
        if new_total < auction.reserve { panic!("below-reserve"); }
        if new_total < auction.best_bid + auction.min_increment { panic!("insufficient-increment"); }

        // Update auction state
        auction.second_bid = auction.best_bid;
        auction.best_bid = new_total;
        auction.best_bidder = bidder.clone();

        // Anti-sniping: extend auction if bid is within extend_window
        if auction.extensions_count < auction.max_extensions {
            let time_remaining = auction.end_ts - now;
            if time_remaining <= auction.extend_window {
                auction.end_ts += auction.extend_secs;
                auction.extensions_count += 1;
                e.events().publish((sym("AuctionExtended"), auction_id), auction.end_ts);
            }
        }

        let end_ts = auction.end_ts;
        auctions.set(auction_id, auction);
        Self::put_auctions(&e, &auctions);

        e.events().publish((sym("BidPlaced"), auction_id), (bidder, new_total, now, end_ts));
    }

    /// Finalize the auction and settle payments
    pub fn finalize(
        e: Env, 
        auction_id: u64, 
        _lessor: Address, 
        _new_lessee: Address
    ) {
        let mut auctions = Self::get_auctions(&e);
        let mut auction = auctions.get(auction_id).expect("auction-not-found");
        
        // Validation
        if auction.settled { panic!("already-settled"); }
        let now = e.ledger().timestamp();
        if now < auction.end_ts { panic!("auction-not-ended"); }
        auction.seller.require_auth();

        let token_client = token::Client::new(&e, &auction.token);
        let contract_addr = e.current_contract_address();

        // Check if reserve was met
        if auction.best_bid < auction.reserve {
            // Refund all bidders
            let bids = Self::get_bids(&e);
            for (_, bidder) in bids.keys() {
                if let Some(amount) = bids.get((auction_id, bidder.clone())) {
                    if amount > 0 {
                        token_client.transfer(&contract_addr, &bidder, &amount);
                        e.events().publish((sym("RefundIssued"), auction_id), (bidder, amount));
                    }
                }
            }
            
            auction.settled = true;
            let reserve_price = auction.reserve;
            auctions.set(auction_id, auction);
            Self::put_auctions(&e, &auctions);
            
            e.events().publish((sym("AuctionFailed"), auction_id), reserve_price);
            return;
        }

        // Calculate clearing price (second price)
        let clearing_price = if auction.second_bid > auction.reserve {
            auction.second_bid
        } else {
            auction.reserve
        };

        // Pay seller
        token_client.transfer(&contract_addr, &auction.seller, &clearing_price);

        // Refund winner (best_bid - clearing_price)
        let winner_refund = auction.best_bid - clearing_price;
        if winner_refund > 0 {
            token_client.transfer(&contract_addr, &auction.best_bidder, &winner_refund);
        }

        // Refund all other bidders
        let bids = Self::get_bids(&e);
        for (_, bidder) in bids.keys() {
            if bidder != auction.best_bidder {
                if let Some(amount) = bids.get((auction_id, bidder.clone())) {
                    if amount > 0 {
                        token_client.transfer(&contract_addr, &bidder, &amount);
                        e.events().publish((sym("RefundIssued"), auction_id), (bidder, amount));
                    }
                }
            }
        }

        // Clear bids for this auction
        let mut bids = Self::get_bids(&e);
        for (_, bidder) in bids.keys() {
            bids.remove((auction_id, bidder.clone()));
        }
        Self::put_bids(&e, &bids);

        auction.settled = true;
        let winner = auction.best_bidder.clone();
        let lease_id = auction.lease_id;
        auctions.set(auction_id, auction);
        Self::put_auctions(&e, &auctions);

        e.events().publish((sym("AuctionFinalized"), auction_id), 
            (winner, clearing_price, lease_id));
    }

    /// Cancel an auction (only if no bids or before start)
    pub fn cancel(e: Env, auction_id: u64) {
        let mut auctions = Self::get_auctions(&e);
        let mut auction = auctions.get(auction_id).expect("auction-not-found");
        
        auction.seller.require_auth();
        if auction.settled { panic!("already-settled"); }

        let now = e.ledger().timestamp();
        let has_bids = auction.best_bid > 0;
        
        if has_bids && now >= auction.start_ts { panic!("cannot-cancel-with-bids"); }

        // Refund any existing bids
        if has_bids {
            let token_client = token::Client::new(&e, &auction.token);
            let contract_addr = e.current_contract_address();
            let bids = Self::get_bids(&e);
            
            for (_, bidder) in bids.keys() {
                if let Some(amount) = bids.get((auction_id, bidder.clone())) {
                    if amount > 0 {
                        token_client.transfer(&contract_addr, &bidder, &amount);
                        e.events().publish((sym("RefundIssued"), auction_id), (bidder, amount));
                    }
                }
            }
        }

        auction.settled = true;
        auctions.set(auction_id, auction);
        Self::put_auctions(&e, &auctions);

        e.events().publish((sym("AuctionCanceled"), auction_id), ());
    }

    /// Get auction details
    pub fn get_auction(e: Env, auction_id: u64) -> Auction {
        let auctions = Self::get_auctions(&e);
        auctions.get(auction_id).expect("auction-not-found")
    }

    /// Get bidder's current escrowed amount
    pub fn get_bid(e: Env, auction_id: u64, bidder: Address) -> i128 {
        let bids = Self::get_bids(&e);
        bids.get((auction_id, bidder)).unwrap_or(0)
    }

    /// Get auction status
    pub fn get_status(e: Env, auction_id: u64) -> Symbol {
        let auction = Self::get_auction(e.clone(), auction_id);
        let now = e.ledger().timestamp();
        
        if auction.settled {
            sym("settled")
        } else if now < auction.start_ts {
            sym("pending")
        } else if now <= auction.end_ts {
            sym("active")
        } else {
            sym("ended")
        }
    }

    // Helper functions for storage
    fn next_id(e: &Env) -> u64 {
        let k = Self::k_next_id();
        let mut n: u64 = e.storage().instance().get(&k).unwrap_or(0);
        n += 1;
        e.storage().instance().set(&k, &n);
        n
    }

    fn get_auctions(e: &Env) -> Map<u64, Auction> {
        e.storage().instance().get(&Self::k_auctions()).unwrap_or(Map::new(e))
    }

    fn put_auctions(e: &Env, auctions: &Map<u64, Auction>) {
        e.storage().instance().set(&Self::k_auctions(), auctions);
    }

    fn get_bids(e: &Env) -> Map<(u64, Address), i128> {
        e.storage().instance().get(&Self::k_bids()).unwrap_or(Map::new(e))
    }

    fn put_bids(e: &Env, bids: &Map<(u64, Address), i128>) {
        e.storage().instance().set(&Self::k_bids(), bids);
    }
}
