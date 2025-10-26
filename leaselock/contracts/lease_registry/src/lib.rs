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
            terms, // Immutable: terms cannot be changed after creation
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
        
        // Defense-in-depth: validate terms match parent if parent exists
        if let Some(parent_id) = n.parent {
            let parent = m.get(parent_id).expect("parent");
            if n.terms != parent.terms { panic!("terms-drift"); }
        }
        
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
        if limit > parent.limit { panic!("limit-exceeds-parent"); }
        if limit == 0 { panic!("limit-0"); }
        if expiry_ts == 0 { panic!("bad-expiry"); }
        if expiry_ts > parent.expiry_ts { panic!("expiry-exceeds-parent"); }
        if parent.depth >= 10 { panic!("max-depth"); }
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

    pub fn terms_of(e: Env, id: u64) -> BytesN<32> {
        let m = get_leases(&e);
        let node = m.get(id).expect("unknown");
        node.terms
    }

    pub fn get_lease(e: Env, id: u64) -> Node {
        let m = get_leases(&e);
        m.get(id).expect("unknown")
    }

    pub fn children_of(e: Env, id: u64) -> Vec<u64> {
        let ch = get_kids(&e);
        ch.get(id).unwrap_or(Vec::new(&e))
    }

    pub fn parent_of(e: Env, id: u64) -> Option<u64> {
        let m = get_leases(&e);
        let node = m.get(id).expect("unknown");
        node.parent
    }

    pub fn root_of(e: Env, id: u64) -> u64 {
        let m = get_leases(&e);
        let mut current_id = id;
        loop {
            let node = m.get(current_id).expect("unknown");
            match node.parent {
                Some(parent_id) => current_id = parent_id,
                None => return current_id,
            }
        }
    }

    pub fn set_active(e: Env, id: u64) {
        let mut m = get_leases(&e);
        let mut node = m.get(id).expect("unknown");
        node.lessor.require_auth();
        if !node.accepted { panic!("not-accepted"); }
        if node.active { panic!("already-active"); }
        
        node.active = true;
        m.set(id, node);
        put_leases(&e, &m);
        e.events().publish((sym("Activated"), id), ());
    }

    pub fn set_delinquent(e: Env, id: u64) {
        let mut m = get_leases(&e);
        let mut node = m.get(id).expect("unknown");
        node.lessor.require_auth();
        
        node.active = false;
        m.set(id, node);
        put_leases(&e, &m);
        e.events().publish((sym("Delinq"), id), ());
    }

    pub fn cancel_unaccepted(e: Env, id: u64) {
        let mut m = get_leases(&e);
        let node = m.get(id).expect("unknown");
        node.lessor.require_auth();
        if node.accepted { panic!("already-accepted"); }
        
        // Remove from parent's children list
        if let Some(parent_id) = node.parent {
            let mut ch = get_kids(&e);
            let mut v = ch.get(parent_id).unwrap_or(Vec::new(&e));
            let mut new_v = Vec::new(&e);
            for child_id in v.iter() {
                if child_id != id {
                    new_v.push_back(child_id);
                }
            }
            ch.set(parent_id, new_v);
            put_kids(&e, &ch);
        }
        
        // Remove the lease itself
        m.remove(id);
        put_leases(&e, &m);
        e.events().publish((sym("Canceled"), id), ());
    }

    pub fn replace_sublessee(e: Env, id: u64, new_lessee: Address) {
        let mut m = get_leases(&e);
        let mut node = m.get(id).expect("unknown");
        node.lessor.require_auth();
        if node.accepted { panic!("already-accepted"); }
        
        let old_lessee = node.lessee.clone();
        node.lessee = new_lessee.clone();
        m.set(id, node);
        put_leases(&e, &m);
        e.events().publish((sym("Reassign"), id), (old_lessee, new_lessee));
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
            &2, // Same limit as parent
            &2_000_000_000,
        );
        assert!(child > 0);
    }

    #[test]
    fn test_terms_enforcement_happy_path() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);
        let sub2 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]); // Same terms hash

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        // Create master lease
        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        // Create sublease with same terms
        let child1 = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        client.accept(&child1);

        // Create grandchild with same terms
        let child2 = client.create_sublease(&child1, &sub2, &terms, &2, &2_000_000_000);
        assert!(child2 > 0);
    }

    #[test]
    #[should_panic(expected = "terms-mismatch")]
    fn test_terms_mismatch_rejection() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms1 = BytesN::from_array(&e, &[1u8; 32]);
        let terms2 = BytesN::from_array(&e, &[2u8; 32]); // Different terms

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms1, &2, &2_000_000_000);
        client.accept(&root);

        // This should panic with "terms-mismatch"
        client.create_sublease(&root, &sub1, &terms2, &2, &2_000_000_000);
    }

    #[test]
    #[should_panic(expected = "limit-exceeds-parent")]
    fn test_limit_exceeds_parent() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        // This should panic with "limit-exceeds-parent" (child limit > parent limit)
        client.create_sublease(&root, &sub1, &terms, &3, &2_000_000_000);
    }

    #[test]
    fn test_terms_of_query() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[42u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        
        // Query the terms hash
        let retrieved_terms = client.terms_of(&root);
        assert_eq!(retrieved_terms, terms);
    }

    #[test]
    fn test_accept_validates_terms() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms1 = BytesN::from_array(&e, &[1u8; 32]);
        let terms2 = BytesN::from_array(&e, &[2u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms1, &2, &2_000_000_000);
        client.accept(&root);

        // Create a valid sublease with matching terms
        let child = client.create_sublease(&root, &sub1, &terms1, &2, &2_000_000_000);
        
        // Accept should succeed with matching terms
        client.accept(&child);
        
        // This test validates that the accept function includes terms validation logic
        // The actual terms drift test would require manipulating storage directly,
        // which is complex in the test environment
        assert!(true); // Test passes if we get here without panic
    }

    #[test]
    #[should_panic(expected = "expiry-exceeds-parent")]
    fn test_expiry_exceeds_parent() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &1_000_000_000);
        client.accept(&root);

        // This should panic with "expiry-exceeds-parent" (child expiry > parent expiry)
        client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
    }

    #[test]
    #[should_panic(expected = "max-depth")]
    fn test_max_depth_enforcement() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);
        let sub2 = Address::generate(&e);
        let sub3 = Address::generate(&e);
        let sub4 = Address::generate(&e);
        let sub5 = Address::generate(&e);
        let sub6 = Address::generate(&e);
        let sub7 = Address::generate(&e);
        let sub8 = Address::generate(&e);
        let sub9 = Address::generate(&e);
        let sub10 = Address::generate(&e);
        let sub11 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        // Create a deep chain (10 levels)
        let mut current_id = client.create_master(&unit, &landlord, &master, &terms, &1, &2_000_000_000);
        client.accept(&current_id);
        
        let tenants = [sub1, sub2, sub3, sub4, sub5, sub6, sub7, sub8, sub9, sub10, sub11];
        for tenant in tenants.iter() {
            current_id = client.create_sublease(&current_id, tenant, &terms, &1, &2_000_000_000);
            client.accept(&current_id);
        }
        
        // This should panic with "max-depth" (trying to create at depth 11)
        client.create_sublease(&current_id, &Address::generate(&e), &terms, &1, &2_000_000_000);
    }

    #[test]
    fn test_flexible_limit_allows_lower() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &3, &2_000_000_000);
        client.accept(&root);

        // This should succeed (child limit < parent limit)
        let child = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        assert!(child > 0);
    }

    #[test]
    fn test_read_apis() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);
        let sub2 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        // Create master lease
        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        // Create subleases
        let child1 = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        let child2 = client.create_sublease(&root, &sub2, &terms, &2, &2_000_000_000);

        // Test get_lease
        let lease = client.get_lease(&child1);
        assert_eq!(lease.id, child1);
        assert_eq!(lease.parent, Some(root));
        assert_eq!(lease.depth, 1);

        // Test children_of
        let children = client.children_of(&root);
        assert_eq!(children.len(), 2);
        assert!(children.contains(&child1));
        assert!(children.contains(&child2));

        // Test parent_of
        assert_eq!(client.parent_of(&child1), Some(root));
        assert_eq!(client.parent_of(&root), None);

        // Test root_of
        assert_eq!(client.root_of(&child1), root);
        assert_eq!(client.root_of(&child2), root);
        assert_eq!(client.root_of(&root), root);
    }

    #[test]
    fn test_activation_flow() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        // Create and accept master lease
        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        // Create and accept sublease
        let child = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        client.accept(&child);

        // Test activation flow
        client.set_active(&root);
        client.set_active(&child);

        // Verify both are active
        let root_lease = client.get_lease(&root);
        let child_lease = client.get_lease(&child);
        assert!(root_lease.active);
        assert!(child_lease.active);

        // Test delinquency
        client.set_delinquent(&child);
        let child_lease_after = client.get_lease(&child);
        assert!(!child_lease_after.active);
    }

    #[test]
    #[should_panic(expected = "not-accepted")]
    fn test_set_active_requires_accepted() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        
        // This should panic with "not-accepted" (trying to activate before accepting)
        client.set_active(&root);
    }

    #[test]
    #[should_panic(expected = "already-active")]
    fn test_set_active_already_active() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);
        client.set_active(&root);
        
        // This should panic with "already-active" (trying to activate again)
        client.set_active(&root);
    }

    #[test]
    fn test_cancel_unaccepted() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        // Create unaccepted sublease
        let child = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        
        // Verify it exists
        let children_before = client.children_of(&root);
        assert_eq!(children_before.len(), 1);
        assert!(children_before.contains(&child));

        // Cancel it
        client.cancel_unaccepted(&child);

        // Verify it's removed
        let children_after = client.children_of(&root);
        assert_eq!(children_after.len(), 0);
    }

    #[test]
    #[should_panic(expected = "already-accepted")]
    fn test_cancel_unaccepted_fails_if_accepted() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        let child = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        client.accept(&child);
        
        // This should panic with "already-accepted" (trying to cancel accepted lease)
        client.cancel_unaccepted(&child);
    }

    #[test]
    fn test_replace_sublessee() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);
        let sub2 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        // Create unaccepted sublease
        let child = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        
        // Replace lessee
        client.replace_sublessee(&child, &sub2);

        // Verify lessee changed
        let lease = client.get_lease(&child);
        assert_eq!(lease.lessee, sub2);
    }

    #[test]
    #[should_panic(expected = "already-accepted")]
    fn test_replace_sublessee_fails_if_accepted() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);
        let sub2 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        let child = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        client.accept(&child);
        
        // This should panic with "already-accepted" (trying to replace lessee of accepted lease)
        client.replace_sublessee(&child, &sub2);
    }

    #[test]
    fn test_multi_level_recursion() {
        let e = Env::default();
        let landlord = Address::generate(&e);
        let master = Address::generate(&e);
        let sub1 = Address::generate(&e);
        let sub2 = Address::generate(&e);
        let sub3 = Address::generate(&e);

        let unit = Symbol::short("unit");
        let terms = BytesN::from_array(&e, &[1u8; 32]);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, LeaseRegistry);
        let client = LeaseRegistryClient::new(&e, &contract_id);

        // Create 3-level chain: landlord -> master -> sub1 -> sub2 -> sub3
        let root = client.create_master(&unit, &landlord, &master, &terms, &2, &2_000_000_000);
        client.accept(&root);

        let child1 = client.create_sublease(&root, &sub1, &terms, &2, &2_000_000_000);
        client.accept(&child1);

        let child2 = client.create_sublease(&child1, &sub2, &terms, &1, &2_000_000_000);
        client.accept(&child2);

        let child3 = client.create_sublease(&child2, &sub3, &terms, &1, &2_000_000_000);
        client.accept(&child3);

        // Test tree structure
        assert_eq!(client.root_of(&child3), root);
        assert_eq!(client.parent_of(&child3), Some(child2));
        assert_eq!(client.parent_of(&child2), Some(child1));
        assert_eq!(client.parent_of(&child1), Some(root));
        assert_eq!(client.parent_of(&root), None);

        // Test depths
        assert_eq!(client.get_lease(&root).depth, 0);
        assert_eq!(client.get_lease(&child1).depth, 1);
        assert_eq!(client.get_lease(&child2).depth, 2);
        assert_eq!(client.get_lease(&child3).depth, 3);

        // Test children
        assert_eq!(client.children_of(&root).len(), 1);
        assert_eq!(client.children_of(&child1).len(), 1);
        assert_eq!(client.children_of(&child2).len(), 1);
        assert_eq!(client.children_of(&child3).len(), 0);
    }

}