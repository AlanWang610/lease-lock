# IoT Lock Daemon

This directory contains a Python daemon that interfaces with the lease-lock smart contract to manage physical locks based on lease events.

## Overview

The lock daemon subscribes to events from the `lease_registry` smart contract and maintains a local state machine that controls lock access. It polls the Stellar RPC for contract events and updates lock states deterministically.

## Events Handled

- `LeaseActivated` → `UNLOCK` (tenant gains access)
- `Delinquent` → `LOCK` (tenant loses access due to non-payment)
- `LeaseEnded` → `LOCK` (tenant loses access permanently)
- `SubleaseGranted` → no change (optional, for logging only)

## Files

- `iot_lock_daemon.py` - Main daemon script
- `mock_lock_simple.py` - Mock lock interface for terminal display
- `test_lock_system.py` - Unified test script for all components
- `requirements.txt` - Python dependencies
- `.lock_state.json` - Persistent lock states (created at runtime)
- `.lock_cursor.txt` - Event cursor for resumption (created at runtime)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export LEASE_REGISTRY_ID=<your_deployed_contract_id>
export STELLAR_RPC=https://soroban-testnet.stellar.org  # optional, defaults to testnet
```

3. Make sure you have the Stellar CLI installed and configured with your keys.

## Usage

### Running the Daemon

Start the lock daemon in one terminal:
```bash
python iot_lock_daemon.py
```

The daemon will:
- Load any existing lock states from `.lock_state.json`
- Resume from the last processed event cursor
- Poll for new contract events every second
- Update lock states based on events
- Persist state changes immediately

### Testing the System

Run the unified test script to test all components:
```bash
# Run all tests
python test_lock_system.py

# Run specific tests
python test_lock_system.py --mock      # Test mock lock only
python test_lock_system.py --daemon    # Test daemon integration
python test_lock_system.py --contract  # Test contract events
python test_lock_system.py --demo      # Run demonstration
```

This will:
1. Test mock lock interface functionality
2. Test daemon integration with mock lock
3. Test actual contract event triggering
4. Show comprehensive test results

### Manual Contract Invocation

You can also trigger events manually using the Stellar CLI:

```bash
# Activate lease
stellar contract invoke --id <contract_id> -- \
  activate_lease --unit unit:NYC:123-A --subtenant <tenant_address>

# Mark as delinquent
stellar contract invoke --id <contract_id> -- \
  set_delinquent --unit unit:NYC:123-A --subtenant <tenant_address>

# End lease
stellar contract invoke --id <contract_id> -- \
  end_lease --unit unit:NYC:123-A --subtenant <tenant_address>
```

## Environment Variables

- `LEASE_REGISTRY_ID` (required): The deployed contract ID to monitor
- `STELLAR_RPC`: RPC endpoint (default: https://soroban-testnet.stellar.org)
- `LOCK_STATE_FILE`: File to persist lock states (default: .lock_state.json)
- `LOCK_CURSOR_FILE`: File to persist event cursor (default: .lock_cursor.txt)
- `TEST_UNIT`: Unit identifier for testing (default: unit:NYC:123-A)

## State Management

The daemon maintains persistent state across restarts:

- **Lock States**: Stored in JSON format with unit → state mapping
- **Event Cursor**: Tracks the last processed event to avoid reprocessing
- **Graceful Shutdown**: Saves state on Ctrl+C

## Production Considerations

1. **Authorization**: The current contract implementation allows any authenticated caller to trigger events. In production, add proper authorization checks.

2. **RPC Reliability**: The daemon handles RPC errors gracefully with retries and backoff.

3. **Event Retention**: Stellar RPC retains events for ~7 days. For longer retention, implement your own event storage.

4. **Security**: In production, consider:
   - Running the daemon as a system service
   - Implementing proper logging
   - Adding monitoring and alerting
   - Securing the state files

## Troubleshooting

- **"LEASE_REGISTRY_ID not set"**: Set the environment variable to your deployed contract ID
- **"stellar command not found"**: Install the Stellar CLI
- **RPC errors**: Check your network connection and RPC endpoint
- **No events**: Verify the contract ID is correct and events are being emitted

## Integration

This daemon is designed to be integrated with physical IoT locks. The lock state can be used to:

- Control electronic door locks
- Manage access cards/permissions
- Trigger security systems
- Send notifications to tenants/landlords

The state machine provides a deterministic way to control access based on on-chain lease events.
