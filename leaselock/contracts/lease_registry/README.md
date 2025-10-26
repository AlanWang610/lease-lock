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

Creates a sublease with enhanced validation.

**Parameters:**
- `parent_id`: u64 - Parent lease ID
- `sublessee`: Address of the subtenant
- `terms`: BytesN<32> - Must match parent's terms exactly
- `limit`: u32 - Must be <= parent's limit (flexible inheritance)
- `expiry_ts`: u64 - Must be <= parent's expiry timestamp

**Returns:** New lease ID

**Events:** 
- `Sublease(parent_id, id)` - Sublease created

**Validation:**
- Terms must match parent exactly (`terms-mismatch` error)
- Limit must be <= parent limit (`limit-exceeds-parent` error)
- Expiry must be <= parent expiry (`expiry-exceeds-parent` error)
- Max depth of 10 levels (`max-depth` error)
- Cannot sublease to self (`self-sublease` error)
- Parent must have capacity (`limit` error)

### `terms_of(id) -> BytesN<32>`

Returns the terms hash for a given lease.

**Parameters:**
- `id`: u64 - Lease ID

**Returns:** BytesN<32> - Terms hash

## Read APIs

### `get_lease(id) -> Node`

Returns the complete lease node data.

**Parameters:**
- `id`: u64 - Lease ID

**Returns:** Node struct with all lease details

### `children_of(id) -> Vec<u64>`

Returns the direct children of a lease.

**Parameters:**
- `id`: u64 - Lease ID

**Returns:** Vec<u64> - List of child lease IDs

### `parent_of(id) -> Option<u64>`

Returns the parent lease ID.

**Parameters:**
- `id`: u64 - Lease ID

**Returns:** Option<u64> - Parent ID or None for root leases

### `root_of(id) -> u64`

Walks up the lease chain to find the root lease.

**Parameters:**
- `id`: u64 - Lease ID

**Returns:** u64 - Root lease ID

## Activation APIs

### `set_active(id)`

Activates an accepted lease.

**Parameters:**
- `id`: u64 - Lease ID to activate

**Events:** `Activated(id)` - Lease activated

**Validation:**
- Lease must be accepted (`not-accepted` error)
- Lease must not already be active (`already-active` error)
- Requires lessor authorization

### `set_delinquent(id)`

Marks a lease as delinquent (deactivates it).

**Parameters:**
- `id`: u64 - Lease ID to mark delinquent

**Events:** `Delinq(id)` - Lease marked delinquent

**Validation:**
- Requires lessor authorization

## Quality-of-Life APIs

### `cancel_unaccepted(id)`

Cancels an unaccepted sublease.

**Parameters:**
- `id`: u64 - Lease ID to cancel

**Events:** `Canceled(id)` - Sublease canceled

**Validation:**
- Lease must not be accepted (`already-accepted` error)
- Requires lessor authorization
- Removes lease from parent's children list

### `replace_sublessee(id, new_lessee)`

Replaces the lessee of an unaccepted lease.

**Parameters:**
- `id`: u64 - Lease ID
- `new_lessee`: Address - New lessee address

**Events:** `Reassign(id)` - Lessee reassigned

**Validation:**
- Lease must not be accepted (`already-accepted` error)
- Requires lessor authorization

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
- `limit-exceeds-parent`: Sublease limit exceeds parent limit
- `expiry-exceeds-parent`: Sublease expiry exceeds parent expiry
- `max-depth`: Maximum depth of 10 levels exceeded
- `terms-drift`: Terms validation failed during acceptance
- `self-sublease`: Cannot sublease to self
- `limit`: Parent has reached sublease capacity
- `limit-0`: Limit cannot be zero
- `bad-expiry`: Expiry timestamp cannot be zero
- `not-accepted`: Lease must be accepted before activation
- `already-accepted`: Lease is already accepted
- `already-active`: Lease is already active

## Usage Examples

### Creating and Activating a Master Lease

```bash
# Generate terms hash
TERMS_HEX=$(python client/scripts/hash_terms.py terms.json)

# Create master lease
MID=$(stellar contract invoke --id lease-registry-inst -- create_master \
  --unit unit:NYC:123-A --landlord G...LAND --master G...TEN \
  --terms $TERMS_HEX --limit 2 --expiry-ts 2000000000)

# Accept master lease
stellar contract invoke --id lease-registry-inst -- accept --id $MID --sign G...TEN

# Activate master lease
stellar contract invoke --id lease-registry-inst -- set_active --id $MID --sign G...LAND
```

### Creating a Sublease Chain

```bash
# Create first sublease
SID1=$(stellar contract invoke --id lease-registry-inst -- create_sublease \
  --parent-id $MID --sublessee G...SUB1 --terms $TERMS_HEX \
  --limit 1 --expiry-ts 2000000000 --sign G...TEN)

# Accept first sublease
stellar contract invoke --id lease-registry-inst -- accept --id $SID1 --sign G...SUB1

# Activate first sublease
stellar contract invoke --id lease-registry-inst -- set_active --id $SID1 --sign G...TEN

# Create second-level sublease
SID2=$(stellar contract invoke --id lease-registry-inst -- create_sublease \
  --parent-id $SID1 --sublessee G...SUB2 --terms $TERMS_HEX \
  --limit 1 --expiry-ts 2000000000 --sign G...SUB1)

# Accept and activate second sublease
stellar contract invoke --id lease-registry-inst -- accept --id $SID2 --sign G...SUB2
stellar contract invoke --id lease-registry-inst -- set_active --id $SID2 --sign G...SUB1
```

