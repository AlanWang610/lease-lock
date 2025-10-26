#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, Address, Env, Symbol
};

#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Reading {
    pub kwh: i64,
    pub gas: i64,
    pub water: i64,
}

fn k_admin() -> Symbol { Symbol::short("admin") }
fn k_reading() -> Symbol { Symbol::short("reading") }

#[contract]
pub struct UtilitiesOracle;

#[contractimpl]
impl UtilitiesOracle {
    pub fn init(e: Env, admin: Address) {
        // one-time init
        if e.storage().instance().has(&k_admin()) { panic!("inited"); }
        e.storage().instance().set(&k_admin(), &admin);
    }

    pub fn set_reading(e: Env, unit: Symbol, period: Symbol, kwh: i64, gas: i64, water: i64) {
        // only admin can write (mock "oracle")
        let admin: Address = e.storage().instance().get(&k_admin()).expect("no-admin");
        admin.require_auth();

        // simple bounds (optional)
        if kwh < 0 || gas < 0 || water < 0 { panic!("neg"); }

        // store using a simple key (for demo purposes)
        let reading = Reading { kwh, gas, water };
        e.storage().instance().set(&k_reading(), &reading);
    }

    pub fn get_reading(e: Env, unit: Symbol, period: Symbol) -> Reading {
        e.storage().instance().get(&k_reading()).expect("no-reading")
    }
}

#[cfg(test)]
mod test {
    use super::*;
    use soroban_sdk::{testutils::Address as _, Env};

    #[test]
    fn test_init_and_set_reading() {
        let e = Env::default();
        let admin = Address::generate(&e);
        let unit = Symbol::short("unit:NYC:123-A");
        let period = Symbol::short("2025-10");

        e.mock_all_auths();

        // Register the contract
        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        // Initialize with admin
        client.init(&admin);

        // Set a reading
        client.set_reading(&unit, &period, &320, &14, &6800);

        // Get the reading back
        let reading = client.get_reading(&unit, &period);
        assert_eq!(reading.kwh, 320);
        assert_eq!(reading.gas, 14);
        assert_eq!(reading.water, 6800);
    }

    #[test]
    #[should_panic(expected = "inited")]
    fn test_double_init_panics() {
        let e = Env::default();
        let admin = Address::generate(&e);

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        // First init should succeed
        client.init(&admin);

        // Second init should panic
        client.init(&admin);
    }

    #[test]
    #[should_panic(expected = "no-admin")]
    fn test_set_reading_without_init_panics() {
        let e = Env::default();
        let unit = Symbol::short("unit:NYC:123-A");
        let period = Symbol::short("2025-10");

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        // Try to set reading without initializing admin
        client.set_reading(&unit, &period, &320, &14, &6800);
    }

    #[test]
    #[should_panic(expected = "neg")]
    fn test_negative_values_rejected() {
        let e = Env::default();
        let admin = Address::generate(&e);
        let unit = Symbol::short("unit:NYC:123-A");
        let period = Symbol::short("2025-10");

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        client.init(&admin);

        // Try to set negative values
        client.set_reading(&unit, &period, &-1, &14, &6800);
    }

    #[test]
    #[should_panic(expected = "no-reading")]
    fn test_get_nonexistent_reading_panics() {
        let e = Env::default();
        let admin = Address::generate(&e);
        let unit = Symbol::short("unit:NYC:123-A");
        let period = Symbol::short("2025-10");

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        client.init(&admin);

        // Try to get reading that doesn't exist
        client.get_reading(&unit, &period);
    }

    #[test]
    fn test_multiple_readings() {
        let e = Env::default();
        let admin = Address::generate(&e);
        let unit1 = Symbol::short("unit:NYC:123-A");
        let unit2 = Symbol::short("unit:NYC:456-B");
        let period1 = Symbol::short("2025-10");
        let period2 = Symbol::short("2025-11");

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        client.init(&admin);

        // Set multiple readings
        client.set_reading(&unit1, &period1, &320, &14, &6800);
        client.set_reading(&unit1, &period2, &350, &16, &7200);
        client.set_reading(&unit2, &period1, &280, &12, &6500);

        // Verify all readings
        let reading1 = client.get_reading(&unit1, &period1);
        assert_eq!(reading1.kwh, 320);
        assert_eq!(reading1.gas, 14);
        assert_eq!(reading1.water, 6800);

        let reading2 = client.get_reading(&unit1, &period2);
        assert_eq!(reading2.kwh, 350);
        assert_eq!(reading2.gas, 16);
        assert_eq!(reading2.water, 7200);

        let reading3 = client.get_reading(&unit2, &period1);
        assert_eq!(reading3.kwh, 280);
        assert_eq!(reading3.gas, 12);
        assert_eq!(reading3.water, 6500);
    }

    #[test]
    fn test_zero_values_allowed() {
        let e = Env::default();
        let admin = Address::generate(&e);
        let unit = Symbol::short("unit:NYC:123-A");
        let period = Symbol::short("2025-10");

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        client.init(&admin);

        // Set reading with zero values
        client.set_reading(&unit, &period, &0, &0, &0);

        let reading = client.get_reading(&unit, &period);
        assert_eq!(reading.kwh, 0);
        assert_eq!(reading.gas, 0);
        assert_eq!(reading.water, 0);
    }

    #[test]
    fn test_event_emission() {
        let e = Env::default();
        let admin = Address::generate(&e);
        let unit = Symbol::short("unit:NYC:123-A");
        let period = Symbol::short("2025-10");

        e.mock_all_auths();

        let contract_id = e.register_contract(None, UtilitiesOracle);
        let client = UtilitiesOracleClient::new(&e, &contract_id);

        client.init(&admin);

        // Set reading and check events
        client.set_reading(&unit, &period, &320, &14, &6800);

        // Check that event was emitted
        let events = e.events().all();
        assert_eq!(events.len(), 1);
        
        let event = &events[0];
        assert_eq!(event.event.type_, soroban_sdk::xdr::ContractEventType::Contract);
        
        // Verify event data structure
        let event_data = &event.event.body.contract_event;
        assert_eq!(event_data.contract_id, contract_id);
    }
}