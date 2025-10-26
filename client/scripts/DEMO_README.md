# Terminal Demo: Lease-Lock System

This demo shows the complete lease-lock workflow: payments, lock state management, utility posting/splitting, and delinquency handling.

## Prerequisites

1. **Deployed Contracts on Testnet:**
   - `LeaseRegistry` (set_active, set_delinquent, tree functions)
   - `UtilitiesOracle` (set_reading, get_reading functions)

2. **Python Environment:**
   ```bash
   pip install -r client/requirements.txt
   ```

3. **Environment Configuration:**
   Update `client/config.env` with your actual contract IDs and lease data:
   - `REGISTRY_ID`: Your LeaseRegistry contract ID
   - `UTILITIES_ID`: Your UtilitiesOracle contract ID
   - `UNIT`: Unit identifier (e.g., "unit:NYC:123-A")
   - `PERIOD`: Period identifier (e.g., "2025-10")
   - `LEAF_ID`: ID of active leaf lease to test
   - `ROOT_ID`: ID of root lease
   - `LESSOR_SECRET`: Secret key of the lessor who can activate/mark delinquent

## Demo Setup

### Four-Terminal Runbook

#### Terminal A: Lock Daemon

Monitor lease events and control lock state:

```bash
cd lock
python iot_lock_daemon.py
```

**Expected Output:**
```
Lock daemon started. Press Ctrl+C to stop.
Monitoring contract: CBRYYKZFYRQFAX2M54QOKFXP4M7AB4C7N3OPQ23OV5TTVTCQ
RPC endpoint: https://soroban-testnet.stellar.org
```

When events occur, you'll see:
```
[2025-01-XX...] lease_id=2: LOCKED -> UNLOCKED (Activated)
```

#### Terminal B: Payment + Activation

Send rent payment and activate the lease:

```bash
python client/scripts/demo_pay_rent.py
```

**Expected Output:**
```
============================================================
DEMO: Payment + Activation
============================================================

Step 1: Paying rent...
✓ Payment sent: 3.5 XLM
  Transaction hash: abc123...

Waiting for transaction confirmation...

Step 2: Activating lease...

Activating leaf lease 2...
✓ Lease activated
  Transaction: {...}

============================================================
Demo complete! Check your lock daemon for UNLOCK event.
============================================================
```

**Watch Terminal A:** You should see the lock transition to UNLOCKED state.

#### Terminal C: Utilities

Post and split utility costs:

```bash
# Post utility reading
python client/scripts/demo_post_reading.py

# Split costs among active leases
python client/scripts/demo_split_utilities.py
```

**Expected Output (Post Reading):**
```
============================================================
DEMO: Post Utility Reading
============================================================

✓ Utility reading posted:
   Unit: unit:NYC:123-A
   Period: 2025-10
   Electricity: 320 kWh
   Gas: 14 units
   Water: 6800 units
   Transaction: {...}

============================================================
Demo complete!
============================================================
```

**Expected Output (Split Utilities):**
```
============================================================
DEMO: Split Utilities
============================================================

Reading utility data for unit:NYC:123-A - 2025-10...
✓ Utility totals:
   Electricity: 320 kWh
   Gas: 14 units
   Water: 6800 units

Getting lease tree from root 1...
✓ Found 3 total active nodes

✓ Found 1 active leaf lease(s)

======================================================================
Utility Cost Split Results
======================================================================
Period: 2025-10
Unit: unit:NYC:123-A
Total usage: 320 kWh, 14 gas, 6800 water
Split among 1 active leaf lease(s)
======================================================================

Lease 1:
  ID: 2
  Lessee: GAABCD...
  Depth: 2
  Share:
    - Electricity: 320 kWh
    - Gas: 14 units
    - Water: 6800 units

======================================================================
Cost Summary (using demo rates):
======================================================================
  Electricity: 320 kWh × $0.120 = $38.40
  Gas: 14 units × $1.50 = $21.00
  Water: 6800 units × $0.008 = $54.40
  Total: $113.80
  Per Lease (1 active): $113.80
======================================================================
```

#### Terminal D: Delinquency

Mark lease as delinquent (triggers lock):

```bash
python client/scripts/demo_mark_delinquent.py
```

**Expected Output:**
```
============================================================
DEMO: Mark Lease as Delinquent
============================================================

Marking leaf lease 2 as delinquent...
✓ Lease marked delinquent
  Transaction: {...}

============================================================
Demo complete! Check your lock daemon for LOCK event.
============================================================
```

**Watch Terminal A:** You should see the lock transition back to LOCKED state.

## Demo Workflow

```
┌─────────────────────────────────────────────────────────┐
│ 1. Setup: Start lock daemon (Terminal A)               │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 2. Payment: Send rent + activate (Terminal B)           │
│    → Lock daemon sees "Activated" event                 │
│    → Lock state: LOCKED → UNLOCKED                     │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 3. Utilities: Post reading + split costs (Terminal C)   │
│    → Oracle stores utility totals                       │
│    → Costs split equally among active leaf leases        │
└─────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────┐
│ 4. Delinquency: Mark as delinquent (Terminal D)          │
│    → Lock daemon sees "Delinq" event                    │
│    → Lock state: UNLOCKED → LOCKED                      │
└─────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Lock daemon not receiving events
- Verify `LEASE_REGISTRY_ID` is set correctly
- Check that events are being published with correct topics
- Try starting from a fresh cursor (delete `.lock_cursor.txt`)

### Payment fails
- Ensure both tenant and landlord accounts are funded on testnet
- Check that `TENANT_SECRET` and `LANDLORD_SECRET` are correct

### Lease activation fails
- Verify lease is accepted before activating
- Check that `LESSOR_SECRET` has authorization to activate
- Ensure `LEAF_ID` is correct

### Utility reading fails
- Verify `UTILITIES_ORACLE_ID` is correct
- Check that oracle admin account is funded
- Ensure `UNIT` and `PERIOD` are valid symbols

### Cost splitting shows no active leases
- Verify `ROOT_ID` is correct
- Check that leases exist in the tree
- Ensure at least one lease has `active=True`

## Files

- `demo_pay_rent.py` - Payment and activation
- `demo_mark_delinquent.py` - Mark lease as delinquent
- `demo_post_reading.py` - Post utility reading to oracle
- `demo_split_utilities.py` - Split costs among active leases
- `lock/iot_lock_daemon.py` - Lock state daemon (watches events)

## Environment Variables

Edit `client/config.env` to configure:

```env
# Network
HORIZON_URL=https://horizon-testnet.stellar.org
SOROBAN_RPC=https://soroban-testnet.stellar.org
NETWORK_PASSPHRASE=Test SDF Network ; September 2015

# Accounts
LANDLORD_SECRET=SC...
TENANT_SECRET=SC...
ARBITRATOR_SECRET=SC...
LESSOR_SECRET=SC...

# Contracts
REGISTRY_ID=...
UTILITIES_ID=...

# Demo data
UNIT=unit:NYC:123-A
PERIOD=2025-10
LEAF_ID=2
ROOT_ID=1

# Lock daemon
LEASE_REGISTRY_ID=...
STELLAR_RPC=https://soroban-testnet.stellar.org
```

