# Utilities Oracle Contract

A Soroban smart contract that serves as a mock utilities oracle for storing and retrieving utility readings (electricity, gas, water) per unit and period. This contract is designed to integrate with the lease registry system for automated utility cost splitting.

## Overview

The Utilities Oracle contract provides a simple interface for:
- Storing utility readings with admin-gated write access
- Retrieving utility readings for billing and cost allocation
- Emitting events for off-chain indexing and processing

## Contract Functions

### `init(admin: Address)`
One-time initialization function that sets the admin address.
- **Admin**: The address that will be authorized to write utility readings
- **Panics**: If called more than once ("inited")

### `set_reading(unit: Symbol, period: Symbol, kwh: i64, gas: i64, water: i64)`
Stores utility reading data for a specific unit and period.
- **Admin Only**: Requires authentication from the admin address
- **Validation**: Rejects negative values (panics with "neg")
- **Storage**: Stores reading data using a simple key structure
- **Panics**: If admin not initialized ("no-admin") or values are negative ("neg")

### `get_reading(unit: Symbol, period: Symbol) -> Reading`
Retrieves utility reading data for a specific unit and period.
- **Public**: No authentication required
- **Returns**: Reading struct with kwh, gas, water values
- **Panics**: If no reading exists ("no-reading")

## Data Structures

### `Reading`
```rust
pub struct Reading {
    pub kwh: i64,    // Electricity usage in kWh
    pub gas: i64,    // Gas usage in units
    pub water: i64,  // Water usage in units
}
```

## Storage Schema

The contract uses simple instance storage:
- `admin`: Address of the authorized admin
- `reading`: Current utility reading data (simplified for demo)

## Events

The contract emits events for off-chain processing:
- `UtilityReading(unit, period)`: Emitted when a reading is set, includes the utility values

## Deployment

### Prerequisites
- Stellar CLI installed and configured
- Testnet account with XLM for transaction fees
- Admin keypair for contract initialization

### Steps

1. **Build the contract**:
   ```bash
   cd leaselock
   stellar scaffold build
   ```

2. **Upload WASM to testnet**:
   ```bash
   stellar contract upload --wasm target/stellar/local/utilities_oracle.wasm --source arbitrator --network testnet
   ```

3. **Deploy contract instance**:
   ```bash
   stellar contract deploy --wasm-hash <WASM_HASH> --source arbitrator --network testnet
   ```

4. **Initialize with admin**:
   ```bash
   stellar contract invoke --id <CONTRACT_ID> --source arbitrator --network testnet -- init --admin <ADMIN_ADDRESS>
   ```

## Usage Examples

### CLI Usage

**Write a utility reading**:
```bash
stellar contract invoke --id <CONTRACT_ID> --source arbitrator --network testnet -- \
  set_reading --unit NYC123A --period OCT2025 --kwh 320 --gas 14 --water 6800
```

**Read a utility reading**:
```bash
stellar contract invoke --id <CONTRACT_ID> --source arbitrator --network testnet -- \
  get_reading --unit NYC123A --period OCT2025
```

### Python Usage

**Write utility reading**:
```python
python utilities_oracle_write.py NYC123A OCT2025 320 14 6800
```

**Read utility reading**:
```python
python utilities_oracle_read.py NYC123A OCT2025
```

**Split costs among leases**:
```python
python utilities_cost_split.py NYC123A OCT2025 --root-lease-id 1
```

## Period Keying Convention

- Use `YYYY-MM` format for periods (e.g., "2025-10")
- Keep unit identifiers simple without special characters (e.g., "NYC123A")
- The contract uses Symbol types which have limitations on special characters

## Integration with Lease Registry

The utilities oracle integrates with the lease registry system for cost splitting:

1. **Read utility data** from the oracle for a specific unit/period
2. **Query lease registry** to find all active leaf leases for the unit
3. **Calculate cost split** equally among active tenants
4. **Generate invoices** for each tenant

Example cost split workflow:
```python
# 1. Read utility data
reading = oracle.get_reading("NYC123A", "OCT2025")

# 2. Find active leases
active_leases = lease_registry.get_active_leaves_for_unit("NYC123A")

# 3. Split costs
cost_per_tenant = total_cost / len(active_leases)

# 4. Generate invoices
for lease in active_leases:
    invoice = create_invoice(lease, cost_per_tenant, reading)
```

## Error Handling

### Common Error Messages
- `"inited"`: Contract already initialized
- `"no-admin"`: Admin not set, contract not initialized
- `"neg"`: Negative utility values provided
- `"no-reading"`: No reading found for the specified unit/period

### Failure Modes
- **Missing reading**: Query returns "no-reading" error
- **Unauthorized write**: Transaction fails if not signed by admin
- **Invalid data**: Negative values are rejected
- **Double initialization**: Second init call panics

## Security Considerations

- **Admin key security**: The admin private key must be kept secure
- **Access control**: Only the admin can write utility readings
- **Data validation**: Negative values are rejected
- **One-time init**: Contract can only be initialized once

## Operational Considerations

- **Backup admin key**: Keep secure backups of the admin keypair
- **Event monitoring**: Subscribe to `UtilityReading` events for off-chain processing
- **Data retention**: Consider implementing data archival for old readings
- **Rate limiting**: Implement client-side rate limiting for write operations

## Future Enhancements

Potential improvements for production use:
- **Batch operations**: Add `set_reading_batch()` for multiple readings
- **Data versioning**: Add version field to Reading struct
- **Historical data**: Implement reading history and archival
- **Multi-admin**: Support multiple authorized writers
- **Data validation**: Add more sophisticated validation rules
- **Cost calculation**: On-chain utility rate storage and calculation

## Testing

The contract includes comprehensive unit tests covering:
- Successful initialization and reading operations
- Error conditions (double init, unauthorized access, negative values)
- Multiple readings for different units/periods
- Event emission verification

Run tests with:
```bash
cd leaselock
cargo test -p utilities_oracle
```

## Contract Address

**Testnet**: `CDDO7X23GQ7J3KXACSIFRIY6T7MESM5EACTX7ZAHRRQZZIW2LYUPIX77`

## Related Scripts

- `utilities_oracle_write.py`: Write utility readings
- `utilities_oracle_read.py`: Read utility readings  
- `utilities_cost_split.py`: Split costs among active leases
- `lease_api.py`: Lease registry integration utilities
