#![no_std]
use soroban_sdk::{
    contract, contractimpl, contracttype, Address, Env, Symbol
};
use soroban_sdk::token; // standard token interface (SAC-compatible)

#[contracttype]
#[derive(Clone, Copy, PartialEq)]
pub enum EscrowStatus { Init, Funded, Released, Refunded }

#[contract]
pub struct Escrow;

#[contractimpl]
impl Escrow {
    // instance storage keys
    fn k_tenant()  -> Symbol { Symbol::short("ten") }
    fn k_landlord()-> Symbol { Symbol::short("ll") }
    fn k_arbit()   -> Symbol { Symbol::short("arb") }
    fn k_token()   -> Symbol { Symbol::short("tok") }
    fn k_amount()  -> Symbol { Symbol::short("amt") }
    fn k_status()  -> Symbol { Symbol::short("st")  }

    /// One-time initializer.
    pub fn init(e: Env, tenant: Address, landlord: Address, arbitrator: Address,
                token: Address, amount: i128) {
        // Any caller can deploy; identities are recorded here.
        if e.storage().instance().has(&Self::k_status()) {
            panic!("already inited");
        }
        e.storage().instance().set(&Self::k_tenant(),   &tenant);
        e.storage().instance().set(&Self::k_landlord(), &landlord);
        e.storage().instance().set(&Self::k_arbit(),    &arbitrator);
        e.storage().instance().set(&Self::k_token(),    &token);
        e.storage().instance().set(&Self::k_amount(),   &amount);
        e.storage().instance().set(&Self::k_status(),   &EscrowStatus::Init);
    }

    /// Tenant funds the escrow by transferring tokens to the contract address.
    pub fn deposit(e: Env) {
        let status: EscrowStatus = e.storage().instance().get(&Self::k_status()).unwrap();
        if status != EscrowStatus::Init { panic!("bad state"); }

        let tenant: Address   = e.storage().instance().get(&Self::k_tenant()).unwrap();
        let token_addr: Address = e.storage().instance().get(&Self::k_token()).unwrap();
        let amount: i128      = e.storage().instance().get(&Self::k_amount()).unwrap();

        // auth by tenant: the token contract will enforce tenant.require_auth() internally
        let token = token::Client::new(&e, &token_addr);
        let me = e.current_contract_address();
        token.transfer(&tenant, &me, &amount);

        e.storage().instance().set(&Self::k_status(), &EscrowStatus::Funded);
    }

    /// Arbitrator releases funds to landlord.
    pub fn release(e: Env) {
        let arbitrator: Address = e.storage().instance().get(&Self::k_arbit()).unwrap();
        arbitrator.require_auth();

        let status: EscrowStatus = e.storage().instance().get(&Self::k_status()).unwrap();
        if status != EscrowStatus::Funded { panic!("bad state"); }

        let landlord: Address = e.storage().instance().get(&Self::k_landlord()).unwrap();
        let token_addr: Address = e.storage().instance().get(&Self::k_token()).unwrap();
        let amount: i128 = e.storage().instance().get(&Self::k_amount()).unwrap();

        let token = token::Client::new(&e, &token_addr);
        let me = e.current_contract_address();
        token.transfer(&me, &landlord, &amount);

        e.storage().instance().set(&Self::k_status(), &EscrowStatus::Released);
    }

    /// Arbitrator refunds tenant.
    pub fn refund(e: Env) {
        let arbitrator: Address = e.storage().instance().get(&Self::k_arbit()).unwrap();
        arbitrator.require_auth();

        let status: EscrowStatus = e.storage().instance().get(&Self::k_status()).unwrap();
        if status != EscrowStatus::Funded { panic!("bad state"); }

        let tenant: Address = e.storage().instance().get(&Self::k_tenant()).unwrap();
        let token_addr: Address = e.storage().instance().get(&Self::k_token()).unwrap();
        let amount: i128 = e.storage().instance().get(&Self::k_amount()).unwrap();

        let token = token::Client::new(&e, &token_addr);
        let me = e.current_contract_address();
        token.transfer(&me, &tenant, &amount);

        e.storage().instance().set(&Self::k_status(), &EscrowStatus::Refunded);
    }

    pub fn status(e: Env) -> EscrowStatus {
        e.storage().instance().get(&Self::k_status()).unwrap()
    }
}
