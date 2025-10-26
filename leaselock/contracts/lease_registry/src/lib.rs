#![no_std]
mod types;
mod storage;

use soroban_sdk::{contract, contractimpl, Env, Address, BytesN, Symbol, Vec};
use types::Node;
use storage::*;

fn sym(s: &str) -> Symbol { Symbol::short(s) }

#[contract]
pub struct LeaseRegistry;

#[contractimpl]
impl LeaseRegistry {
    pub fn create_master(
        e: Env,
        unit: Symbol,
        landlord: Address,
        master: Address,
        terms: BytesN<32>,
        limit: u32,
        expiry_ts: u64,
    ) -> u64 {
        landlord.require_auth();
        if limit == 0 { panic!("limit-0"); }
        if expiry_ts == 0 { panic!("bad-expiry"); }
        let id = next_id(&e);

        let mut m = get_leases(&e);
        let node = Node {
            id,
            parent: None,
            unit: unit.clone(),
            lessor: landlord.clone(),
            lessee: master.clone(),
            depth: 0,
            terms,
            limit,
            expiry_ts,
            accepted: false,
            active: false,
        };
        m.set(id, node);
        put_leases(&e, &m);

        e.events().publish((sym("Lease"), unit, id), master);
        id
    }

    pub fn accept(e: Env, id: u64) {
        let mut m = get_leases(&e);
        let mut n = m.get(id).expect("unknown");
        n.lessee.require_auth();
        if n.accepted { return; }
        n.accepted = true;
        m.set(id, n);
        put_leases(&e, &m);
        e.events().publish((sym("Accept"), id), ());
    }

    pub fn create_sublease(
        e: Env,
        parent_id: u64,
        sublessee: Address,
        terms: BytesN<32>,
        limit: u32,
        expiry_ts: u64,
    ) -> u64 {
        let mut m = get_leases(&e);
        let parent = m.get(parent_id).expect("parent");
        parent.lessee.require_auth();
        if terms != parent.terms { panic!("terms-mismatch"); }
        if limit == 0 { panic!("limit-0"); }
        if expiry_ts == 0 { panic!("bad-expiry"); }
        if sublessee == parent.lessee { panic!("self-sublease"); }

        let mut ch = get_kids(&e);
        let mut v = ch.get(parent_id).unwrap_or(Vec::new(&e));
        if (v.len() as u32) >= parent.limit { panic!("limit"); }

        let id = next_id(&e);
        let node = Node {
            id,
            parent: Some(parent_id),
            unit: parent.unit.clone(),
            lessor: parent.lessee.clone(),
            lessee: sublessee.clone(),
            depth: parent.depth + 1,
            terms,
            limit,
            expiry_ts,
            accepted: false,
            active: false,
        };
        m.set(id, node);
        put_leases(&e, &m);
        v.push_back(id);
        ch.set(parent_id, v);
        put_kids(&e, &ch);

        e.events().publish((sym("Sublease"), parent_id, id), sublessee);
        id
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use soroban_sdk::{testutils::Address as _, Env};

    #[test]
    fn graph_happy_path() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[0u8; 32]);

        e.mock_all_auths(); // for quick unit tests

        // Register the contract
        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(
            &unit,
            &landlord,
            &master,
            &terms,
            &2,
            &2_000_000_000,
        );
        client.accept(&root);
        let child = client.create_sublease(
            &root,
            &sub1,
            &terms,
            &1,
            &2_000_000_000,
        );
        assert!(child > 0);
    }

}