### Querying Lease Data

```bash
# Get lease details
stellar contract invoke --id lease-registry-inst -- get_lease --id $SID2

# Get children of a lease
stellar contract invoke --id lease-registry-inst -- children_of --id $MID

# Get parent of a lease
stellar contract invoke --id lease-registry-inst -- parent_of --id $SID2

# Get root lease ID
stellar contract invoke --id lease-registry-inst -- root_of --id $SID2

# Get terms hash
stellar contract invoke --id lease-registry-inst -- terms_of --id $MID
```

### Managing Lease Status

```bash
# Mark lease as delinquent
stellar contract invoke --id lease-registry-inst -- set_delinquent --id $SID2 --sign G...SUB1

# Reactivate lease
stellar contract invoke --id lease-registry-inst -- set_active --id $SID2 --sign G...SUB1
```

### Quality-of-Life Operations

```bash
# Create unaccepted sublease for testing
TEST_ID=$(stellar contract invoke --id lease-registry-inst -- create_sublease \
  --parent-id $MID --sublessee G...TEST --terms $TERMS_HEX \
  --limit 1 --expiry-ts 2000000000 --sign G...TEN)

# Replace sublessee (before acceptance)
stellar contract invoke --id lease-registry-inst -- replace_sublessee \
  --id $TEST_ID --new-lessee G...NEW --sign G...TEN

# Cancel unaccepted sublease
stellar contract invoke --id lease-registry-inst -- cancel_unaccepted \
  --id $TEST_ID --sign G...TEN
```

### Python API Usage

```python
from lease_api import LeaseAPI
from stellar_sdk import Keypair

# Initialize API client
api = LeaseAPI("your-contract-id")

# Create keypairs
landlord = Keypair.from_secret("your-landlord-secret")
tenant = Keypair.from_secret("your-tenant-secret")
subtenant = Keypair.random()

# Define terms
terms_dict = {
    "currency": "USD",
    "rent_amount": "1200.00",
    "due_day": 1,
    "deposit_amount": "1200.00",
    "late_fee_policy": {"percent": 5, "grace_days": 3},
    "utilities_policy": {"electric": "tenant", "gas": "tenant", "water": "tenant"},
    "insurance_required": True,
    "lock_policy": {"auto_revoke_on_delinquent": True},
    "sublease_limit_per_node": 2
}

# Create master lease
root_id = api.create_master(
    landlord, "unit:NYC:123-A", landlord, tenant,
    terms_dict, 2, 2_000_000_000
)

# Accept and activate
api.accept(tenant, root_id)
api.set_active(landlord, root_id)

# Create sublease chain
sublease_ids = api.create_chain(
    tenant, root_id, [subtenant], terms_dict, 1, 2_000_000_000
)

# Query lease tree
api.print_tree(root_id)

# Get lease details
lease_details = api.get_lease(root_id)
print(f"Lease details: {lease_details}")
```

## Security Guarantees

1. **Terms Immutability**: Master lease terms cannot be modified after creation
2. **Chain Consistency**: All subleases inherit identical terms from their parent
3. **Defense in Depth**: Terms are validated at creation, acceptance, and activation
4. **Cryptographic Verification**: Terms integrity verified using SHA-256 hashing
5. **Expiry Validation**: Subleases cannot outlive their parent leases
6. **Depth Limiting**: Maximum depth of 10 levels prevents excessive recursion
7. **Flexible Limits**: Children can have lower limits than parents (but not higher)
8. **Authorization**: All state changes require proper authorization

## Testing

Run the contract tests:

```bash
cd leaselock/contracts/lease_registry
cargo test
```

Run integration tests with Python API:

```bash
cd client/scripts
python test_lease_graph.py
```

Run Python API example:

```bash
cd client/scripts
python lease_api.py
```

## Features Implemented

### Core Sublease Recursion
- ✅ Enhanced `create_sublease` with expiry, depth, and flexible limit validation
- ✅ Read APIs: `get_lease`, `children_of`, `parent_of`, `root_of`
- ✅ Activation APIs: `set_active`, `set_delinquent`
- ✅ Quality-of-life APIs: `cancel_unaccepted`, `replace_sublessee`

### Validation Rules
- ✅ Expiry validation: `expiry_ts <= parent.expiry_ts`
- ✅ Max depth enforcement: 10 levels maximum
- ✅ Flexible limit inheritance: `limit <= parent.limit`
- ✅ Terms consistency: All leases must have identical terms
- ✅ Authorization checks: Proper auth for all operations

### Python Integration
- ✅ `LeaseAPI` wrapper class with all contract functions
- ✅ `create_chain` helper for creating sublease chains
- ✅ `get_lease_tree` and `print_tree` for visualization
- ✅ Enhanced `test_lease_graph.py` with comprehensive testing
- ✅ Error handling and validation testing

### Comprehensive Testing
- ✅ 18 unit tests covering all new features
- ✅ Error case testing for all validation rules
- ✅ Multi-level recursion testing
- ✅ Activation and delinquency flow testing
- ✅ Read API functionality testing
