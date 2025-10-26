# Quick Start: Terminal Demo

This document provides a simple guide to test the demo scripts.

## What Was Created

1. **demo_pay_rent.py** - Payment + activation
2. **demo_mark_delinquent.py** - Mark lease as delinquent  
3. **demo_post_reading.py** - Post utility readings
4. **demo_split_utilities.py** - Split utility costs
5. **lock/iot_lock_daemon.py** - Updated for "Activated" and "Delinq" events

## Configuration

Edit `client/config.env` and update:
- `ROOT_ID` - Your actual root lease ID
- `LEAF_ID` - Your actual leaf lease ID  
- `LESSOR_SECRET` - Secret of lessor who can activate/mark delinquent

## Running the Demo

### Step 1: Terminal A - Lock Daemon

```bash
cd lock
python iot_lock_daemon.py
```

### Step 2: Terminal B - Payment Flow

```bash
cd client/scripts
python demo_pay_rent.py
```

This will:
1. Send 3.5 XLM from tenant to landlord
2. Activate the lease (triggers UNLOCK event)
3. Terminal A should show: `lease_id=X: LOCKED -> UNLOCKED (Activated)`

### Step 3: Terminal C - Utilities

```bash
cd client/scripts

# Post reading
python demo_post_reading.py

# Split costs
python demo_split_utilities.py
```

### Step 4: Terminal D - Delinquency

```bash
cd client/scripts
python demo_mark_delinquent.py
```

This will mark the lease as delinquent.
Terminal A should show: `lease_id=X: UNLOCKED -> LOCKED (Delinq)`

## Notes

- Make sure you have valid lease IDs in `client/config.env`
- The lock daemon must be running to see events
- All contracts must be deployed on testnet
- Accounts must be funded on testnet

