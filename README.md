# Lease Lock System

A comprehensive lease management system built on Stellar blockchain with hierarchical sublease support and IoT lock integration.

## Architecture

The system consists of three main components:

- **Lease Registry Contract** (`leaselock/`): Soroban smart contract managing lease hierarchies
- **Client Scripts** (`client/`): Python scripts for interacting with the contract
- **IoT Lock System** (`lock/`): Physical lock control and monitoring
- **Anchor Service** (`anchor/`): Web service for lock management

## Terms Enforcement

The system enforces identical contract terms across all leases in a chain using SHA-256 hashing of canonical JSON.

### Workflow

1. **Define Terms**: Create `terms.json` with immutable lease parameters
2. **Generate Hash**: Use `python client/scripts/hash_terms.py terms.json`
3. **Create Master**: Deploy master lease with terms hash
4. **Create Subleases**: All subleases must use identical terms hash
5. **Validate**: Contract automatically validates terms at each step

### Example Terms JSON

```json
{
  "currency": "USD",
  "rent_amount": "1200.00",
  "due_day": 1,
  "deposit_amount": "1200.00",
  "late_fee_policy": {"percent": 5, "grace_days": 3},
  "utilities_policy": {"electric": "tenant", "gas": "tenant", "water": "tenant"},
  "insurance_required": true,
  "lock_policy": {"auto_revoke_on_delinquent": true},
  "sublease_limit_per_node": 2
}
```

### CLI Commands

```bash
# Generate terms hash
TERMS_HEX=$(python client/scripts/hash_terms.py terms.json)

# Create master lease
stellar contract invoke --id lease-registry-inst -- \
  create_master --unit unit:NYC:123-A \
  --landlord G...LAND --master G...TEN \
  --terms $TERMS_HEX --limit 2 --expiry-ts 2000000000

# Create sublease (same terms)
stellar contract invoke --id lease-registry-inst -- \
  create_sublease --parent-id 1 --sublessee G...SUB1 \
  --terms $TERMS_HEX --limit 2 --expiry-ts 2000000000
```

## Error Handling

The system provides clear error messages for common issues:

- `terms-mismatch`: Sublease terms don't match parent
- `limit-mismatch`: Sublease limit doesn't match parent  
- `terms-drift`: Terms validation failed during acceptance
- `self-sublease`: Cannot sublease to self
- `limit`: Parent has reached sublease capacity

## Testing

### Contract Tests
```bash
cd leaselock/contracts/lease_registry
cargo test
```

### Integration Tests
```bash
cd client/scripts
python test_lease_graph.py
```

### Terms Hash Examples
```bash
cd client/scripts
python terms_hash_example.py
```

## Security Features

- **Immutable Terms**: Master lease terms cannot be changed after creation
- **Chain Validation**: All subleases inherit identical terms from parent
- **Cryptographic Verification**: SHA-256 hashing ensures terms integrity
- **Defense in Depth**: Validation at creation, acceptance, and activation

## Components

### Lease Registry Contract
- Hierarchical lease management
- Terms enforcement via SHA-256 hashing
- Event emission for observability
- Query functions for terms verification

### Client Scripts
- Terms hash generation utilities
- Contract interaction helpers
- Integration test suite
- Tree visualization tools

### IoT Lock System
- Physical lock control
- Lease status monitoring
- Automatic lock/unlock based on lease state

### Anchor Service
- Web interface for lock management
- Deposit and withdrawal handling
- Integration with lease registry

## Getting Started

1. **Setup Environment**: Configure `.env` files in each component
2. **Deploy Contract**: Deploy lease registry to Stellar testnet
3. **Generate Terms**: Create and hash your lease terms JSON
4. **Create Leases**: Use client scripts to create master and subleases
5. **Test System**: Run integration tests to verify functionality

## Documentation

- [Lease Registry Contract](leaselock/contracts/lease_registry/README.md)
- [Client Scripts](client/README.md)
- [IoT Lock System](lock/README.md)
- [Anchor Service](anchor/README.md)
