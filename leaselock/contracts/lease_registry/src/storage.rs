#![no_std]
use soroban_sdk::{Env, Map, Symbol, Vec};
use crate::types::Node;

pub fn k_next() -> Symbol { Symbol::short("next") }
pub fn k_leases() -> Symbol { Symbol::short("lease") }
pub fn k_kids() -> Symbol { Symbol::short("kids") }

pub fn next_id(e: &Env) -> u64 {
    let k = k_next();
    let mut n: u64 = e.storage().instance().get(&k).unwrap_or(0);
    n += 1;
    e.storage().instance().set(&k, &n);
    n
}

pub fn get_leases(e: &Env) -> Map<u64, Node> {
    e.storage().instance().get(&k_leases()).unwrap_or(Map::new(e))
}

pub fn put_leases(e: &Env, m: &Map<u64, Node>) {
    e.storage().instance().set(&k_leases(), m);
}

pub fn get_kids(e: &Env) -> Map<u64, Vec<u64>> {
    e.storage().instance().get(&k_kids()).unwrap_or(Map::new(e))
}

pub fn put_kids(e: &Env, m: &Map<u64, Vec<u64>>) {
    e.storage().instance().set(&k_kids(), m);
}
