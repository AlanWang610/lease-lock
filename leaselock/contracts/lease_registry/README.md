# Lease Registry Contract

## Overview

The Lease Registry contract implements a hierarchical lease management system where master leases can spawn subleases, with strict enforcement of identical contract terms across the entire chain.

## Terms Enforcement

The contract enforces that all leases in a chain must have identical terms using SHA-256 hashing of canonical JSON. This ensures:

- **Immutability**: Master lease terms cannot be changed after creation
- **Consistency**: All subleases must have identical terms to their parent
- **Verifiability**: Terms can be verified off-chain using the same hashing algorithm

## Contract Functions

### `create_master(unit, landlord, master, terms, limit, expiry_ts) -> u64`

Creates a master lease with immutable terms.

**Parameters:**
- `unit`: Symbol identifying the property unit
- `landlord`: Address of the landlord
- `master`: Address of the master tenant
- `terms`: BytesN<32> - SHA-256 hash of canonical JSON terms
- `limit`: u32 - Maximum number of direct subleases allowed
- `expiry_ts`: u64 - Unix timestamp when lease expires

**Returns:** Lease ID

**Events:** `Lease(unit, id)` - Master lease created

### `accept(id)`

Accepts a lease. Includes defense-in-depth validation that terms match parent.

**Parameters:**
- `id`: u64 - Lease ID to accept

**Events:** `Accept(id)` - Lease accepted

**Validation:** If lease has a parent, validates that terms match parent's terms

### `create_sublease(parent_id, sublessee, terms, limit, expiry_ts) -> u64`

Creates a sublease with strict validation.

**Parameters:**
- `parent_id`: u64 - Parent lease ID
- `sublessee`: Address of the subtenant
- `terms`: BytesN<32> - Must match parent's terms exactly
- `limit`: u32 - Must match parent's limit exactly
- `expiry_ts`: u64 - Unix timestamp when lease expires

**Returns:** New lease ID

**Events:** 
- `TermsCheckPassed(parent_id, id)` - Terms validation passed
- `Sublease(parent_id, id)` - Sublease created

**Validation:**
- Terms must match parent exactly (`terms-mismatch` error)
- Limit must match parent exactly (`limit-mismatch` error)
- Cannot sublease to self (`self-sublease` error)
- Parent must have capacity (`limit` error)

### `terms_of(id) -> BytesN<32>`

Returns the terms hash for a given lease.

**Parameters:**
- `id`: u64 - Lease ID

**Returns:** BytesN<32> - Terms hash

## Terms JSON Format

The canonical terms JSON must include these immutable fields:

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

**Excluded fields** (can differ per node):
- `lessee`, `lessor` - Node-specific addresses
- `expiry_ts` - Node-specific expiry

## Error Messages

- `terms-mismatch`: Sublease terms don't match parent
- `limit-mismatch`: Sublease limit doesn't match parent
- `terms-drift`: Terms validation failed during acceptance
- `self-sublease`: Cannot sublease to self
- `limit`: Parent has reached sublease capacity
- `limit-0`: Limit cannot be zero
- `bad-expiry`: Expiry timestamp cannot be zero

## Usage Examples

### Creating a Master Lease

```bash
# Generate terms hash
TERMS_HEX=$(python client/scripts/hash_terms.py terms.json)

# Create master lease
stellar contract invoke --id lease-registry-inst -- \
  create_master --unit unit:NYC:123-A \
  --landlord G...LAND --master G...TEN \
  --terms $TERMS_HEX --limit 2 --expiry-ts 2000000000
```

### Creating a Sublease

```bash
# Use same terms hash
stellar contract invoke --id lease-registry-inst -- \
  create_sublease --parent-id 1 --sublessee G...SUB1 \
  --terms $TERMS_HEX --limit 2 --expiry-ts 2000000000
```

### Querying Terms

```bash
# Get terms hash for a lease
stellar contract invoke --id lease-registry-inst -- \
  terms_of --id 1
```

## Security Guarantees

1. **Terms Immutability**: Master lease terms cannot be modified after creation
2. **Chain Consistency**: All subleases inherit identical terms from their parent
3. **Defense in Depth**: Terms are validated at creation, acceptance, and activation
4. **Cryptographic Verification**: Terms integrity verified using SHA-256 hashing

## Testing

Run the contract tests:

```bash
cd leaselock/contracts/lease_registry
cargo test
```

Run integration tests:

```bash
cd client/scripts
python test_lease_graph.py
```
