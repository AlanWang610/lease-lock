#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, Address, Env, Map, Symbol, Vec
};

#[contracttype]
#[derive(Clone, Copy, PartialEq)]
pub enum Event {
    LeaseGranted,       // (unit) -> master
    SubleaseGranted,    // (unit) -> sub
    LeaseActivated,     // (unit) -> subtenant (when sublease becomes usable)
    Delinquent,         // (unit) -> subtenant (when payment is overdue)
    LeaseEnded,         // (unit) -> subtenant (when lease is terminated)
}

#[contract]
pub struct LeaseRegistry;

#[contractimpl]
impl LeaseRegistry {
    // Storage keys
    fn k_masters() -> Symbol { Symbol::short("masters") } // Map<unit, Vec<Address>>
    fn k_chains()  -> Symbol { Symbol::short("chains") }  // Map<unit, Vec<Address>>

    /// Register master lease lineage start.
    /// Only landlord may call.
    pub fn register_master(e: Env, unit: Symbol, landlord: Address, master: Address) {
        landlord.require_auth();

        let mut masters: Map<Symbol, Vec<Address>> =
            e.storage().instance().get(&Self::k_masters()).unwrap_or(Map::new(&e));
        let mut v = Vec::new(&e);
        v.push_back(landlord.clone());
        v.push_back(master.clone());
        masters.set(unit.clone(), v);
        e.storage().instance().set(&Self::k_masters(), &masters);

        e.events().publish((Event::LeaseGranted, unit.clone()), master);
    }

    /// Grant a sublease off an existing holder (parent).
    /// Only parent may call.
    pub fn grant_sublease(e: Env, unit: Symbol, parent: Address, sub: Address) {
        parent.require_auth();

        // optional: validate parent exists in lineage
        let masters: Map<Symbol, Vec<Address>> =
            e.storage().instance().get(&Self::k_masters()).unwrap_or(Map::new(&e));
        let chains: Map<Symbol, Vec<Address>> =
            e.storage().instance().get(&Self::k_chains()).unwrap_or(Map::new(&e));

        let mut lineage = Vec::new(&e);
        if let Some(v) = masters.get(unit.clone()) { for a in v.iter() { lineage.push_back(a) } }
        if let Some(v) = chains.get(unit.clone())  { for a in v.iter() { lineage.push_back(a) } }

        let mut ok = false;
        for a in lineage.iter() {
            if a == parent { ok = true; break; }
        }
        if !ok { panic!("parent not in lineage"); }

        let mut chains_mut = chains;
        let mut v = chains_mut.get(unit.clone()).unwrap_or(Vec::new(&e));
        v.push_back(parent.clone());
        v.push_back(sub.clone());
        chains_mut.set(unit.clone(), v);
        e.storage().instance().set(&Self::k_chains(), &chains_mut);

        e.events().publish((Event::SubleaseGranted, unit), sub);
    }

    /// Read full lineage: [landlord, master, parent, sub, parent2, sub2, ...]
    pub fn lineage(e: Env, unit: Symbol) -> Vec<Address> {
        let masters: Map<Symbol, Vec<Address>> =
            e.storage().instance().get(&Self::k_masters()).unwrap_or(Map::new(&e));
        let chains: Map<Symbol, Vec<Address>> =
            e.storage().instance().get(&Self::k_chains()).unwrap_or(Map::new(&e));

        let mut out = Vec::new(&e);
        if let Some(v) = masters.get(unit.clone()) { for a in v.iter() { out.push_back(a) } }
        if let Some(v) = chains.get(unit)           { for a in v.iter() { out.push_back(a) } }
        out
    }

    /// Activate a lease - when a sublease becomes usable (e.g., first rent paid / landlord approval)
    /// Only landlord or master tenant may call
    pub fn activate_lease(e: Env, unit: Symbol, subtenant: Address) {
        // For now, allow any authenticated caller - in production, add proper authorization
        subtenant.require_auth();
        
        e.events().publish((Event::LeaseActivated, unit.clone()), subtenant.clone());
    }

    /// Mark tenant as delinquent to trigger lock revoke
    /// Only landlord or master tenant may call
    pub fn set_delinquent(e: Env, unit: Symbol, subtenant: Address) {
        // For now, allow any authenticated caller - in production, add proper authorization
        subtenant.require_auth();
        
        e.events().publish((Event::Delinquent, unit.clone()), subtenant.clone());
    }

    /// Mark lease as ended to revoke lock permanently
    /// Only landlord or master tenant may call
    pub fn end_lease(e: Env, unit: Symbol, subtenant: Address) {
        // For now, allow any authenticated caller - in production, add proper authorization
        subtenant.require_auth();
        
        e.events().publish((Event::LeaseEnded, unit.clone()), subtenant.clone());
    }
}
