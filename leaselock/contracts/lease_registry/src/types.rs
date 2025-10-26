#![no_std]
use soroban_sdk::{contracttype, Address, BytesN, Symbol};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Node {
    pub id: u64,
    pub parent: Option<u64>,
    pub unit: Symbol,
    pub lessor: Address,
    pub lessee: Address,
    pub depth: u32,
    pub terms: BytesN<32>,   // 32-byte hash of canonical terms
    pub limit: u32,          // max direct children
    pub expiry_ts: u64,      // unix seconds
    pub accepted: bool,
    pub active: bool,
}
