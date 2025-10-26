# Python Stellar Client Scripts

This directory contains Python scripts to interact with the lease_registry Soroban contract on Stellar testnet.

## Setup

### 1. Virtual Environment

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
python -m pip install -U "stellar-sdk>=10.0.0" python-dotenv
```

### 3. Configure Environment

Copy `env.example` to `.env` and update with your configuration:

```bash
cp env.example .env
```

Edit `.env` with your actual values:
- Secret keys for landlord, tenant, and arbitrator accounts
- Contract ID: `CBRYYKZFYRQFAX2M54QOKFXP4M7AB4C7N3OPQ23OV5TTVTCQ`
- Set `BALANCE_ID` after creating a claimable balance

## Scripts

### 1. Initialize and Fund Accounts

```bash
python scripts/01_init_and_fund.py
```

Funds all three accounts (landlord, tenant, arbitrator) via friendbot and displays balances.

### 2. Pay Rent (Classic Payment)

```bash
python scripts/02_pay_rent.py
```

Sends 5 XLM from tenant to landlord with memo "rent-2025-10".

### 3. Create Deposit Escrow

```bash
python scripts/03_create_deposit.py
```

Creates a claimable balance of 10 XLM with:
- Landlord can claim after 3 minutes (timelock)
- Arbitrator can claim anytime

**Note**: After running this script, copy the balance ID from the output and set it in your `.env` file as `BALANCE_ID`.

### 4. Claim Deposit

```bash
python scripts/04_claim_deposit.py
```

Claims the escrow deposit. Works for landlord (after timelock) or arbitrator (anytime).

### 5. Call Contract

```bash
python scripts/05_call_contract.py
```

Interacts with the lease_registry contract:
1. **register_master**: Landlord registers unit "unit:NYC:123-A" with tenant as master
2. **grant_sublease**: Tenant grants sublease to subtenant
3. **lineage**: Reads and displays the full lineage chain

## Contract Methods

The scripts interact with these contract methods from `lease_registry`:

- `register_master(unit: Symbol, landlord: Address, master: Address)`: Register master lease lineage
- `grant_sublease(unit: Symbol, parent: Address, sub: Address)`: Grant sublease
- `lineage(unit: Symbol) -> Vec<Address>`: Read full lineage chain

## Common Errors

- **`op_low_reserve`**: Account needs more XLM for reserves or transaction fees
- **`tx_bad_auth`**: Wrong signer or missing `tx.sign()`
- **`op_no_trust`**: Only applies to non-native assets; use XLM for simplicity
- **Soroban simulate errors**: Check contract arguments and types match the contract interface
- **Claimable balance not found**: Wait for ledger close, then query again

## Network Configuration

- **Network**: Stellar Testnet
- **Passphrase**: "Test SDF Network ; September 2015"
- **Horizon**: https://horizon-testnet.stellar.org
- **Soroban RPC**: https://soroban-testnet.stellar.org
- **Contract ID**: `CBRYYKZFYRQFAX2M54QOKFXP4M7AB4C7N3OPQ23OV5TTVTCQ`
